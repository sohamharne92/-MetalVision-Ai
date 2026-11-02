"""
METALVISION AI — Page 12: Motor Control
Live telemetry from the 28BYJ-48 pot-control Arduino sketch.
Original sketch runs unchanged — Python only reads its output.
"""
import streamlit as st
import time
from modules.motor import MotorController, MotorError, get_or_connect, get_singleton

BG="#12100a";BG2="#1c1710";BORDER2="#2e1e0c"
CL="#e8a85a";CD="#8a5520";AMBER="#f5a623";TEXT="#f5ead8";TEXT2="#c8a878";TEXT3="#8a6840"
ACCEPT="#34d399";REJECT="#fb7185";WARN="#fbbf24"

def sec(label):
    st.markdown(f'<div class="v-section">{label}</div>', unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="v-hero">
  <span class="rivet tl">●</span><span class="rivet tr">●</span>
  <span class="rivet bl">●</span><span class="rivet br">●</span>
  <div class="v-hero-title">Motor Control</div>
  <div class="v-hero-sub">
    28BYJ-48 stepper · ULN2003 driver · Pot speed control · COM3 · 9600 baud
  </div>
  <div class="v-hero-meta">
    <span class="v-hero-pill">COM3 — CH340</span>
    <span class="v-hero-pill">28BYJ-48</span>
    <span class="v-hero-pill">ULN2003</span>
    <span class="v-hero-pill">9600 BAUD</span>
    <span class="v-hero-pill">POT CONTROL</span>
  </div>
</div>""", unsafe_allow_html=True)

# ── Motor singleton ───────────────────────────────────────────────────────────
motor = get_singleton()

sec("Connection")
col_stat, col_btn = st.columns([2, 1])

with col_btn:
    if st.button("🔌 Connect / Refresh", type="primary", use_container_width=True):
        with st.spinner("Connecting to COM3…"):
            try:
                motor = get_or_connect(force_reconnect=True)
                st.session_state["motor_ctrl"] = motor
                st.rerun()
            except MotorError as e:
                st.error(f"❌ {e}")

    if motor and motor.connected:
        if st.button("Disconnect", use_container_width=True):
            motor.disconnect()
            st.session_state["motor_ctrl"] = None
            st.rerun()

with col_stat:
    if motor and motor.connected:
        t = motor.telemetry
        spr = motor.seconds_per_revolution()
        st.markdown(f"""
        <div style="background:{BG2};border:1px solid {ACCEPT};
                    border-left:4px solid {ACCEPT};border-radius:6px;
                    padding:14px 18px;font-family:'JetBrains Mono',monospace;
                    font-size:0.85rem;line-height:2.1;">
          <div><span style="color:{CD};">Port      </span>
               <span style="color:{TEXT};">&nbsp;{motor.port_used}</span></div>
          <div><span style="color:{CD};">Baud      </span>
               <span style="color:{TEXT};">&nbsp;9600</span></div>
          <div><span style="color:{CD};">Motor     </span>
               <span style="color:{ACCEPT};">&nbsp;28BYJ-48 — RUNNING ✓</span></div>
          <div><span style="color:{CD};">Speed     </span>
               <span style="color:{AMBER};">&nbsp;{t['rpm']:.1f} RPM</span></div>
          <div><span style="color:{CD};">Pot Value </span>
               <span style="color:{AMBER};">&nbsp;{t['pot']} / 1023</span></div>
          <div><span style="color:{CD};">Est. Angle</span>
               <span style="color:{CL};">&nbsp;{t['angle']:.1f}°</span></div>
          <div><span style="color:{CD};">Rev Time  </span>
               <span style="color:{TEXT2};">&nbsp;{f"{spr:.1f} s/rev" if spr > 0 else "stopped"}</span></div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:{BG2};border:1px solid {REJECT};
                    border-left:4px solid {REJECT};border-radius:6px;
                    padding:14px 18px;font-family:'JetBrains Mono',monospace;
                    font-size:0.85rem;color:{REJECT};">
          Not connected — click 🔌 Connect / Refresh above.
        </div>""", unsafe_allow_html=True)

# ── Live telemetry dashboard ──────────────────────────────────────────────────
if motor and motor.connected:
    sec("Live Telemetry")

    auto_refresh = st.toggle("Auto-refresh (1 s)", value=True, key="motor_refresh")

    t   = motor.telemetry
    spr = motor.seconds_per_revolution()
    m1, m2, m3, m4 = st.columns(4)

    def metric_card(col, label, value, color=AMBER):
        col.markdown(f"""
        <div style="background:{BG2};border:1px solid {BORDER2};border-radius:8px;
                    padding:16px 12px;text-align:center;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:1.5rem;
                      font-weight:700;color:{color};line-height:1.1;">{value}</div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:0.7rem;
                      font-weight:700;letter-spacing:0.14em;text-transform:uppercase;
                      color:{TEXT3};margin-top:5px;">{label}</div>
        </div>""", unsafe_allow_html=True)

    metric_card(m1, "Motor Speed",  f"{t['rpm']:.1f} RPM",    AMBER)
    metric_card(m2, "Pot Value",    f"{t['pot']} / 1023",     CL)
    metric_card(m3, "Est. Angle",   f"{t['angle']:.1f}°",     ACCEPT)
    metric_card(m4, "Rev Time",     f"{spr:.1f} s" if spr > 0 else "—", TEXT2)

    # Angle gauge bar
    angle_pct = t["angle"] / 360.0
    st.markdown(f"""
    <div style="background:{BG2};border:1px solid {BORDER2};border-radius:8px;
                padding:16px 20px;margin-top:12px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;
                  color:{CD};margin-bottom:8px;letter-spacing:0.1em;">
        ROTATION POSITION — {t['angle']:.1f}° / 360°
      </div>
      <div style="background:{BORDER2};border-radius:4px;height:12px;overflow:hidden;">
        <div style="width:{angle_pct*100:.1f}%;height:100%;
                    background:linear-gradient(90deg,{CD},{AMBER});
                    border-radius:4px;"></div>
      </div>
      <div style="display:flex;justify-content:space-between;
                  font-family:'JetBrains Mono',monospace;font-size:0.7rem;
                  color:{TEXT3};margin-top:4px;">
        <span>0°</span><span>90°</span><span>180°</span><span>270°</span><span>360°</span>
      </div>
    </div>""", unsafe_allow_html=True)

    # 12-position capture timing info
    st.markdown("<br>", unsafe_allow_html=True)
    sec("Inspection Timing Estimate")
    if spr > 0:
        time_per_30deg = spr * (30.0 / 360.0)
        total_time     = time_per_30deg * 12
        st.markdown(f"""
        <div style="background:{BG2};border:1px solid {BORDER2};border-radius:8px;
                    padding:14px 18px;font-family:'JetBrains Mono',monospace;
                    font-size:0.82rem;color:{TEXT2};line-height:2;">
          <div>Current speed  : <span style="color:{AMBER};">{t['rpm']:.1f} RPM</span></div>
          <div>Time per 30°   : <span style="color:{AMBER};">{time_per_30deg:.2f} s</span></div>
          <div>12-position scan: <span style="color:{ACCEPT};">{total_time:.1f} s total</span></div>
          <div style="color:{TEXT3};font-size:0.72rem;margin-top:4px;">
            Adjust pot to control speed. Higher RPM = faster scan but may blur images.
            Recommended: 5–8 RPM for clear captures.
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.warning("Motor appears stopped. Check pot position and power supply.")

    if auto_refresh:
        time.sleep(1.0)
        st.rerun()

# ── COM port diagnostics ──────────────────────────────────────────────────────
sec("COM Port Diagnostics")
ports = MotorController.list_ports()
if ports:
    for p in ports:
        c = ACCEPT if p["is_ch340"] else TEXT3
        st.markdown(
            f'<div style="padding:8px 14px;background:{BG2};border:1px solid '
            f'{"#34d39944" if p["is_ch340"] else BORDER2};border-radius:6px;'
            f'margin-bottom:6px;font-family:JetBrains Mono,monospace;'
            f'font-size:0.82rem;color:{TEXT2};display:flex;gap:16px;align-items:center;">'
            f'<span style="color:{c};font-weight:700;min-width:48px;">{p["device"]}</span>'
            f'<span style="flex:1;">{p["description"]}</span>'
            f'<span style="color:{TEXT3};">VID:{p["vid"]} PID:{p["pid"]}'
            f'{"  ← CH340 MOTOR" if p["is_ch340"] else ""}</span></div>',
            unsafe_allow_html=True,
        )
else:
    st.warning("No COM ports found. Check USB cable.")
