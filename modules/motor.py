"""
METALVISION AI — Motor Driver  (modules/motor.py)
===================================================
Works with the original 28BYJ-48 pot-control Arduino sketch (unchanged).

The sketch continuously prints:
    Pot Value: <0-1023> | Motor Speed: <1-15> RPM

This driver:
  1. Opens COM3 at 9600 baud WITHOUT resetting the Arduino (DTR=False).
  2. Runs a background thread that parses every telemetry line.
  3. Tracks estimated rotation angle from RPM + elapsed time.
  4. Exposes wait_for_angle() so the inspection page can wait until
     the motor has rotated to each 30° capture position.

No commands are ever sent to the Arduino — the original sketch is kept
exactly as uploaded.

Hardware:
    28BYJ-48 stepper  (2048 steps/rev via ULN2003 driver)
    Pins: IN1=8, IN3=10, IN2=9, IN4=11
    Potentiometer on A0  →  speed 1–15 RPM
"""

from __future__ import annotations

import re
import threading
import time
from typing import Optional, Callable

try:
    import serial
    import serial.tools.list_ports
    _SERIAL_OK = True
except ImportError:
    _SERIAL_OK = False

# ── Constants ──────────────────────────────────────────────────────────────────
CH340_VID   = 0x1A86
CH340_PID   = 0x7523
BAUD        = 9600
ANGLE_TOL   = 8.0      # degrees — "close enough" to the target angle
SETTLE_S    = 0.3      # wait after reaching target before capture

# Parse: "Pot Value: 359 | Motor Speed: 5 RPM"
_LINE_RE = re.compile(
    r"Pot\s+Value:\s*(\d+)\s*\|\s*Motor\s+Speed:\s*([\d.]+)\s*RPM",
    re.IGNORECASE,
)


class MotorError(Exception):
    pass


class MotorController:
    """
    Read-only interface to the 28BYJ-48 pot-control sketch.

    connect()           — open port, start background reader
    wait_for_angle(deg) — block until motor reaches that angle
    telemetry           — {'pot', 'rpm', 'angle'}
    disconnect()        — close port
    """

    def __init__(self, port: Optional[str] = None, simulate: bool = False):
        self._port      = port
        self._simulate  = simulate
        self._ser: Optional["serial.Serial"] = None
        self._lock      = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running   = False

        # Live state updated by reader thread
        self._pot       = 0
        self._rpm       = 0.0
        self._angle     = 0.0      # estimated, continuously wrapping 0–360
        self._last_ts   = time.time()

        self.connected  = False
        self.port_used  = None
        self.firmware   = "pot_control_sketch"

    # ── Connection ─────────────────────────────────────────────────────────────

    @staticmethod
    def find_port() -> Optional[str]:
        if not _SERIAL_OK:
            return None
        for p in serial.tools.list_ports.comports():
            if p.vid == CH340_VID and p.pid == CH340_PID:
                return p.device
            if "CH340" in (p.description or "").upper():
                return p.device
        return None

    @staticmethod
    def list_ports() -> list[dict]:
        if not _SERIAL_OK:
            return []
        return [{
            "device":      p.device,
            "description": p.description or "",
            "vid":         f"{p.vid:04X}" if p.vid else "????",
            "pid":         f"{p.pid:04X}" if p.pid else "????",
            "is_ch340":    (p.vid == CH340_VID and p.pid == CH340_PID),
        } for p in serial.tools.list_ports.comports()]

    def connect(self) -> dict:
        """Open port WITHOUT resetting the Arduino, start background reader."""
        if self._simulate:
            self.connected = True
            self.port_used = "SIMULATE"
            self._rpm = 5.0; self._pot = 512
            self._running = True
            self._thread = threading.Thread(target=self._sim_loop, daemon=True)
            self._thread.start()
            return self._status("Simulation mode — 28BYJ-48 @ 5 RPM simulated.")

        if not _SERIAL_OK:
            raise MotorError("pyserial not installed. Run: pip install pyserial")

        port = self._port or self.find_port()
        if not port:
            raise MotorError(
                "No CH340 found on any COM port. "
                "Check USB cable and Windows Device Manager."
            )

        try:
            # DTR=False → Arduino does NOT reset → motor keeps spinning
            ser = serial.Serial()
            ser.port          = port
            ser.baudrate      = BAUD
            ser.timeout       = 2.0
            ser.write_timeout = 2.0
            ser.dsrdtr        = False
            ser.rtscts        = False
            ser.dtr           = False   # set BEFORE open() — critical
            ser.rts           = False
            ser.open()
            time.sleep(0.3)
            ser.reset_input_buffer()

            self._ser       = ser
            self._port      = port
            self.port_used  = port
            self.connected  = True
            self._last_ts   = time.time()

            # Start background telemetry reader
            self._running = True
            self._thread  = threading.Thread(
                target=self._reader_loop, daemon=True)
            self._thread.start()

            # Wait up to 3 s for first telemetry line
            t0 = time.time()
            while time.time() - t0 < 3.0 and self._rpm == 0.0:
                time.sleep(0.05)

            msg = (f"Connected to {port} @ {BAUD} baud. "
                   f"Motor spinning at {self._rpm:.1f} RPM "
                   f"(Pot: {self._pot}/1023). Arduino NOT reset.")
            return self._status(msg)

        except serial.SerialException as e:
            raise MotorError(f"Cannot open {port}: {e}") from e

    def disconnect(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser      = None
        self.connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def angle(self) -> float:
        """Estimated current rotation angle (0–360°, continuously updated)."""
        return round(self._angle % 360.0, 1)

    @property
    def rpm(self) -> float:
        return round(self._rpm, 2)

    @property
    def pot(self) -> int:
        return self._pot

    @property
    def is_ready(self) -> bool:
        return self.connected

    @property
    def telemetry(self) -> dict:
        return {
            "pot":   self._pot,
            "rpm":   round(self._rpm, 2),
            "angle": round(self._angle % 360.0, 1),
        }

    def seconds_per_revolution(self) -> float:
        """Time for one full revolution at current RPM (0 if stopped)."""
        return 60.0 / self._rpm if self._rpm > 0 else 0.0

    def wait_for_angle(
        self,
        target_deg: float,
        timeout_s: float = 60.0,
        on_tick: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """
        Block until the motor's estimated angle is within ANGLE_TOL of target.

        Parameters
        ----------
        target_deg : angle to wait for (0–359°).
        timeout_s  : give up after this many seconds (default 60).
        on_tick    : optional callback(current_angle) called ~10 Hz.

        Returns True when reached, False on timeout.
        """
        if self._simulate:
            # Simulate rotation at 5 RPM = 30°/s
            deg_per_sec = (self._rpm / 60.0) * 360.0
            cur = self._angle % 360.0
            diff = (target_deg - cur) % 360.0
            time.sleep(diff / max(deg_per_sec, 1.0))
            with self._lock:
                self._angle = float(target_deg)
            return True

        target = float(target_deg) % 360.0
        t0 = time.time()

        while time.time() - t0 < timeout_s:
            cur  = self._angle % 360.0
            diff = abs(cur - target)
            if diff > 180.0:
                diff = 360.0 - diff
            if diff <= ANGLE_TOL:
                time.sleep(SETTLE_S)
                return True
            if on_tick:
                on_tick(cur)
            time.sleep(0.1)

        return False   # timed out

    def status(self) -> dict:
        return self._status()

    # ── Background threads ─────────────────────────────────────────────────────

    def _reader_loop(self):
        """Parse telemetry from the Arduino sketch, update angle estimate."""
        while self._running:
            try:
                raw  = self._ser.readline()
                line = raw.decode("ascii", errors="ignore").strip()
                m    = _LINE_RE.search(line)
                if m:
                    pot = int(m.group(1))
                    rpm = float(m.group(2))
                    now = time.time()
                    with self._lock:
                        dt           = now - self._last_ts
                        # degrees elapsed since last reading
                        degs         = (rpm / 60.0) * 360.0 * dt
                        self._pot    = pot
                        self._rpm    = rpm
                        self._angle  = (self._angle + degs) % 360.0
                        self._last_ts = now
            except Exception:
                if self._running:
                    time.sleep(0.1)

    def _sim_loop(self):
        """Simulate 5 RPM rotation for demo/testing without hardware."""
        while self._running:
            time.sleep(0.1)
            with self._lock:
                self._angle = (self._angle + 3.0) % 360.0  # 5 RPM ≈ 30°/s


    def _status(self, message: str = "") -> dict:
        return {
            "connected": self.connected,
            "port":      self.port_used,
            "baud":      BAUD,
            "firmware":  self.firmware,
            "rpm":       round(self._rpm, 2),
            "pot":       self._pot,
            "angle":     round(self._angle % 360.0, 1),
            "is_ready":  self.is_ready,
            "simulate":  self._simulate,
            "message":   message,
        }


# ── Aliases ────────────────────────────────────────────────────────────────────
MotorMonitor = MotorController


# ── Module-level singleton (survives Streamlit reruns) ─────────────────────────
_singleton: Optional[MotorController] = None


def get_or_connect(force_reconnect: bool = False) -> MotorController:
    """
    Return the module-level singleton, connecting if needed.
    Use force_reconnect=True to close and reopen the port.
    This is the correct way to use the motor from Streamlit pages —
    the singleton lives in module memory, NOT in session_state, so
    the open serial port survives every Streamlit rerun.
    """
    global _singleton
    if force_reconnect and _singleton is not None:
        try:
            _singleton.disconnect()
        except Exception:
            pass
        _singleton = None

    if _singleton is not None and _singleton.connected:
        try:
            if _singleton._simulate or (_singleton._ser and _singleton._ser.is_open):
                return _singleton
        except Exception:
            pass
        _singleton = None

    mc = MotorController()
    mc.connect()
    _singleton = mc
    return _singleton


def get_singleton() -> Optional[MotorController]:
    """Return existing singleton without connecting. None if not connected."""
    global _singleton
    if _singleton is not None and _singleton.connected:
        try:
            if _singleton._simulate or (_singleton._ser and _singleton._ser.is_open):
                return _singleton
        except Exception:
            pass
    return None
