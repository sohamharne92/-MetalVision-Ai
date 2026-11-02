"""
Tests for modules/simulator.py — MetalPartSimulator.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import INSPECTION_POSITIONS, DEMO_SCENARIOS
from modules.simulator import MetalPartSimulator


class TestSimulatorInit:
    def test_creates_unique_id(self):
        s1 = MetalPartSimulator()
        s2 = MetalPartSimulator()
        assert s1.inspection_id != s2.inspection_id

    def test_initial_state_empty(self):
        sim = MetalPartSimulator()
        assert sim.inspection_results == {}
        assert sim.final_decision is None
        assert sim.defect_count == 0


class TestRunInspection:
    def test_returns_dict(self):
        sim    = MetalPartSimulator()
        result = sim.run_inspection("Scenario 1: Normal Component")
        assert isinstance(result, dict)

    def test_all_positions_present(self):
        sim    = MetalPartSimulator()
        result = sim.run_inspection("Scenario 1: Normal Component")
        for pos in INSPECTION_POSITIONS:
            assert pos in result["positions"]

    def test_scenario1_all_normal(self):
        sim    = MetalPartSimulator()
        result = sim.run_inspection("Scenario 1: Normal Component")
        assert result["final_decision"] == "ACCEPT"
        assert result["defect_count"]   == 0
        for pos in result["positions"].values():
            assert pos["class"] == "Normal"

    def test_scenario2_has_scratch_at_90(self):
        sim    = MetalPartSimulator()
        result = sim.run_inspection("Scenario 2: Scratch at 90°")
        assert result["final_decision"] == "REJECT"
        assert result["positions"][90]["class"] == "Scratch"

    def test_scenario3_has_crack_at_180(self):
        sim    = MetalPartSimulator()
        result = sim.run_inspection("Scenario 3: Crack at 180°")
        assert result["final_decision"] == "REJECT"
        assert result["positions"][180]["class"] == "Crack"

    def test_scenario4_has_three_defects(self):
        sim    = MetalPartSimulator()
        result = sim.run_inspection("Scenario 4: Multiple Defects")
        assert result["final_decision"] == "REJECT"
        assert result["defect_count"]   == 3
        assert result["positions"][60]["class"]  == "Dent"
        assert result["positions"][210]["class"] == "Scratch"
        assert result["positions"][330]["class"] == "Crack"

    def test_confidence_between_0_and_1(self):
        sim    = MetalPartSimulator()
        result = sim.run_inspection("Scenario 5: Random Test")
        for pos in result["positions"].values():
            assert 0.0 <= pos["confidence"] <= 1.0

    def test_overall_confidence_in_range(self):
        sim    = MetalPartSimulator()
        result = sim.run_inspection("Scenario 1: Normal Component")
        assert 0.0 <= result["overall_confidence"] <= 1.0

    def test_unknown_scenario_uses_random(self):
        sim    = MetalPartSimulator()
        result = sim.run_inspection("Scenario 99: Does Not Exist")
        assert "final_decision" in result
        assert result["final_decision"] in ("ACCEPT", "REJECT")


class TestInspectOne:
    def test_inspect_one_returns_position_dict(self):
        sim = MetalPartSimulator()
        result = sim.inspect_one(90, "Scenario 1: Normal Component")
        assert isinstance(result, dict)
        assert result["class"] == "Normal"
        assert result["angle"] == 90

    def test_finalise_after_all_positions(self):
        sim = MetalPartSimulator()
        for angle in INSPECTION_POSITIONS:
            sim.inspect_one(angle, "Scenario 1: Normal Component")
        summary = sim.finalise()
        assert summary["final_decision"] == "ACCEPT"
        assert len(summary["positions"])  == 12

    def test_finalise_with_defect(self):
        sim = MetalPartSimulator()
        for angle in INSPECTION_POSITIONS:
            sim.inspect_one(angle, "Scenario 2: Scratch at 90°")
        summary = sim.finalise()
        assert summary["final_decision"] == "REJECT"


class TestReset:
    def test_reset_clears_results(self):
        sim = MetalPartSimulator()
        sim.run_inspection("Scenario 1: Normal Component")
        old_id = sim.inspection_id
        sim.reset()
        assert sim.inspection_results == {}
        assert sim.final_decision is None
        assert sim.inspection_id != old_id


class TestGetDefectSummary:
    def test_all_normal_summary(self):
        sim = MetalPartSimulator()
        sim.run_inspection("Scenario 1: Normal Component")
        summary = sim.get_defect_summary()
        assert summary["Normal"]  == 12
        assert summary["Crack"]   == 0
        assert summary["Dent"]    == 0
        assert summary["Scratch"] == 0

    def test_one_crack_summary(self):
        sim = MetalPartSimulator()
        sim.run_inspection("Scenario 3: Crack at 180°")
        summary = sim.get_defect_summary()
        assert summary["Crack"] == 1
        assert summary["Normal"] == 11
