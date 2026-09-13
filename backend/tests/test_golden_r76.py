"""Golden calculation test based on authoritative OIML R 76-1:2006 (E) clause A.4.4.3 example."""

from decimal import Decimal
from app.engines.calculation import CalculationEngine
from app.engines.compliance import ComplianceEngine
from app.models.configuration import AccuracyClass
from app.models.metrology import ComplianceDecision


def test_oiml_r76_clause_a443_golden_example():
    """Exact golden test derived from OIML R 76-1: 2006 (E), clause A.4.4.3 (page 89).
    
    Standard Example Text:
    "An instrument with a verification scale interval, e, of 5 g is loaded with 1 kg
     and thereby indicates 1 000 g. After adding successive weights of 0.5 g, the indication
     changes from 1 000 g to 1 005 g at an additional load of 1.5 g. Inserted in the above formula
     these observations give:
         P = (1 000 + 2.5 - 1.5) g = 1 001 g
     Thus the true indication prior to rounding is 1 001 g, and the error is:
         E = (1 001 - 1 000) g = + 1 g
     If the changeover point at zero as calculated above was E0 = + 0.5 g, the corrected error is:
         Ec = + 1 - (+ 0.5) = + 0.5 g"
    """
    inputs = {
        "load": Decimal("1000"),                     # L = 1 000 g (1 kg)
        "indication": Decimal("1000"),               # I = 1 000 g
        "verification_scale_interval": Decimal("5"), # e = 5 g
        "additional_load": Decimal("1.5"),           # ΔL = 1.5 g
        "zero_error": Decimal("0.5"),                # E0 = + 0.5 g
        "unit": "g",
        "accuracy_class": "CLASS_III",
    }

    result = CalculationEngine.calculate("R76_A4_4_3_ERROR", inputs)
    out = result.output

    # 1. Verify Indication prior to rounding: P = I + 0.5e - ΔL = 1000 + 2.5 - 1.5 = 1001 g
    assert Decimal(out["P"]) == Decimal("1001")

    # 2. Verify Error prior to rounding: E = P - L = 1001 - 1000 = +1 g
    assert Decimal(out["E"]) == Decimal("1")

    # 3. Verify Zero error E0 = +0.5 g
    assert Decimal(out["E0"]) == Decimal("0.5")

    # 4. Verify Corrected error prior to rounding: Ec = E - E0 = 1 - 0.5 = +0.5 g
    assert Decimal(out["Ec"]) == Decimal("0.5")

    # 5. Verify MPE determination for Class III at load 1000 g:
    # m = L / e = 1000 / 5 = 200 intervals.
    # From Table 6 for Class III: 0 <= m <= 500 intervals -> mpe = +/- 0.5 e = +/- 2.5 g
    assert Decimal(out["mpe_factor"]) == Decimal("0.5")
    assert Decimal(out["mpe_mass"]) == Decimal("2.5")

    # 6. Verify Compliance Decision
    comp = ComplianceEngine.evaluate(result.calculation_code, out)
    assert comp.decision == ComplianceDecision.PASS
    assert comp.criterion_value == "<= 2.500000 g"
    assert comp.measured_value == "0.500000 g"
    assert comp.margin == "+2.000000 g"
    assert "within maximum permissible error" in comp.reasoning_json["explanation"]
