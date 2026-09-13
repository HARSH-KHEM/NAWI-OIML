"""Tests for CalculationEngine and ComplianceEngine.

Verifies:
- Weighing performance Decimal calculation (A.4.4.3)
- Eccentricity test calculation (A.4.7)
- Repeatability test calculation (A.4.10)
- Compliance decisions: PASS, FAIL, INCOMPLETE
- Deterministic structured reasoning
- Precision: Strict Decimal, no binary float arithmetic
"""

from decimal import Decimal
import pytest
from app.engines.calculation import CalculationEngine
from app.engines.compliance import ComplianceEngine
from app.models.metrology import ComplianceDecision


def test_weighing_calculation_pass():
    """Authoritative A.4.4.3 calculation where corrected error Ec is well within MPE."""
    # Class III NAWI: Max 30 kg, e = 0.01 kg
    # Load = 10.00 kg (1000 e -> Band 2: MPE = 1.0 e = 0.010 kg)
    # L = 10.00, I = 10.00, e = 0.01, dL = 0.005, E0 = 0.000
    # P = 10.00 + 0.005 - 0.005 = 10.000
    # E = 10.000 - 10.000 = 0.000
    # Ec = 0.000
    inputs = {
        "load": "10.00",
        "indication": "10.00",
        "verification_scale_interval": "0.01",
        "additional_load": "0.005",
        "zero_error": "0.000",
        "unit": "kg",
        "accuracy_class": "CLASS_III",
    }
    calc_res = CalculationEngine.calculate("R76_A4_4_3_ERROR", inputs)
    out = calc_res.output

    assert out["P"] == "10.000"
    assert out["E"] == "0.000"
    assert out["Ec"] == "0.000"
    assert out["mpe_mass"] == "0.010"
    assert out["mpe_factor"] == "1.0"

    # Evaluate compliance
    comp = ComplianceEngine.evaluate(calc_res.calculation_code, out)
    assert comp.decision == ComplianceDecision.PASS
    assert "<= 0.010" in comp.criterion_value
    assert "0.000" in comp.measured_value
    assert "+0.010" in comp.margin
    assert "within" in comp.reasoning_json["explanation"].lower()


def test_weighing_calculation_fail():
    """Authoritative A.4.4.3 calculation where corrected error Ec exceeds MPE."""
    # Class III NAWI: e = 0.01 kg.
    # Load = 10.00 kg -> MPE = 0.010 kg
    # Suppose indication I = 10.02, dL = 0.005, E0 = 0.000
    # P = 10.02 + 0.005 - 0.005 = 10.020
    # E = 10.020 - 10.000 = +0.020 kg
    # Ec = +0.020 kg > MPE (0.010 kg) -> FAIL
    inputs = {
        "load": "10.00",
        "indication": "10.02",
        "verification_scale_interval": "0.01",
        "additional_load": "0.005",
        "zero_error": "0.000",
        "unit": "kg",
        "accuracy_class": "CLASS_III",
    }
    calc_res = CalculationEngine.calculate("R76_A4_4_3_ERROR", inputs)
    out = calc_res.output

    assert out["Ec"] == "0.020"
    assert out["mpe_mass"] == "0.010"

    comp = ComplianceEngine.evaluate(calc_res.calculation_code, out)
    assert comp.decision == ComplianceDecision.FAIL
    assert "-0.010" in comp.margin
    assert comp.reasoning_json["rule_reference"] == "OIML R 76-1:2006, A.4.4.3 & 3.5.1 Table 6"
    assert "exceeds" in comp.reasoning_json["explanation"].lower()


def test_eccentricity_calculation():
    """Eccentricity under A.4.7 across 5 positions."""
    # Test load = 10 kg (1/3 Max of 30 kg), e = 0.01 kg -> MPE = 0.010 kg
    inputs = {
        "verification_scale_interval": "0.01",
        "unit": "kg",
        "accuracy_class": "CLASS_III",
        "zero_error": "0.000",
        "positions": [
            {"position": "CENTER", "load": "10.00", "indication": "10.00", "additional_load": "0.005", "zero_error": "0.000"},
            {"position": "FRONT", "load": "10.00", "indication": "10.005", "additional_load": "0.005", "zero_error": "0.000"},
            {"position": "BACK", "load": "10.00", "indication": "9.995", "additional_load": "0.005", "zero_error": "0.000"},
            {"position": "LEFT", "load": "10.00", "indication": "10.00", "additional_load": "0.005", "zero_error": "0.000"},
            {"position": "RIGHT", "load": "10.00", "indication": "10.00", "additional_load": "0.005", "zero_error": "0.000"},
        ],
    }
    calc_res = CalculationEngine.calculate("R76_ECCENTRICITY", inputs)
    out = calc_res.output
    assert len(out["position_results"]) == 5
    assert out["max_absolute_error"] == "0.005"
    assert out["mpe_mass"] == "0.010"

    comp = ComplianceEngine.evaluate(calc_res.calculation_code, out)
    assert comp.decision == ComplianceDecision.PASS
    assert "+0.005" in comp.margin


def test_repeatability_calculation():
    """Repeatability under A.4.10: difference between max and min error shall not exceed |MPE|."""
    # Load = 15 kg (50% Max), e = 0.01 kg -> 1500 e -> MPE = 1.0 e = 0.010 kg
    weighings = [
        {"weighing_number": i, "load": "15.00", "indication": "15.00" if i % 2 == 0 else "15.005", "additional_load": "0.005"}
        for i in range(1, 11)
    ]
    inputs = {
        "target_load": "15.00",
        "verification_scale_interval": "0.01",
        "unit": "kg",
        "accuracy_class": "CLASS_III",
        "zero_error": "0.000",
        "weighings": weighings,
    }
    calc_res = CalculationEngine.calculate("R76_REPEATABILITY", inputs)
    out = calc_res.output
    assert out["weighings_count"] == 10
    assert out["repeatability_error"] == "0.005"
    assert out["mpe_mass"] == "0.010"

    comp = ComplianceEngine.evaluate(calc_res.calculation_code, out)
    assert comp.decision == ComplianceDecision.PASS
    assert "+0.005" in comp.margin


def test_repeatability_failing_spread():
    """Repeatability failing when difference between readings exceeds MPE."""
    # If one reading is 15.00 and another is 15.015, spread = 0.015 kg > MPE (0.010 kg)
    weighings = [
        {"weighing_number": 1, "load": "15.00", "indication": "15.00", "additional_load": "0.005"},
        {"weighing_number": 2, "load": "15.00", "indication": "15.015", "additional_load": "0.005"},
        {"weighing_number": 3, "load": "15.00", "indication": "15.00", "additional_load": "0.005"},
    ]
    inputs = {
        "target_load": "15.00",
        "verification_scale_interval": "0.01",
        "unit": "kg",
        "accuracy_class": "CLASS_III",
        "zero_error": "0.000",
        "weighings": weighings,
    }
    calc_res = CalculationEngine.calculate("R76_REPEATABILITY", inputs)
    out = calc_res.output
    comp = ComplianceEngine.evaluate(calc_res.calculation_code, out)
    assert comp.decision == ComplianceDecision.FAIL
    assert "-0.005" in comp.margin


def test_compliance_incomplete():
    """Unimplemented or incomplete procedure code produces INCOMPLETE decision."""
    incomp = ComplianceEngine.evaluate("R76_UNREGISTERED_TEST", {})
    assert incomp.decision == ComplianceDecision.INCOMPLETE
