"""Comprehensive Phase 2 Final Regression Verification Test Suite.

Authoritative coverage for all 39 regression test scenarios specified in Part M:
- Eccentricity (1-11)
- Unit Normalization (12-20)
- Configuration Fail-Closed & Boolean Coercion (21-22)
- Multi-Range Safety (23-25)
- Repeatability Dual-Series (26-30)
- RuleVersion Deterministic Dispatch (31-34)
- Observation Immutability & Retest (35-37)
- End-to-End Metrological Traceability (38-39)
"""

from decimal import Decimal
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.applicability import (
    ApplicabilityEngine,
    ConfigurationValidationError,
    calculate_required_eccentricity_load,
    determine_eccentricity_procedure,
)
from app.engines.calculation import CalculationEngine, CalculationOutput
from app.engines.compliance import ComplianceDecision, ComplianceEngine, ComplianceEvaluation
from app.models.configuration import AccuracyClass, InstrumentConfiguration, TareType
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.instrument import Instrument
from app.models.metrology import Calculation, ComplianceResult
from app.models.rule import Rule, RuleVersion
from app.models.test_definition import ImplementationStatus, TestDefinition
from app.models.test_execution import (
    EvaluationTest,
    Observation,
    TestAttempt,
    TestAttemptStatus,
    TestStep,
)
from app.services.calculation_service import execute_attempt_calculation
from app.services.plan_service import (
    create_initial_steps_for_attempt,
    ensure_test_definitions,
    generate_evaluation_plan,
)
from app.services.test_service import (
    ObservationLockedError,
    create_retest_attempt,
    record_observation,
)


@pytest.fixture
def base_fixture(db_session: Session):
    """Canonical test setup with standard OIML R-76 rules and canonical definitions."""
    ensure_test_definitions(db_session)
    rule = db_session.scalar(select(Rule).where(Rule.code == "OIML-R76-2006"))
    if not rule:
        rule = Rule(code="OIML-R76-2006", name="OIML R 76-1:2006", description="NAWI standard")
        db_session.add(rule)
        db_session.flush()

    rule_def = {
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
    }

    rv = RuleVersion(
        rule_id=rule.id,
        version_number=f"2006-final-{uuid.uuid4().hex[:6]}",
        standard_version="OIML R 76-1: 2006 (E)",
        clause="A.4",
        calculation_identifier="R76_A4_4_3_ERROR",
        applicability_identifier="R76_APPLICABILITY_V1",
        aggregation_strategy="ALL_POINTS_PASS",
        definition_json=rule_def,
        content_hash="canonical_hash",
        is_active=True,
    )
    db_session.add(rv)
    db_session.flush()

    return {"rule": rule, "rule_version": rv}


def create_eval_env(
    db: Session,
    base_fixture: dict,
    extra_caps: dict = None,
    max_cap: str = "30.000",
    unit: str = "kg",
    ranges: list = None,
    is_multiple_range: bool = False,
):
    """Helper to instantiate complete instrument, evaluation, and test plan."""
    rv = base_fixture["rule_version"]
    caps = extra_caps if extra_caps is not None else {
        "load_receptor": {
            "support_count": 4,
            "special_receptor": False,
            "rolling_load": False,
        }
    }

    inst = Instrument(
        serial_number=f"SN-{uuid.uuid4().hex[:8].upper()}",
        manufacturer="Metrology-Corp",
        model_name="P2-Verifier",
        is_synthetic=True,
    )
    db.add(inst)
    db.flush()

    num_ranges = len(ranges) if ranges else 1
    config = InstrumentConfiguration(
        instrument_id=inst.id,
        accuracy_class=AccuracyClass.CLASS_III,
        max_capacity=Decimal(max_cap),
        min_capacity=Decimal("0.200"),
        verification_scale_interval=Decimal("0.010"),
        actual_scale_interval=Decimal("0.010"),
        unit=unit,
        number_of_ranges=num_ranges,
        is_multiple_range=is_multiple_range,
        tare_type=TareType.SUBTRACTIVE,
        is_electronic=True,
        has_zero_setting=True,
        extra_capabilities=caps,
    )
    db.add(config)
    db.flush()

    snapshot = {
        "accuracy_class": "CLASS_III",
        "max_capacity": max_cap,
        "min_capacity": "0.200",
        "verification_scale_interval": "0.010",
        "actual_scale_interval": "0.010",
        "unit": unit,
        "number_of_ranges": num_ranges,
        "is_multiple_range": is_multiple_range,
        "is_electronic": True,
        "has_zero_setting": True,
        "tare_type": "SUBTRACTIVE",
        "ranges": ranges or [],
        "extra_capabilities": caps,
    }

    eval_obj = Evaluation(
        evaluation_number=f"EVAL-{uuid.uuid4().hex[:8].upper()}",
        instrument_id=inst.id,
        instrument_configuration_id=config.id,
        rule_version_id=rv.id,
        status=EvaluationStatus.IN_PROGRESS,
        configuration_snapshot=snapshot,
    )
    db.add(eval_obj)
    db.flush()

    tests = generate_evaluation_plan(db, eval_obj.id)
    db.commit()

    return {
        "instrument": inst,
        "configuration": config,
        "evaluation": eval_obj,
        "tests": tests,
        "snapshot": snapshot,
    }


# ==============================================================================
# PART A & B: ECCENTRICITY REGRESSION TESTS (1 - 11)
# ==============================================================================

def test_01_4_support_configuration_generates_four_quarter_segments(db_session: Session, base_fixture):
    """1. 4-support configuration generates four quarter segments."""
    env = create_eval_env(db_session, base_fixture, extra_caps={
        "load_receptor": {"support_count": 4, "special_receptor": False, "rolling_load": False}
    })
    ecc_test = next(t for t in env["tests"] if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]
    steps = attempt.steps

    assert len(steps) == 4
    step_codes = [s.step_code for s in steps]
    assert step_codes == ["STEP_QUARTER_1", "STEP_QUARTER_2", "STEP_QUARTER_3", "STEP_QUARTER_4"]
    for s in steps:
        assert s.metadata_json["procedure"] == "FOUR_QUARTER_SEGMENTS"
        assert Decimal(s.metadata_json["required_test_load"]) == Decimal("10")
        assert s.metadata_json["unit"] == "kg"


def test_02_4_support_does_not_generate_center_front_back_left_right(db_session: Session, base_fixture):
    """2. 4-support configuration does NOT generate CENTER/FRONT/BACK/LEFT/RIGHT."""
    env = create_eval_env(db_session, base_fixture, extra_caps={
        "load_receptor": {"support_count": 4, "special_receptor": False, "rolling_load": False}
    })
    ecc_test = next(t for t in env["tests"] if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]
    step_codes = [s.step_code for s in attempt.steps]

    for legacy in ["STEP_POS_CENTER", "STEP_POS_FRONT", "STEP_POS_BACK", "STEP_POS_LEFT", "STEP_POS_RIGHT"]:
        assert legacy not in step_codes


def test_03_6_support_configuration_generates_support_1_to_6(db_session: Session, base_fixture):
    """3. 6-support configuration generates SUPPORT_1 through SUPPORT_6."""
    env = create_eval_env(db_session, base_fixture, extra_caps={
        "load_receptor": {"support_count": 6, "special_receptor": False, "rolling_load": False}
    })
    ecc_test = next(t for t in env["tests"] if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]
    steps = attempt.steps

    assert len(steps) == 6
    step_codes = [s.step_code for s in steps]
    expected_codes = [f"STEP_SUPPORT_{i}" for i in range(1, 7)]
    assert step_codes == expected_codes
    for s in steps:
        assert s.metadata_json["procedure"] == "SUPPORT_SPECIFIC"
        # Required load for 6 supports: Max / (6 - 1) = 30 / 5 = 6 kg
        assert Decimal(s.metadata_json["required_test_load"]) == Decimal("6")


def test_04_rolling_load_configuration_generates_roll_positions(db_session: Session, base_fixture):
    """4. rolling-load configuration generates ROLL_BEGIN, ROLL_MIDDLE, ROLL_END."""
    env = create_eval_env(db_session, base_fixture, extra_caps={
        "load_receptor": {"rolling_load": True, "support_count": 4}
    })
    ecc_test = next(t for t in env["tests"] if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]
    steps = attempt.steps

    assert len(steps) == 3
    step_codes = [s.step_code for s in steps]
    assert step_codes == ["STEP_ROLL_BEGIN", "STEP_ROLL_MIDDLE", "STEP_ROLL_END"]
    for s in steps:
        assert s.metadata_json["procedure"] == "ROLLING_LOAD"


def test_05_missing_geometry_fails_closed(db_session: Session, base_fixture):
    """5. missing geometry fails closed (marked BLOCKED/UNSUPPORTED)."""
    snapshot = {
        "accuracy_class": "CLASS_III",
        "max_capacity": "30.000",
        "min_capacity": "0.200",
        "verification_scale_interval": "0.010",
        "actual_scale_interval": "0.010",
        "unit": "kg",
        "is_electronic": True,
        "tare_type": "SUBTRACTIVE",
        "ranges": [],
        # No extra_capabilities / load_receptor geometry
    }
    plan = ApplicabilityEngine.evaluate_plan(snapshot)
    ecc_item = next(item for item in plan if item.test_code == "ECCENTRICITY")

    assert ecc_item.applicable is False
    assert "BLOCKED" in ecc_item.reason
    assert "Missing required 'load_receptor' geometry metadata" in ecc_item.reason


def test_06_eccentricity_required_load_max_30kg_tare_0_is_10kg():
    """6. eccentricity required load for Max=30 kg, additive tare=0 equals 10 kg."""
    snapshot = {
        "max_capacity": "30.000",
        "extra_capabilities": {
            "load_receptor": {"support_count": 4, "special_receptor": False, "rolling_load": False}
        },
    }
    proc_info = determine_eccentricity_procedure(snapshot)
    load = calculate_required_eccentricity_load(snapshot, proc_info)
    assert load == Decimal("10")


def test_07_non_zero_additive_tare_changes_required_load_correctly():
    """7. non-zero additive tare changes the required load correctly: (Max + tare)/3."""
    snapshot = {
        "max_capacity": "30.000",
        "maximum_additive_tare_effect": "6.000",
        "extra_capabilities": {
            "load_receptor": {"support_count": 4, "special_receptor": False, "rolling_load": False}
        },
    }
    proc_info = determine_eccentricity_procedure(snapshot)
    load = calculate_required_eccentricity_load(snapshot, proc_info)
    # (30 + 6) / 3 = 12 kg
    assert load == Decimal("12")


def test_08_wrong_eccentricity_load_cannot_produce_pass(db_session: Session, base_fixture):
    """8. wrong eccentricity load cannot produce PASS (deterministic INCOMPLETE)."""
    env = create_eval_env(db_session, base_fixture)
    ecc_test = next(t for t in env["tests"] if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]

    # Required load is 10 kg. Operator applies 5 kg.
    positions = ["QUARTER_1", "QUARTER_2", "QUARTER_3", "QUARTER_4"]
    for pos in positions:
        record_observation(
            db_session,
            attempt.id,
            f"POS_{pos}",
            unit="kg",
            value_json={
                "position": pos,
                "load": "5.000",
                "indication": "5.000",
                "additional_load": "0.005",
                "zero_error": "0.000",
                "unit": "kg",
            },
        )
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert res["calculation"] is None
    assert "Incorrect eccentricity test load" in res["compliance"]["reasoning"]["reason"]


def test_09_missing_eccentricity_load_produces_incomplete(db_session: Session, base_fixture):
    """9. missing eccentricity load produces INCOMPLETE."""
    env = create_eval_env(db_session, base_fixture)
    ecc_test = next(t for t in env["tests"] if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]

    for pos in ["QUARTER_1", "QUARTER_2", "QUARTER_3", "QUARTER_4"]:
        record_observation(
            db_session,
            attempt.id,
            f"POS_{pos}",
            unit="kg",
            value_json={
                "position": pos,
                "indication": "10.000",
                "additional_load": "0.005",
                "zero_error": "0.000",
                "unit": "kg",
                # 'load' omitted
            },
        )
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert res["calculation"] is None
    assert "missing: load" in res["compliance"]["reasoning"]["reason"]


def test_10_duplicate_positions_are_rejected(db_session: Session, base_fixture):
    """10. duplicate positions are rejected."""
    env = create_eval_env(db_session, base_fixture)
    ecc_test = next(t for t in env["tests"] if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]

    record_observation(
        db_session,
        attempt.id,
        "POS_QUARTER_1",
        unit="kg",
        value_json={"position": "QUARTER_1", "load": "10.000", "indication": "10.000", "unit": "kg"},
    )
    with pytest.raises(ValueError, match="Duplicate eccentricity position"):
        record_observation(
            db_session,
            attempt.id,
            "POS_QUARTER_1_DUP",
            unit="kg",
            value_json={"position": "QUARTER_1", "load": "10.000", "indication": "10.000", "unit": "kg"},
        )


def test_11_missing_required_eccentricity_fields_produce_incomplete(db_session: Session, base_fixture):
    """11. missing required eccentricity fields produce INCOMPLETE."""
    env = create_eval_env(db_session, base_fixture)
    ecc_test = next(t for t in env["tests"] if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]

    for pos in ["QUARTER_1", "QUARTER_2", "QUARTER_3", "QUARTER_4"]:
        payload = {
            "position": pos,
            "load": "10.000",
            "indication": "10.000",
            "additional_load": "0.005",
            "unit": "kg",
        }
        if pos != "QUARTER_4":
            payload["zero_error"] = "0.000"
        record_observation(db_session, attempt.id, f"POS_{pos}", unit="kg", value_json=payload)
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert "QUARTER_4 missing: zero_error" in res["compliance"]["reasoning"]["reason"]


# ==============================================================================
# PART C & D: UNIT NORMALIZATION TESTS (12 - 20)
# ==============================================================================

def test_12_kg_input_works(db_session: Session, base_fixture):
    """12. kg input works directly in calculation."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("15.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "PASS"
    assert res["calculation"] is not None
    assert Decimal(res["calculation"]["output"]["Ec"]) == Decimal("0")


def test_13_g_input_is_converted_to_kg(db_session: Session, base_fixture):
    """13. g input is converted to kg."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    # 15000 g == 15 kg
    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15000"), unit="g")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("15000"), unit="g")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("5"), unit="g")  # 0.005 kg
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0"), unit="g")
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "PASS"
    input_snap = res["calculation"]["input_snapshot"]
    assert Decimal(input_snap["load"]) == Decimal("15")
    assert input_snap["unit"] == "kg"


def test_14_mg_input_is_converted_to_kg(db_session: Session, base_fixture):
    """14. mg input is converted to kg."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    # 15000000 mg == 15 kg
    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15000000"), unit="mg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("15000000"), unit="mg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("5000"), unit="mg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0"), unit="mg")
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "PASS"
    input_snap = res["calculation"]["input_snapshot"]
    assert Decimal(input_snap["load"]) == Decimal("15")


def test_15_missing_unit_fails_closed(db_session: Session, base_fixture):
    """15. missing unit fails closed."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    # Omit unit entirely
    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15.000"), unit=None)
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("15.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert "Missing required unit on observation" in res["compliance"]["reasoning"]["reason"]


def test_16_unknown_unit_fails_closed(db_session: Session, base_fixture):
    """16. unknown unit fails closed."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    with pytest.raises(ValueError, match="Unsupported metrological unit"):
        record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15.000"), unit="nonexistent_unit")


def test_17_mixed_compatible_units_normalize_correctly(db_session: Session, base_fixture):
    """17. mixed compatible units normalize correctly."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    # LOAD in g (15000 g = 15 kg), INDICATION in kg (15 kg), ADDITIONAL_LOAD in mg (5000 mg = 0.005 kg)
    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15000"), unit="g")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("15"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("5000"), unit="mg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0"), unit="kg")
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "PASS"
    assert res["calculation"] is not None
    assert Decimal(res["calculation"]["output"]["Ec"]) == Decimal("0")


def test_18_max_validation_happens_after_normalization(db_session: Session, base_fixture):
    """18. Max validation happens AFTER normalization (25000 g <= 30 kg is accepted, 35000 g > 30 kg is rejected)."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    # 25000 g = 25 kg <= 30 kg Max: must succeed without false overload error
    obs_valid = record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("25000"), unit="g")
    assert obs_valid.value_numeric == Decimal("25000")

    # 35000 g = 35 kg > Max (30 kg) + overload limit: must raise ValueError
    with pytest.raises(ValueError, match="exceeds allowable range limit"):
        record_observation(db_session, attempt.id, "TARGET_LOAD", value_numeric=Decimal("35000"), unit="g")


def test_19_raw_observation_preserves_original_value_and_unit(db_session: Session, base_fixture):
    """19. raw Observation preserves original value/unit without in-place mutation."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    obs = record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15000"), unit="g")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("15000"), unit="g")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("5"), unit="g")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0"), unit="g")
    db_session.commit()

    execute_attempt_calculation(db_session, attempt.id)

    db_session.refresh(obs)
    assert obs.value_numeric == Decimal("15000")
    assert obs.unit == "g"


def test_20_calculation_input_contains_normalized_value_and_unit(db_session: Session, base_fixture):
    """20. Calculation input contains normalized value/unit and normalization trace."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15000"), unit="g")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("15000"), unit="g")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("5"), unit="g")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0"), unit="g")
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    input_snap = res["calculation"]["input_snapshot"]

    assert Decimal(input_snap["load"]) == Decimal("15")
    assert input_snap["unit"] == "kg"
    assert "normalization_trace" in input_snap
    trace = input_snap["normalization_trace"]
    load_trace = next(t for t in trace if t["field"] == "LOAD")
    assert Decimal(load_trace["original_value"]) == Decimal("15000")
    assert load_trace["original_unit"] == "g"
    assert Decimal(load_trace["normalized_value"]) == Decimal("15")
    assert load_trace["normalized_unit"] == "kg"


# ==============================================================================
# PART G: CONFIGURATION FAIL-CLOSED (21 - 22)
# ==============================================================================

def test_21_missing_applicability_critical_fields_fail_closed():
    """21. missing applicability-critical fields fail closed."""
    for missing_field in ["accuracy_class", "max_capacity", "min_capacity", "verification_scale_interval", "actual_scale_interval", "unit", "is_electronic"]:
        snapshot = {
            "accuracy_class": "CLASS_III",
            "max_capacity": "30.000",
            "min_capacity": "0.200",
            "verification_scale_interval": "0.010",
            "actual_scale_interval": "0.010",
            "unit": "kg",
            "is_electronic": True,
            "ranges": [],
        }
        del snapshot[missing_field]
        with pytest.raises(ConfigurationValidationError):
            ApplicabilityEngine.evaluate_plan(snapshot)


def test_22_boolean_strings_cannot_become_true_through_coercion():
    """22. boolean strings such as 'false' cannot become True through coercion."""
    snapshot = {
        "accuracy_class": "CLASS_III",
        "max_capacity": "30.000",
        "min_capacity": "0.200",
        "verification_scale_interval": "0.010",
        "actual_scale_interval": "0.010",
        "unit": "kg",
        "is_electronic": "false",  # String instead of strict bool
        "ranges": [],
    }
    with pytest.raises(ConfigurationValidationError, match="strict boolean"):
        ApplicabilityEngine.evaluate_plan(snapshot)


# ==============================================================================
# PART H: MULTI-RANGE SAFETY (23 - 25)
# ==============================================================================

def test_23_range_index_0_handled_correctly(db_session: Session, base_fixture):
    """23. range_index=0 is handled correctly (not treated as falsy None)."""
    snapshot = {
        "accuracy_class": "CLASS_III",
        "max_capacity": "30.000",
        "min_capacity": "0.200",
        "verification_scale_interval": "0.010",
        "actual_scale_interval": "0.010",
        "unit": "kg",
        "is_electronic": True,
        "is_multiple_range": True,
        "ranges": [
            {
                "range_index": 0,
                "max_capacity": "15.000",
                "min_capacity": "0.200",
                "verification_scale_interval": "0.005",
                "actual_scale_interval": "0.005",
                "unit": "kg",
            },
            {
                "range_index": 1,
                "max_capacity": "30.000",
                "min_capacity": "15.000",
                "verification_scale_interval": "0.010",
                "actual_scale_interval": "0.010",
                "unit": "kg",
            },
        ],
    }
    plan = ApplicabilityEngine.evaluate_plan(snapshot)
    range_0 = next(item for item in plan if item.range_index == 0)
    assert range_0.range_index == 0
    assert range_0.range_reference == "RANGE_0"


def test_24_range_specific_max_e_d_unit_are_used(db_session: Session, base_fixture):
    """24. range-specific Max/e/d/unit are used."""
    ranges = [
        {"range_index": 1, "max_capacity": "15.000", "min_capacity": "0.200", "verification_scale_interval": "0.005", "actual_scale_interval": "0.005", "unit": "kg"},
        {"range_index": 2, "max_capacity": "30.000", "min_capacity": "15.000", "verification_scale_interval": "0.010", "actual_scale_interval": "0.010", "unit": "kg"},
    ]
    env = create_eval_env(db_session, base_fixture, ranges=ranges, is_multiple_range=True)
    tests = env["tests"]
    r1_test = next(t for t in tests if t.range_index == 1)
    attempt = r1_test.attempts[0]

    # Range 1: e = 0.005 kg. Apply load = 2 kg (400 e <= 500 e -> MPE = 0.5 e = 0.0025 kg)
    # (If global e = 0.010 were used, MPE would be 0.5 * 0.010 = 0.0050 kg)
    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("2.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("2.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.0025"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "PASS"
    # Verification interval used must be 0.005 (MPE = 0.0025), not global 0.010 (MPE = 0.0050)
    assert Decimal(res["calculation"]["output"]["mpe_mass"]) == Decimal("0.0025")


def test_25_range_specific_calculation_never_falls_back_to_global_values(db_session: Session, base_fixture):
    """25. range-specific calculation never falls back to global values."""
    ranges = [
        {"range_index": 1, "max_capacity": "10.000", "min_capacity": "0.200", "verification_scale_interval": "0.002", "actual_scale_interval": "0.002", "unit": "kg"},
        {"range_index": 2, "max_capacity": "30.000", "min_capacity": "10.000", "verification_scale_interval": "0.010", "actual_scale_interval": "0.010", "unit": "kg"},
    ]
    env = create_eval_env(db_session, base_fixture, ranges=ranges, is_multiple_range=True)
    tests = env["tests"]
    r1_test = next(t for t in tests if t.range_index == 1)
    attempt = r1_test.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("2.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("2.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.001"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert Decimal(res["calculation"]["input_snapshot"]["verification_scale_interval"]) == Decimal("0.002")


# ==============================================================================
# PART I: REPEATABILITY TESTS (26 - 30)
# ==============================================================================

def test_26_valid_10_weighing_dual_series_passes(db_session: Session, base_fixture):
    """26. valid 10-weighing dual-series case passes."""
    env = create_eval_env(db_session, base_fixture)
    rep_test = next(t for t in env["tests"] if t.test_definition.test_code == "REPEATABILITY")
    attempt = rep_test.attempts[0]

    for i in range(1, 11):
        record_observation(
            db_session, attempt.id, f"REP_50_{i}", unit="kg",
            value_json={"series": "50_PERCENT_MAX", "weighing_index": i, "test_load": "15.000", "loaded_indication": "15.002", "unloaded_indication": "0.002", "unit": "kg"}
        )
    for i in range(1, 11):
        record_observation(
            db_session, attempt.id, f"REP_100_{i}", unit="kg",
            value_json={"series": "100_PERCENT_MAX", "weighing_index": i, "test_load": "30.000", "loaded_indication": "30.003", "unloaded_indication": "0.001", "unit": "kg"}
        )
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "PASS"
    assert res["calculation"] is not None


def test_27_insufficient_weighings_produce_incomplete(db_session: Session, base_fixture):
    """27. insufficient weighings produce INCOMPLETE."""
    env = create_eval_env(db_session, base_fixture)
    rep_test = next(t for t in env["tests"] if t.test_definition.test_code == "REPEATABILITY")
    attempt = rep_test.attempts[0]

    # Only 9 weighings for 50% Max (< 10)
    for i in range(1, 10):
        record_observation(
            db_session, attempt.id, f"REP_50_{i}", unit="kg",
            value_json={"series": "50_PERCENT_MAX", "weighing_index": i, "test_load": "15.000", "loaded_indication": "15.002", "unloaded_indication": "0.002", "unit": "kg"}
        )
    for i in range(1, 11):
        record_observation(
            db_session, attempt.id, f"REP_100_{i}", unit="kg",
            value_json={"series": "100_PERCENT_MAX", "weighing_index": i, "test_load": "30.000", "loaded_indication": "30.003", "unloaded_indication": "0.001", "unit": "kg"}
        )
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert "50_PERCENT_MAX has 9/10" in res["compliance"]["reasoning"]["reason"]


def test_28_duplicate_weighing_indices_rejected(db_session: Session, base_fixture):
    """28. duplicate weighing indices rejected."""
    env = create_eval_env(db_session, base_fixture)
    rep_test = next(t for t in env["tests"] if t.test_definition.test_code == "REPEATABILITY")
    attempt = rep_test.attempts[0]

    record_observation(
        db_session, attempt.id, "REP_50_1", unit="kg",
        value_json={"series": "50_PERCENT_MAX", "weighing_index": 1, "test_load": "15.000", "loaded_indication": "15.002", "unloaded_indication": "0.002", "unit": "kg"}
    )
    with pytest.raises(ValueError, match="Duplicate weighing_index"):
        record_observation(
            db_session, attempt.id, "REP_50_1_DUP", unit="kg",
            value_json={"series": "50_PERCENT_MAX", "weighing_index": 1, "test_load": "15.000", "loaded_indication": "15.002", "unloaded_indication": "0.002", "unit": "kg"}
        )


def test_29_inconsistent_series_load_rejected(db_session: Session, base_fixture):
    """29. inconsistent series load rejected."""
    env = create_eval_env(db_session, base_fixture)
    rep_test = next(t for t in env["tests"] if t.test_definition.test_code == "REPEATABILITY")
    attempt = rep_test.attempts[0]

    for i in range(1, 11):
        load_val = "15.500" if i == 10 else "15.000"
        record_observation(
            db_session, attempt.id, f"REP_50_{i}", unit="kg",
            value_json={"series": "50_PERCENT_MAX", "weighing_index": i, "test_load": load_val, "loaded_indication": "15.002", "unloaded_indication": "0.002", "unit": "kg"}
        )
    for i in range(1, 11):
        record_observation(
            db_session, attempt.id, f"REP_100_{i}", unit="kg",
            value_json={"series": "100_PERCENT_MAX", "weighing_index": i, "test_load": "30.000", "loaded_indication": "30.003", "unloaded_indication": "0.001", "unit": "kg"}
        )
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert "inconsistent test loads" in res["compliance"]["reasoning"]["reason"]


def test_30_50_and_100_percent_loads_must_be_distinct(db_session: Session, base_fixture):
    """30. 50% and 100% loads must be distinct."""
    env = create_eval_env(db_session, base_fixture)
    rep_test = next(t for t in env["tests"] if t.test_definition.test_code == "REPEATABILITY")
    attempt = rep_test.attempts[0]

    # Both series use 15.000 kg
    for i in range(1, 11):
        record_observation(
            db_session, attempt.id, f"REP_50_{i}", unit="kg",
            value_json={"series": "50_PERCENT_MAX", "weighing_index": i, "test_load": "15.000", "loaded_indication": "15.002", "unloaded_indication": "0.002", "unit": "kg"}
        )
    for i in range(1, 11):
        record_observation(
            db_session, attempt.id, f"REP_100_{i}", unit="kg",
            value_json={"series": "100_PERCENT_MAX", "weighing_index": i, "test_load": "15.000", "loaded_indication": "15.002", "unloaded_indication": "0.002", "unit": "kg"}
        )
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert "must have distinct test loads" in res["compliance"]["reasoning"]["reason"]


# ==============================================================================
# PART J: RULEVERSION DETERMINISTIC DISPATCH (31 - 34)
# ==============================================================================

def test_31_and_32_custom_calculation_and_criterion_dispatch(db_session: Session, base_fixture):
    """31. custom calculation dispatch executes AND 32. custom criterion dispatch executes."""
    calc_invoked = []
    crit_invoked = []

    # Register custom calculation in trusted Python registry
    @CalculationEngine.register("CUSTOM_CALC_REGRESSION")
    def custom_calc(inputs: dict) -> CalculationOutput:
        calc_invoked.append(True)
        return CalculationOutput(
            calculation_code="CUSTOM_CALC_REGRESSION",
            formula_reference="CUSTOM_FORMULA_R76",
            input_snapshot=inputs,
            output={"custom_val": "42.0", "Ec": "0.0"},
        )

    # Register custom criterion in trusted Python registry
    @ComplianceEngine.register_criterion("CUSTOM_CRITERION_REGRESSION")
    def custom_crit(output_data: dict, config: dict) -> ComplianceEvaluation:
        crit_invoked.append(True)
        return ComplianceEvaluation(
            decision=ComplianceDecision.PASS,
            criterion_value="CUSTOM_THRESHOLD <= 50",
            measured_value=str(output_data.get("custom_val")),
            margin="8.0",
            rule_reference="CUSTOM_R76_SPEC",
            calculation_code="CUSTOM_CALC_REGRESSION",
            reasoning_json={"custom_pass": True},
        )

    # Create RuleVersion pointing explicitly to custom calculation and custom criterion
    rule = base_fixture["rule"]
    custom_rv = RuleVersion(
        rule_id=rule.id,
        version_number=f"2006-custom-{uuid.uuid4().hex[:4]}",
        standard_version="OIML R 76-1: 2006 (E)",
        clause="A.4",
        calculation_identifier="CUSTOM_CALC_REGRESSION",
        applicability_identifier="R76_APPLICABILITY_V1",
        aggregation_strategy="ALL_POINTS_PASS",
        definition_json={
            "tests": {
                "WEIGHING_PERFORMANCE": {
                    "clause": "A.4.4.3",
                    "calculation_identifier": "CUSTOM_CALC_REGRESSION",
                    "criterion": {"type": "CUSTOM_CRITERION_REGRESSION"},
                }
            }
        },
        content_hash="custom_hash_123",
        is_active=True,
    )
    db_session.add(custom_rv)
    db_session.flush()

    env = create_eval_env(db_session, {"rule": rule, "rule_version": custom_rv})
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("15.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)

    # Prove BOTH custom calculation and custom criterion executed
    assert len(calc_invoked) == 1, "Custom calculation was not executed"
    assert len(crit_invoked) == 1, "Custom criterion was not executed"
    assert res["compliance"]["decision"] == "PASS"
    assert res["compliance"]["measured_value"] == "42.0"
    assert res["compliance"]["criterion_value"] == "CUSTOM_THRESHOLD <= 50"


def test_33_missing_rule_version_fails_closed(db_session: Session, base_fixture):
    """33. missing RuleVersion fails closed."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    # Assign non-existent rule_version_id
    test_obj.rule_version_id = uuid.uuid4()
    env["evaluation"].rule_version_id = uuid.uuid4()
    db_session.flush()

    with pytest.raises(ValueError, match="cannot be resolved in database"):
        execute_attempt_calculation(db_session, attempt.id)


def test_34_malformed_rule_definition_fails_closed(db_session: Session, base_fixture):
    """34. malformed rule definition fails closed."""
    rule = base_fixture["rule"]
    malformed_rv = RuleVersion(
        rule_id=rule.id,
        version_number=f"2006-malformed-{uuid.uuid4().hex[:4]}",
        standard_version="OIML R 76-1: 2006 (E)",
        clause="A.4",
        calculation_identifier="R76_A4_4_3_ERROR",
        applicability_identifier="R76_APPLICABILITY_V1",
        aggregation_strategy="ALL_POINTS_PASS",
        definition_json={"broken": "missing tests definition"},
        content_hash="malformed_hash",
        is_active=True,
    )
    db_session.add(malformed_rv)
    db_session.flush()

    env = create_eval_env(db_session, {"rule": rule, "rule_version": malformed_rv})
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15.000"), unit="kg")
    db_session.commit()

    with pytest.raises(ValueError, match="missing configuration for test"):
        execute_attempt_calculation(db_session, attempt.id)


# ==============================================================================
# PART K: OBSERVATION IMMUTABILITY & RETEST (35 - 37)
# ==============================================================================

def test_35_observations_cannot_be_modified_after_calculation(db_session: Session, base_fixture):
    """35. observations cannot be modified after calculation."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("15.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")
    db_session.commit()

    execute_attempt_calculation(db_session, attempt.id)

    # Attempting to add or modify observations on this attempt MUST raise ObservationLockedError
    with pytest.raises(ObservationLockedError, match="locked because calculations or compliance results already exist"):
        record_observation(db_session, attempt.id, "LOAD_2", value_numeric=Decimal("20.000"), unit="kg")


def test_36_and_37_retest_creates_attempt_2_and_preserves_attempt_1(db_session: Session, base_fixture):
    """36. retest creates Attempt 2 AND 37. Attempt 1 remains preserved."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt1 = test_obj.attempts[0]

    # Attempt 1: Fails or completes
    obs1 = record_observation(db_session, attempt1.id, "LOAD", value_numeric=Decimal("15.000"), unit="kg")
    record_observation(db_session, attempt1.id, "INDICATION", value_numeric=Decimal("15.000"), unit="kg")
    record_observation(db_session, attempt1.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt1.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")
    db_session.commit()

    res1 = execute_attempt_calculation(db_session, attempt1.id)
    attempt1_calc_id = res1["calculation"]["id"]

    # Create Retest (Attempt 2)
    attempt2 = create_retest_attempt(
        db=db_session,
        test_id=test_obj.id,
        notes="Retest after recalibration",
    )

    # 36. Verify Attempt 2 properties
    assert attempt2.attempt_number == 2
    assert attempt2.supersedes_attempt_id == attempt1.id
    assert attempt2.status == TestAttemptStatus.ACTIVE

    # 37. Verify Attempt 1 remains preserved
    db_session.refresh(attempt1)
    assert attempt1.status == TestAttemptStatus.SUPERSEDED
    assert len(attempt1.calculations) == 1
    assert str(attempt1.calculations[0].id) == attempt1_calc_id
    assert len(attempt1.observations) == 4


# ==============================================================================
# PART L: TRACEABILITY REGRESSION TESTS (38 - 39)
# ==============================================================================

def test_38_complete_trace_chain_returned(db_session: Session, base_fixture):
    """38. complete trace chain is returned from ComplianceResult to Instrument."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("15.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    comp_id = uuid.UUID(res["compliance"]["id"])

    # Trace backward through SQLAlchemy relationships
    comp = db_session.get(ComplianceResult, comp_id)
    assert comp is not None

    # ComplianceResult -> Calculation
    calc = comp.calculation
    assert calc is not None
    assert calc.calculation_code == "R76_A4_4_3_ERROR"

    # Calculation -> TestAttempt
    att = calc.test_attempt
    assert att.id == attempt.id

    # TestAttempt -> Observations
    raw_obs = att.observations
    assert len(raw_obs) == 4

    # TestAttempt -> EvaluationTest
    e_test = att.evaluation_test
    assert e_test.id == test_obj.id

    # EvaluationTest -> Evaluation
    ev = e_test.evaluation
    assert ev.id == env["evaluation"].id

    # Evaluation -> InstrumentConfiguration & Instrument
    conf = ev.instrument_configuration
    assert conf.id == env["configuration"].id
    inst = ev.instrument
    assert inst.id == env["instrument"].id
    assert ev.configuration_snapshot is not None


def test_39_original_observation_and_normalized_input_both_visible(db_session: Session, base_fixture):
    """39. original observation unit/value and normalized calculation input are both visible."""
    env = create_eval_env(db_session, base_fixture)
    test_obj = next(t for t in env["tests"] if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = test_obj.attempts[0]

    obs = record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("15000"), unit="g")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("15000"), unit="g")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("5"), unit="g")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0"), unit="g")
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)
    calc_id = uuid.UUID(res["calculation"]["id"])

    # Verify raw observation has original laboratory evidence
    db_session.refresh(obs)
    assert obs.value_numeric == Decimal("15000")
    assert obs.unit == "g"

    # Verify calculation has normalized values and explicit trace record
    calc = db_session.get(Calculation, calc_id)
    input_snap = calc.input_snapshot_json
    assert input_snap["load"] == "15"
    assert input_snap["unit"] == "kg"
    assert "normalization_trace" in input_snap
    trace = input_snap["normalization_trace"]
    load_trace = next(t for t in trace if t["field"] == "LOAD")
    assert load_trace["original_value"] == "15000"
    assert load_trace["original_unit"] == "g"
    assert load_trace["normalized_value"] == "15"
    assert load_trace["normalized_unit"] == "kg"
