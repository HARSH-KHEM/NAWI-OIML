"""Comprehensive Regression Test Suite for Phase 2.1 Metrological Correctness Patch.

Verifies all 19 mandatory P0 / P1 scenarios under OIML R 76-1:2006:
1. Valid weighing-performance calculation -> PASS
2. Weighing-performance missing zero error -> INCOMPLETE
3. Weighing-performance missing indication -> INCOMPLETE
4. Invalid load -> rejected
5. Valid eccentricity -> PASS
6. Missing eccentricity position -> INCOMPLETE
7. Valid repeatability -> PASS
8. Repeatability with insufficient weighings -> INCOMPLETE
9. Repeatability duplicate index -> rejected
10. Repeatability malformed JSON -> rejected
11. MPE lower/upper boundary tests
12. Out-of-range MPE configuration -> invalid/unsupported
13. Multiple-range uses correct range Max/e
14. RuleVersion is actually used by calculation/compliance dispatch
15. Observation modification after calculation -> rejected
16. Retest preserves Attempt 1 and creates Attempt 2
17. Trace contains complete evidence chain
18. Transaction rollback on failure
19. Configuration validation fail-closed behavior
"""

from decimal import Decimal
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.applicability import (
    ApplicabilityEngine,
    ConfigurationValidationError,
    validate_configuration_snapshot,
)
from app.engines.calculation import CalculationEngine
from app.engines.compliance import ComplianceEngine
from app.engines.mpe import MPEEngine
from app.models.configuration import AccuracyClass, InstrumentConfiguration, TareType
from app.models.range import InstrumentConfigurationRange
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.instrument import Instrument
from app.models.metrology import Calculation, ComplianceDecision, ComplianceResult
from app.models.rule import Rule, RuleVersion
from app.models.test_execution import (
    EvaluationTest,
    EvaluationTestStatus,
    Observation,
    TestAttempt,
    TestAttemptStatus,
)
from app.models.user import User, UserRole
from app.services.calculation_service import execute_attempt_calculation
from app.services.plan_service import generate_evaluation_plan
from app.services.test_service import (
    ObservationLockedError,
    create_retest_attempt,
    record_observation,
    update_observation,
)
from app.services.trace_service import get_test_attempt_trace


# ==============================================================================
# FIXTURES & HELPERS
# ==============================================================================

@pytest.fixture
def test_env(db_session: Session):
    """Set up complete valid instrument, configuration, rule, and evaluation fixture."""
    user = User(email=f"tester-{uuid.uuid4().hex[:6]}@lab.org", full_name="Metrologist", role=UserRole.OPERATOR)
    db_session.add(user)
    db_session.flush()

    inst = Instrument(
        serial_number=f"SN-{uuid.uuid4().hex[:8].upper()}",
        manufacturer="Mettler-Test",
        model_name="XP-3000",
        is_synthetic=True,
    )
    db_session.add(inst)
    db_session.flush()

    config = InstrumentConfiguration(
        instrument_id=inst.id,
        accuracy_class=AccuracyClass.CLASS_III,
        max_capacity=Decimal("30.000"),
        min_capacity=Decimal("0.200"),
        verification_scale_interval=Decimal("0.010"),
        actual_scale_interval=Decimal("0.010"),
        unit="kg",
        number_of_ranges=1,
        is_multiple_range=False,
        tare_type=TareType.SUBTRACTIVE,
        is_electronic=True,
        has_zero_setting=True,
        extra_capabilities={
            "load_receptor": {
                "support_count": 4,
                "special_receptor": False,
                "rolling_load": False,
            }
        },
    )
    db_session.add(config)
    db_session.flush()

    rule = db_session.scalar(select(Rule).where(Rule.code == "OIML-R76-2006"))
    if not rule:
        rule = Rule(code="OIML-R76-2006", name="OIML R 76-1:2006", description="NAWI standard")
        db_session.add(rule)
        db_session.flush()

    rv = RuleVersion(
        rule_id=rule.id,
        version_number=f"2006-test-{uuid.uuid4().hex[:4]}",
        standard_version="OIML R 76-1: 2006 (E)",
        clause="A.4",
        calculation_identifier="R76_A4_4_3_ERROR",
        applicability_identifier="R76_APPLICABILITY_V1",
        aggregation_strategy="ALL_POINTS_PASS",
        definition_json={
            "tests": {
                "WEIGHING_PERFORMANCE": {
                    "clause": "A.4.4.3",
                    "calculation_identifier": "R76_A4_4_3_ERROR",
                    "criterion": {"type": "ABS_LE_MPE"},
                },
                "ECCENTRICITY": {
                    "clause": "A.4.7",
                    "calculation_identifier": "R76_ECCENTRICITY",
                    "criterion": {"type": "MAX_POS_ABS_LE_MPE"},
                },
                "REPEATABILITY": {
                    "clause": "A.4.10",
                    "calculation_identifier": "R76_REPEATABILITY",
                    "criterion": {"type": "SPAN_LE_MPE"},
                },
            }
        },
        content_hash="d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592",
        is_active=True,
    )
    db_session.add(rv)
    db_session.flush()

    snapshot = {
        "accuracy_class": "CLASS_III",
        "max_capacity": "30.000",
        "min_capacity": "0.200",
        "verification_scale_interval": "0.010",
        "actual_scale_interval": "0.010",
        "unit": "kg",
        "number_of_ranges": 1,
        "is_multiple_range": False,
        "is_electronic": True,
        "has_zero_setting": True,
        "tare_type": "SUBTRACTIVE",
        "ranges": [],
        "extra_capabilities": {
            "load_receptor": {
                "support_count": 4,
                "special_receptor": False,
                "rolling_load": False,
            }
        },
    }

    eval_obj = Evaluation(
        evaluation_number=f"EVAL-{uuid.uuid4().hex[:8].upper()}",
        instrument_id=inst.id,
        instrument_configuration_id=config.id,
        rule_version_id=rv.id,
        operator_id=user.id,
        status=EvaluationStatus.IN_PROGRESS,
        configuration_snapshot=snapshot,
    )
    db_session.add(eval_obj)
    db_session.flush()

    tests = generate_evaluation_plan(db_session, eval_obj.id)
    db_session.commit()

    return {
        "user": user,
        "instrument": inst,
        "configuration": config,
        "rule_version": rv,
        "evaluation": eval_obj,
        "tests": tests,
    }


# ==============================================================================
# SCENARIO 1: Valid weighing-performance calculation -> PASS
# ==============================================================================

def test_scenario_01_valid_weighing_performance_pass(db_session: Session, test_env):
    """Scenario 1: Valid weighing-performance calculation produces PASS with non-fabricated outputs."""
    tests = test_env["tests"]
    w_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = w_test.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["compliance"]["decision"] == "PASS"
    assert res["calculation"] is not None
    assert Decimal(res["calculation"]["output"]["Ec"]) == Decimal("0")
    assert Decimal(res["calculation"]["output"]["mpe_mass"]) == Decimal("0.010")
    assert "+0.010" in res["compliance"]["margin"]


# ==============================================================================
# SCENARIO 2: Weighing-performance missing zero error -> INCOMPLETE
# ==============================================================================

def test_scenario_02_weighing_performance_missing_zero_error_incomplete(db_session: Session, test_env):
    """Scenario 2: Missing zero error MUST NOT fallback to Decimal('0'); must result in INCOMPLETE."""
    tests = test_env["tests"]
    w_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = w_test.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    # Omit ZERO_ERROR

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert res["calculation"] is None
    assert "ZERO_ERROR" in res["compliance"]["reasoning"]["missing_observations"]
    assert w_test.status == EvaluationTestStatus.INCOMPLETE


# ==============================================================================
# SCENARIO 3: Weighing-performance missing indication -> INCOMPLETE
# ==============================================================================

def test_scenario_03_weighing_performance_missing_indication_incomplete(db_session: Session, test_env):
    """Scenario 3: Missing indication MUST NOT fallback to synthetic value; must result in INCOMPLETE."""
    tests = test_env["tests"]
    w_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = w_test.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")
    # Omit INDICATION

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert res["calculation"] is None
    assert "INDICATION" in res["compliance"]["reasoning"]["missing_observations"]


# ==============================================================================
# SCENARIO 4: Invalid load -> rejected
# ==============================================================================

def test_scenario_04_invalid_load_rejected(db_session: Session, test_env):
    """Scenario 4: Negative load, zero load, and gross overload (> Max + 9e) are rejected."""
    tests = test_env["tests"]
    w_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = w_test.attempts[0]

    # Negative load
    with pytest.raises(ValueError, match="strictly positive"):
        record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("-5.00"), unit="kg")

    # Zero load
    with pytest.raises(ValueError, match="strictly positive"):
        record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("0.00"), unit="kg")

    # Gross overload (Max is 30 kg, e is 0.010 kg, limit is 30.09 kg)
    with pytest.raises(ValueError, match="exceeds allowable range limit"):
        record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("45.00"), unit="kg")


# ==============================================================================
# SCENARIO 5: Valid eccentricity -> PASS
# ==============================================================================

def test_scenario_05_valid_eccentricity_pass(db_session: Session, test_env):
    """Scenario 5: Valid eccentricity test with 4 quarter segments passes."""
    tests = test_env["tests"]
    ecc_test = next(t for t in tests if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]

    positions = ["QUARTER_1", "QUARTER_2", "QUARTER_3", "QUARTER_4"]
    for pos in positions:
        record_observation(
            db_session,
            attempt.id,
            f"POS_{pos}",
            unit="kg",
            value_json={
                "position": pos,
                "load": "10.000",
                "indication": "10.000",
                "additional_load": "0.005",
                "zero_error": "0.000",
                "unit": "kg",
            },
        )

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["compliance"]["decision"] == "PASS"
    assert res["calculation"] is not None
    assert len(res["calculation"]["output"]["position_results"]) == 4
    assert Decimal(res["calculation"]["output"]["max_absolute_error"]) == Decimal("0")


# ==============================================================================
# SCENARIO 6: Missing eccentricity position -> INCOMPLETE
# ==============================================================================

def test_scenario_06_missing_eccentricity_position_incomplete(db_session: Session, test_env):
    """Scenario 6: Missing required positions must result in INCOMPLETE without synthesized fallback."""
    tests = test_env["tests"]
    ecc_test = next(t for t in tests if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]

    # Record only 2 positions (QUARTER_1 and QUARTER_2)
    for pos in ["QUARTER_1", "QUARTER_2"]:
        record_observation(
            db_session,
            attempt.id,
            f"POS_{pos}",
            unit="kg",
            value_json={
                "position": pos,
                "load": "10.000",
                "indication": "10.000",
                "additional_load": "0.005",
                "zero_error": "0.000",
                "unit": "kg",
            },
        )

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert res["calculation"] is None
    missing = res["compliance"]["reasoning"]["missing_observations"]
    assert "QUARTER_3" in missing
    assert "QUARTER_4" in missing


# ==============================================================================
# SCENARIO 7: Valid repeatability -> PASS
# ==============================================================================

def test_scenario_07_valid_repeatability_pass(db_session: Session, test_env):
    """Scenario 7: Valid repeatability with minimum 10 weighings per series (< 1000 kg) passes."""
    tests = test_env["tests"]
    rep_test = next(t for t in tests if t.test_definition.test_code == "REPEATABILITY")
    attempt = rep_test.attempts[0]

    # 10 weighings for 50% Max
    for i in range(1, 11):
        record_observation(
            db_session,
            attempt.id,
            "REPEATABILITY_WEIGHING",
            unit="kg",
            value_json={
                "series": "50_PERCENT_MAX",
                "weighing_index": i,
                "test_load": "15.000",
                "loaded_indication": "15.000" if i % 2 == 0 else "15.005",
                "unloaded_indication": "0.000",
                "unit": "kg",
            },
        )

    # 10 weighings for 100% Max
    for i in range(1, 11):
        record_observation(
            db_session,
            attempt.id,
            "REPEATABILITY_WEIGHING",
            unit="kg",
            value_json={
                "series": "100_PERCENT_MAX",
                "weighing_index": i,
                "test_load": "30.000",
                "loaded_indication": "30.000" if i % 2 == 0 else "30.005",
                "unloaded_indication": "0.000",
                "unit": "kg",
            },
        )

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["compliance"]["decision"] == "PASS"
    assert res["calculation"] is not None
    assert res["calculation"]["output"]["repeatability_error"] == "0.005"
    assert "series_50" in res["calculation"]["output"]
    assert "series_100" in res["calculation"]["output"]


# ==============================================================================
# SCENARIO 8: Repeatability with insufficient weighings -> INCOMPLETE
# ==============================================================================

def test_scenario_08_repeatability_insufficient_weighings_incomplete(db_session: Session, test_env):
    """Scenario 8: Fewer than required weighings (e.g. 5 instead of 10) must result in INCOMPLETE."""
    tests = test_env["tests"]
    rep_test = next(t for t in tests if t.test_definition.test_code == "REPEATABILITY")
    attempt = rep_test.attempts[0]

    # Record only 5 weighings for 50% series, none for 100% series
    for i in range(1, 6):
        record_observation(
            db_session,
            attempt.id,
            "REPEATABILITY_WEIGHING",
            unit="kg",
            value_json={
                "series": "50_PERCENT_MAX",
                "weighing_index": i,
                "test_load": "15.000",
                "loaded_indication": "15.000",
                "unloaded_indication": "0.000",
                "unit": "kg",
            },
        )

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert res["calculation"] is None
    missing = res["compliance"]["reasoning"]["missing_observations"]

    assert any("50_PERCENT_MAX has 5/10" in m for m in missing)
    assert any("100_PERCENT_MAX has 0/10" in m for m in missing)


# ==============================================================================
# SCENARIO 9: Repeatability duplicate index -> rejected
# ==============================================================================

def test_scenario_09_repeatability_duplicate_index_rejected(db_session: Session, test_env):
    """Scenario 9: Duplicate weighing_index within a series is rejected immediately."""
    tests = test_env["tests"]
    rep_test = next(t for t in tests if t.test_definition.test_code == "REPEATABILITY")
    attempt = rep_test.attempts[0]

    record_observation(
        db_session,
        attempt.id,
        "REPEATABILITY_WEIGHING",
        value_json={
            "series": "50_PERCENT_MAX",
            "weighing_index": 1,
            "test_load": "15.000",
            "loaded_indication": "15.000",
            "unloaded_indication": "0.000",
        },
    )

    with pytest.raises(ValueError, match="Duplicate weighing_index 1"):
        record_observation(
            db_session,
            attempt.id,
            "REPEATABILITY_WEIGHING",
            value_json={
                "series": "50_PERCENT_MAX",
                "weighing_index": 1,
                "test_load": "15.000",
                "loaded_indication": "15.005",
                "unloaded_indication": "0.000",
            },
        )


# ==============================================================================
# SCENARIO 10: Repeatability malformed JSON -> rejected
# ==============================================================================

def test_scenario_10_repeatability_malformed_json_rejected(db_session: Session, test_env):
    """Scenario 10: Non-numeric, negative index, or arbitrary malformed JSON payload is rejected."""
    tests = test_env["tests"]
    rep_test = next(t for t in tests if t.test_definition.test_code == "REPEATABILITY")
    attempt = rep_test.attempts[0]

    # Non-numeric test_load
    with pytest.raises(ValueError, match="Invalid repeatability observation payload"):
        record_observation(
            db_session,
            attempt.id,
            "REPEATABILITY_WEIGHING",
            value_json={
                "series": "50_PERCENT_MAX",
                "weighing_index": 1,
                "test_load": "NOT_A_NUMBER",
                "loaded_indication": "15.000",
                "unloaded_indication": "0.000",
            },
        )

    # Negative index
    with pytest.raises(ValueError, match="Invalid repeatability observation payload"):
        record_observation(
            db_session,
            attempt.id,
            "REPEATABILITY_WEIGHING",
            value_json={
                "series": "50_PERCENT_MAX",
                "weighing_index": -1,
                "test_load": "15.000",
                "loaded_indication": "15.000",
                "unloaded_indication": "0.000",
            },
        )

    # Invalid series name
    with pytest.raises(ValueError, match="Invalid repeatability observation payload"):
        record_observation(
            db_session,
            attempt.id,
            "REPEATABILITY_WEIGHING",
            value_json={
                "series": "75_PERCENT_MAX",
                "weighing_index": 1,
                "test_load": "15.000",
                "loaded_indication": "15.000",
                "unloaded_indication": "0.000",
            },
        )


# ==============================================================================
# SCENARIO 11: MPE lower/upper boundary tests
# ==============================================================================

def test_scenario_11_mpe_table_boundaries():
    """Scenario 11: MPE Table 6 boundaries are verified for all implemented classes."""
    e = Decimal("0.010")

    # Class III: Band 1: 0 <= m <= 500 e -> 0.5e
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, load=Decimal("5.000"), e=e, load_unit="kg", e_unit="kg")
    assert res.load_in_e == Decimal("500")
    assert res.mpe_factor == Decimal("0.5")
    assert res.mpe_mass == Decimal("0.0050")

    # Class III: Band 2: 500 < m <= 2000 e -> 1.0e
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, load=Decimal("5.010"), e=e, load_unit="kg", e_unit="kg")
    assert res.load_in_e == Decimal("501")
    assert res.mpe_factor == Decimal("1.0")

    # Class III: Band 3: 2000 < m <= 10000 e -> 1.5e
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, load=Decimal("100.000"), e=e, load_unit="kg", e_unit="kg")
    assert res.load_in_e == Decimal("10000")
    assert res.mpe_factor == Decimal("1.5")
    assert res.mpe_mass == Decimal("0.0150")

    # Class IIII: Upper boundary is 1000 e
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_IIII, load=Decimal("10.000"), e=e, load_unit="kg", e_unit="kg")
    assert res.load_in_e == Decimal("1000")
    assert res.mpe_factor == Decimal("1.5")


# ==============================================================================
# SCENARIO 12: Out-of-range MPE configuration -> invalid/unsupported
# ==============================================================================

def test_scenario_12_out_of_range_mpe_configuration_rejected():
    """Scenario 12: Loads exceeding Table 6 boundary are rejected with explicit error; never extrapolated."""
    e = Decimal("0.010")

    # Class III: Table 6 upper limit is 10,000 e (100 kg with e=0.01 kg)
    # Load 150 kg = 15,000 e -> must be rejected
    with pytest.raises(ValueError, match="exceeds maximum Table 6 boundary"):
        MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, load=Decimal("150.000"), e=e, load_unit="kg", e_unit="kg")

    # Class IIII: Table 6 upper limit is 1,000 e (10 kg with e=0.01 kg)
    # Load 15 kg = 1,500 e -> must be rejected
    with pytest.raises(ValueError, match="exceeds maximum Table 6 boundary"):
        MPEEngine.calculate_mpe(AccuracyClass.CLASS_IIII, load=Decimal("15.000"), e=e, load_unit="kg", e_unit="kg")


# ==============================================================================
# SCENARIO 13: Multiple-range uses correct range Max/e
# ==============================================================================

def test_scenario_13_multiple_range_uses_correct_range_max_e(db_session: Session, test_env):
    """Scenario 13: Multi-range tests correctly scope Max/Min/e/d to range; range_index=0 handled safely."""
    user = test_env["user"]
    inst = test_env["instrument"]
    config = test_env["configuration"]
    rv = test_env["rule_version"]

    snapshot = {
        "accuracy_class": "CLASS_III",
        "max_capacity": "30.000",
        "min_capacity": "0.200",
        "verification_scale_interval": "0.010",
        "actual_scale_interval": "0.010",
        "unit": "kg",
        "number_of_ranges": 2,
        "is_multiple_range": True,
        "is_electronic": True,
        "ranges": [
            {
                "range_index": 1,
                "max_capacity": "15.000",
                "min_capacity": "0.200",
                "verification_scale_interval": "0.005",
                "actual_scale_interval": "0.005",
                "unit": "kg",
            },
            {
                "range_index": 2,
                "max_capacity": "30.000",
                "min_capacity": "15.000",
                "verification_scale_interval": "0.010",
                "actual_scale_interval": "0.010",
                "unit": "kg",
            },
        ],
    }

    eval_obj = Evaluation(
        evaluation_number=f"EVAL-MR-{uuid.uuid4().hex[:6]}",
        instrument_id=inst.id,
        instrument_configuration_id=config.id,
        rule_version_id=rv.id,
        operator_id=user.id,
        status=EvaluationStatus.IN_PROGRESS,
        configuration_snapshot=snapshot,
    )
    db_session.add(eval_obj)
    db_session.flush()

    tests = generate_evaluation_plan(db_session, eval_obj.id)
    db_session.commit()

    range1_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE" and t.range_index == 1)
    assert range1_test.range_index == 1

    attempt = range1_test.attempts[0]

    # Loading 20 kg on Range 1 (Max 15 kg + 9*0.005 = 15.045 kg) must be rejected
    with pytest.raises(ValueError, match="exceeds allowable range limit"):
        record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("20.000"), unit="kg")

    # Record valid Range 1 observation with e = 0.005 kg
    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.0025"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "PASS"
    # Range 1 e is 0.005 kg (10 kg = 2000 e -> MPE = 1.0 e = 0.005 kg)
    assert res["calculation"]["output"]["mpe_mass"] == "0.0050"


# ==============================================================================
# SCENARIO 14: RuleVersion is actually used by calculation/compliance dispatch
# ==============================================================================

def test_scenario_14_rule_version_dispatch(db_session: Session, test_env):
    """Scenario 14: RuleVersion participates deterministically; content_hash and id recorded in traces."""
    tests = test_env["tests"]
    w_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = w_test.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")

    res = execute_attempt_calculation(db_session, attempt.id)

    rv = test_env["rule_version"]
    assert res["compliance"]["reasoning"]["rule_version_id"] == str(rv.id)
    assert res["compliance"]["reasoning"]["rule_content_hash"] == rv.content_hash

    # Verify persisted in database
    calc = db_session.scalar(select(Calculation).where(Calculation.test_attempt_id == attempt.id))
    comp = db_session.scalar(select(ComplianceResult).where(ComplianceResult.test_attempt_id == attempt.id))
    assert calc.rule_version_id == rv.id
    assert comp.rule_version_id == rv.id


# ==============================================================================
# SCENARIO 15: Observation modification after calculation -> rejected
# ==============================================================================

def test_scenario_15_observation_locking_after_calculation(db_session: Session, test_env):
    """Scenario 15: Once calculation/compliance is executed, observations on that attempt are locked."""
    tests = test_env["tests"]
    w_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = w_test.attempts[0]

    obs1 = record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")

    # Authoritative calculation executes
    execute_attempt_calculation(db_session, attempt.id)

    # Attempting to add a new observation must fail with ObservationLockedError
    with pytest.raises(ObservationLockedError, match="locked because calculations or compliance results already exist"):
        record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")

    # Attempting to modify an existing observation must fail with ObservationLockedError
    with pytest.raises(ObservationLockedError, match="locked"):
        update_observation(db_session, obs1.id, value_numeric=Decimal("12.000"))


# ==============================================================================
# SCENARIO 16: Retest preserves Attempt 1 and creates Attempt 2
# ==============================================================================

def test_scenario_16_retest_preserves_history(db_session: Session, test_env):
    """Scenario 16: Retest creates fresh Attempt 2; Attempt 1 and its failing compliance decision remain intact."""
    tests = test_env["tests"]
    w_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt1 = w_test.attempts[0]

    # Failing measurement for Attempt 1
    record_observation(db_session, attempt1.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt1.id, "INDICATION", value_numeric=Decimal("10.030"), unit="kg")
    record_observation(db_session, attempt1.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt1.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")

    res1 = execute_attempt_calculation(db_session, attempt1.id)
    assert res1["compliance"]["decision"] == "FAIL"

    # Create Retest (Attempt 2)
    attempt2 = create_retest_attempt(db_session, w_test.id, notes="Re-zeroed receptor")
    assert attempt2.attempt_number == 2
    assert attempt2.supersedes_attempt_id == attempt1.id
    assert attempt2.status == TestAttemptStatus.ACTIVE

    # Passing measurements for Attempt 2
    record_observation(db_session, attempt2.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt2.id, "INDICATION", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt2.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt2.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")

    res2 = execute_attempt_calculation(db_session, attempt2.id)
    assert res2["compliance"]["decision"] == "PASS"

    # Verify Attempt 1 history was NOT overwritten
    db_session.refresh(attempt1)
    assert len(attempt1.compliance_results) == 1
    assert attempt1.compliance_results[0].decision == ComplianceDecision.FAIL


# ==============================================================================
# SCENARIO 17: Trace contains complete evidence chain
# ==============================================================================

def test_scenario_17_trace_complete_evidence_chain(db_session: Session, test_env):
    """Scenario 17: Trace contains complete evidence hierarchy answering 'Why did it pass/fail?'."""
    tests = test_env["tests"]
    w_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = w_test.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")

    execute_attempt_calculation(db_session, attempt.id)

    trace = get_test_attempt_trace(db_session, attempt.id)

    assert trace["instrument"]["serial_number"] is not None
    assert trace["configuration_snapshot"]["accuracy_class"] == "CLASS_III"
    assert trace["evaluation"]["evaluation_number"] is not None
    assert trace["evaluation_test"]["test_code"] == "WEIGHING_PERFORMANCE"
    assert trace["test_attempt_id"] == str(attempt.id)
    assert len(trace["raw_observations"]) == 4
    assert trace["calculation"]["code"] == "R76_A4_4_3_ERROR"
    assert trace["rule_version"]["content_hash"] is not None
    assert trace["compliance"]["decision"] == "PASS"
    assert trace["compliance"]["reasoning"]["explanation"] is not None


# ==============================================================================
# SCENARIO 18: Transaction rollback on failure
# ==============================================================================

def test_scenario_18_transaction_rollback_on_failure(db_session: Session, test_env, monkeypatch):
    """Scenario 18: If compliance persistence fails, calculation is rolled back atomically."""
    tests = test_env["tests"]
    w_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = w_test.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")

    att_id = attempt.id

    # Inject failure during compliance evaluation
    def fail_eval(*args, **kwargs):
        raise RuntimeError("Simulated internal error during compliance evaluation")

    monkeypatch.setattr(ComplianceEngine, "evaluate", fail_eval)

    with pytest.raises(RuntimeError, match="Simulated internal error"):
        execute_attempt_calculation(db_session, att_id)

    # Verify no orphan calculation or compliance records exist
    calcs = db_session.scalars(select(Calculation).where(Calculation.test_attempt_id == att_id)).all()
    comps = db_session.scalars(select(ComplianceResult).where(ComplianceResult.test_attempt_id == att_id)).all()
    assert len(calcs) == 0
    assert len(comps) == 0


# ==============================================================================
# SCENARIO 19: Configuration validation fail-closed behavior
# ==============================================================================

def test_scenario_19_configuration_validation_fail_closed():
    """Scenario 19: Configuration validation rejects absent, negative, inconsistent, or invalid configs."""
    valid_base = {
        "accuracy_class": "CLASS_III",
        "max_capacity": "30.000",
        "min_capacity": "0.200",
        "verification_scale_interval": "0.010",
        "actual_scale_interval": "0.010",
        "unit": "kg",
        "is_electronic": True,
        "is_multiple_range": False,
    }

    # Valid base must pass
    validate_configuration_snapshot(valid_base)

    # Missing accuracy class
    with pytest.raises(ConfigurationValidationError, match="Missing required configuration attribute: 'accuracy_class'"):
        snap = dict(valid_base)
        del snap["accuracy_class"]
        validate_configuration_snapshot(snap)

    # Invalid accuracy class
    with pytest.raises(ConfigurationValidationError, match="Invalid accuracy class"):
        snap = dict(valid_base, accuracy_class="CLASS_INVALID")
        validate_configuration_snapshot(snap)

    # Max <= 0
    with pytest.raises(ConfigurationValidationError, match="max_capacity must be strictly positive"):
        snap = dict(valid_base, max_capacity="-10")
        validate_configuration_snapshot(snap)

    # Min > Max
    with pytest.raises(ConfigurationValidationError, match="min_capacity .* cannot exceed max_capacity"):
        snap = dict(valid_base, min_capacity="40.000")
        validate_configuration_snapshot(snap)

    # Actual scale interval d > e
    with pytest.raises(ConfigurationValidationError, match="actual_scale_interval d .* cannot exceed verification_scale_interval e"):
        snap = dict(valid_base, actual_scale_interval="0.050", verification_scale_interval="0.010")
        validate_configuration_snapshot(snap)

    # Unsupported unit
    with pytest.raises(ConfigurationValidationError, match="Unsupported unit: 'lb'"):
        snap = dict(valid_base, unit="lb")
        validate_configuration_snapshot(snap)

    # Multi-range with < 2 ranges
    with pytest.raises(ConfigurationValidationError, match="requires at least 2 ranges"):
        snap = dict(valid_base, is_multiple_range=True, ranges=[{"range_index": 1}])
        validate_configuration_snapshot(snap)

    # Multi-range with duplicate range indexes
    with pytest.raises(ConfigurationValidationError, match="Duplicate range_index"):
        snap = dict(
            valid_base,
            is_multiple_range=True,
            ranges=[
                {"range_index": 1, "max_capacity": "15", "min_capacity": "0.2", "verification_scale_interval": "0.005", "actual_scale_interval": "0.005", "unit": "kg"},
                {"range_index": 1, "max_capacity": "30", "min_capacity": "15", "verification_scale_interval": "0.010", "actual_scale_interval": "0.010", "unit": "kg"},
            ],
        )
        validate_configuration_snapshot(snap)

    # Multi-range non-increasing capacities
    with pytest.raises(ConfigurationValidationError, match="must be strictly increasing"):
        snap = dict(
            valid_base,
            is_multiple_range=True,
            ranges=[
                {"range_index": 1, "max_capacity": "20", "min_capacity": "0.2", "verification_scale_interval": "0.005", "actual_scale_interval": "0.005", "unit": "kg"},
                {"range_index": 2, "max_capacity": "15", "min_capacity": "10", "verification_scale_interval": "0.010", "actual_scale_interval": "0.010", "unit": "kg"},
            ],
        )
        validate_configuration_snapshot(snap)

    # Missing is_electronic
    with pytest.raises(ConfigurationValidationError, match="Missing required configuration attribute: 'is_electronic'"):
        snap = dict(valid_base)
        del snap["is_electronic"]
        validate_configuration_snapshot(snap)
