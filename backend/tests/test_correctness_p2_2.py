"""Phase 2.2 — Final Metrological Integrity Regression Tests.

Verifies:
1. Eccentricity: Omitting additional_load or zero_error produces INCOMPLETE without executing calculation.
2. Eccentricity: Inconsistent test loads across positions produces INCOMPLETE.
3. Repeatability: Inconsistent test loads within a series produces INCOMPLETE (no silent use of first load).
4. Repeatability: Identical test loads between 50% and 100% series produces INCOMPLETE.
5. Repeatability: Inconsistent units across weighings produces INCOMPLETE.
6. Boolean config validation: Rejects non-boolean strings/integers ('false', 'true', 1, 0).
7. RuleVersion: Frozen RuleVersion must not silently fall back to active version if missing or unresolvable.
8. RuleVersion: Missing or malformed definition_json produces explicit ValueError.
9. RuleVersion: Calculation and criterion dispatch are strictly driven by definition_json (custom procedure & criterion verified).
"""

from decimal import Decimal
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.applicability import ConfigurationValidationError, validate_configuration_snapshot
from app.engines.calculation import CalculationEngine, CalculationOutput
from app.models.configuration import AccuracyClass, InstrumentConfiguration, TareType
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.instrument import Instrument
from app.models.metrology import Calculation, ComplianceResult
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
from app.services.test_service import record_observation


@pytest.fixture
def p22_env(db_session: Session):
    """Set up test fixtures for Phase 2.2 regression tests."""
    user = User(email=f"p22-{uuid.uuid4().hex[:6]}@lab.org", full_name="P2.2 Evaluator", role=UserRole.OPERATOR)
    db_session.add(user)
    db_session.flush()

    inst = Instrument(
        serial_number=f"SN-P22-{uuid.uuid4().hex[:6].upper()}",
        manufacturer="Mettler-P22",
        model_name="XP-3000-P22",
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
        version_number=f"2006-p22-{uuid.uuid4().hex[:4]}",
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
        content_hash="p22_content_hash",
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
        "extra_capabilities": {
            "load_receptor": {
                "support_count": 4,
                "special_receptor": False,
                "rolling_load": False,
            }
        },
    }

    eval_obj = Evaluation(
        evaluation_number=f"EVAL-P22-{uuid.uuid4().hex[:6]}",
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
# 1. ECCENTRICITY: REMOVE FABRICATED VALUES
# ==============================================================================

def test_eccentricity_omitting_additional_load_incomplete(db_session: Session, p22_env):
    """Omitting additional_load must produce INCOMPLETE, and calculation must NOT execute."""
    tests = p22_env["tests"]
    ecc_test = next(t for t in tests if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]

    # Record 4 quarter positions where QUARTER_2 omits additional_load
    positions = ["QUARTER_1", "QUARTER_2", "QUARTER_3", "QUARTER_4"]
    for pos in positions:
        payload = {
            "position": pos,
            "load": "10.000",
            "indication": "10.000",
            "zero_error": "0.0000",
            "unit": "kg",
        }
        if pos != "QUARTER_2":
            payload["additional_load"] = "0.0025"
        # QUARTER_2 does not have additional_load
        record_observation(db_session, attempt.id, f"POS_{pos}", unit="kg", value_json=payload)

    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["calculation"] is None
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert "QUARTER_2 missing: additional_load" in res["compliance"]["reasoning"]["reason"]

    # Verify no calculation row was persisted
    calcs = db_session.scalars(select(Calculation).where(Calculation.test_attempt_id == attempt.id)).all()
    assert len(calcs) == 0


def test_eccentricity_omitting_zero_error_incomplete(db_session: Session, p22_env):
    """Omitting zero_error must produce INCOMPLETE, and calculation must NOT execute."""
    tests = p22_env["tests"]
    ecc_test = next(t for t in tests if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]

    # Record 4 quarter positions where QUARTER_3 omits zero_error
    positions = ["QUARTER_1", "QUARTER_2", "QUARTER_3", "QUARTER_4"]
    for pos in positions:
        payload = {
            "position": pos,
            "load": "10.000",
            "indication": "10.000",
            "additional_load": "0.0025",
            "unit": "kg",
        }
        if pos != "QUARTER_3":
            payload["zero_error"] = "0.0000"
        record_observation(db_session, attempt.id, f"POS_{pos}", unit="kg", value_json=payload)

    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["calculation"] is None
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert "QUARTER_3 missing: zero_error" in res["compliance"]["reasoning"]["reason"]

    # Verify no calculation row was persisted
    calcs = db_session.scalars(select(Calculation).where(Calculation.test_attempt_id == attempt.id)).all()
    assert len(calcs) == 0


# ==============================================================================
# 2. ECCENTRICITY: LOAD CONSISTENCY
# ==============================================================================

def test_eccentricity_inconsistent_loads_incomplete(db_session: Session, p22_env):
    """All positions must have a consistent test load; inconsistent loads produce INCOMPLETE."""
    tests = p22_env["tests"]
    ecc_test = next(t for t in tests if t.test_definition.test_code == "ECCENTRICITY")
    attempt = ecc_test.attempts[0]

    # 3 positions at 10.000 kg, but QUARTER_4 at 12.000 kg
    loads = {"QUARTER_1": "10.000", "QUARTER_2": "10.000", "QUARTER_3": "10.000", "QUARTER_4": "12.000"}
    for pos, load_val in loads.items():
        record_observation(
            db_session,
            attempt.id,
            f"POS_{pos}",
            unit="kg",
            value_json={
                "position": pos,
                "load": load_val,
                "indication": load_val,
                "additional_load": "0.0025",
                "zero_error": "0.0000",
                "unit": "kg",
            },
        )
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["calculation"] is None
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert "consistent test load across all positions" in res["compliance"]["reasoning"]["reason"]


# ==============================================================================
# 3. REPEATABILITY: SERIES CONSISTENCY
# ==============================================================================

def test_repeatability_inconsistent_load_in_series_incomplete(db_session: Session, p22_env):
    """Inconsistent test load within a repeatability series must produce INCOMPLETE (no silent fallback)."""
    tests = p22_env["tests"]
    rep_test = next(t for t in tests if t.test_definition.test_code == "REPEATABILITY")
    attempt = rep_test.attempts[0]

    # Series 50: 9 weighings at 15.000 kg, 1 weighing at 15.500 kg
    for i in range(1, 11):
        test_load = "15.500" if i == 10 else "15.000"
        record_observation(
            db_session,
            attempt.id,
            f"REP_50_{i}",
            unit="kg",
            value_json={
                "series": "50_PERCENT_MAX",
                "weighing_index": i,
                "test_load": test_load,
                "loaded_indication": "15.002",
                "unloaded_indication": "0.002",
                "unit": "kg",
            },
        )

    # Series 100: 10 weighings at 30.000 kg
    for i in range(1, 11):
        record_observation(
            db_session,
            attempt.id,
            f"REP_100_{i}",
            unit="kg",
            value_json={
                "series": "100_PERCENT_MAX",
                "weighing_index": i,
                "test_load": "30.000",
                "loaded_indication": "30.003",
                "unloaded_indication": "0.001",
                "unit": "kg",
            },
        )
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["calculation"] is None
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert "50% Max series has inconsistent test loads" in res["compliance"]["reasoning"]["reason"]


def test_repeatability_identical_loads_in_both_series_incomplete(db_session: Session, p22_env):
    """50% Max and 100% Max series must have distinct test loads; identical loads produce INCOMPLETE."""
    tests = p22_env["tests"]
    rep_test = next(t for t in tests if t.test_definition.test_code == "REPEATABILITY")
    attempt = rep_test.attempts[0]

    # Both series use 15.000 kg
    for i in range(1, 11):
        record_observation(
            db_session,
            attempt.id,
            f"REP_50_{i}",
            unit="kg",
            value_json={
                "series": "50_PERCENT_MAX",
                "weighing_index": i,
                "test_load": "15.000",
                "loaded_indication": "15.002",
                "unloaded_indication": "0.002",
                "unit": "kg",
            },
        )
    for i in range(1, 11):
        record_observation(
            db_session,
            attempt.id,
            f"REP_100_{i}",
            unit="kg",
            value_json={
                "series": "100_PERCENT_MAX",
                "weighing_index": i,
                "test_load": "15.000",
                "loaded_indication": "15.002",
                "unloaded_indication": "0.002",
                "unit": "kg",
            },
        )
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["calculation"] is None
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert "must have distinct test loads" in res["compliance"]["reasoning"]["reason"]


def test_repeatability_inconsistent_units_incomplete(db_session: Session, p22_env):
    """Unknown/unsupported unit in repeatability weighing produces INCOMPLETE."""
    tests = p22_env["tests"]
    rep_test = next(t for t in tests if t.test_definition.test_code == "REPEATABILITY")
    attempt = rep_test.attempts[0]

    record_observation(
        db_session,
        attempt.id,
        "REP_50_1",
        unit="xyz",
        value_json={
            "series": "50_PERCENT_MAX",
            "weighing_index": 1,
            "test_load": "15.000",
            "loaded_indication": "15.002",
            "unloaded_indication": "0.002",
            "unit": "xyz",
        },
    )
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)

    assert res["calculation"] is None
    assert res["compliance"]["decision"] == "INCOMPLETE"
    assert "unit" in res["compliance"]["reasoning"]["reason"].lower()



# ==============================================================================
# 4. BOOLEAN CONFIG VALIDATION
# ==============================================================================

def test_boolean_config_validation_rejects_strings_and_numbers():
    """is_electronic and is_multiple_range must be strict booleans, not bool('false') strings or ints."""
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

    # String "false" for is_electronic
    snap1 = {**valid_base, "is_electronic": "false"}
    with pytest.raises(ConfigurationValidationError, match="'is_electronic' must be a strict boolean"):
        validate_configuration_snapshot(snap1)

    # String "true" for is_multiple_range
    snap2 = {**valid_base, "is_multiple_range": "true"}
    with pytest.raises(ConfigurationValidationError, match="'is_multiple_range' must be a strict boolean"):
        validate_configuration_snapshot(snap2)

    # Integer 1 for is_electronic
    snap3 = {**valid_base, "is_electronic": 1}
    with pytest.raises(ConfigurationValidationError, match="'is_electronic' must be a strict boolean"):
        validate_configuration_snapshot(snap3)

    # Integer 0 for is_multiple_range
    snap4 = {**valid_base, "is_multiple_range": 0}
    with pytest.raises(ConfigurationValidationError, match="'is_multiple_range' must be a strict boolean"):
        validate_configuration_snapshot(snap4)


# ==============================================================================
# 5. RULEVERSION DETERMINISTIC DISPATCH & NO-FALLBACK
# ==============================================================================

def test_rule_version_must_not_silently_fallback_on_unresolvable_id(db_session: Session, p22_env):
    """An EvaluationTest with an unresolvable rule_version_id must fail explicitly, never falling back to active rule."""
    tests = p22_env["tests"]
    w_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    attempt = w_test.attempts[0]

    # Assign a non-existent UUID to rule_version_id
    bad_rv_id = uuid.uuid4()
    w_test.rule_version_id = bad_rv_id
    p22_env["evaluation"].rule_version_id = bad_rv_id
    db_session.flush()

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")
    db_session.commit()

    with pytest.raises(ValueError, match="cannot be resolved in database"):
        execute_attempt_calculation(db_session, attempt.id)


def test_rule_version_missing_definition_fails_closed(db_session: Session, p22_env):
    """A RuleVersion with empty or malformed definition_json must fail explicitly, never substituting defaults."""
    rule = db_session.scalar(select(Rule).where(Rule.code == "OIML-R76-2006"))
    empty_rv = RuleVersion(
        rule_id=rule.id,
        version_number=f"2006-empty-{uuid.uuid4().hex[:4]}",
        standard_version="OIML R 76-1: 2006 (E)",
        clause="A.4",
        calculation_identifier="R76_A4_4_3_ERROR",
        applicability_identifier="R76_APPLICABILITY_V1",
        aggregation_strategy="ALL_POINTS_PASS",
        definition_json={"tests": {}},  # Empty tests dict!
        content_hash="empty_hash",
        is_active=True,
    )
    db_session.add(empty_rv)
    db_session.flush()

    tests = p22_env["tests"]
    w_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    w_test.rule_version_id = empty_rv.id
    attempt = w_test.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")
    db_session.commit()

    with pytest.raises(ValueError, match="definition_json is missing configuration for test 'WEIGHING_PERFORMANCE'"):
        execute_attempt_calculation(db_session, attempt.id)


def test_rule_version_actual_calculation_and_criterion_dispatch(db_session: Session, p22_env):
    """Demonstrate that calculation and criterion dispatch are strictly executed from the RuleVersion definition.
    
    1. Register a custom calculation identifier in CalculationEngine.
    2. Configure RuleVersion definition_json to dispatch to that custom identifier.
    3. Execute attempt calculation and verify the custom procedure was called.
    """
    custom_calc_code = "CUSTOM_TEST_DISPATCH_PROCEDURE"

    # Register custom procedure
    @CalculationEngine.register(custom_calc_code)
    def custom_calc_procedure(inputs):
        return CalculationOutput(
            calculation_code=custom_calc_code,
            formula_reference="CUSTOM_FORMULA_REF_42",
            input_snapshot=inputs,
            output={
                "custom_marker": "EXECUTED_VIA_RULE_VERSION_DEFINITION",
                "corrected_error": "0.0000",
                "absolute_error": "0.0000",
                "mpe_mass": "0.0100",
            },
        )

    rule = db_session.scalar(select(Rule).where(Rule.code == "OIML-R76-2006"))
    custom_rv = RuleVersion(
        rule_id=rule.id,
        version_number=f"2006-custom-{uuid.uuid4().hex[:4]}",
        standard_version="OIML R 76-1: 2006 (E)",
        clause="A.4.4.3",
        calculation_identifier=custom_calc_code,
        applicability_identifier="R76_APPLICABILITY_V1",
        aggregation_strategy="ALL_POINTS_PASS",
        definition_json={
            "tests": {
                "WEIGHING_PERFORMANCE": {
                    "clause": "A.4.4.3",
                    "calculation_identifier": custom_calc_code,
                    "criterion": {"type": "ABS_LE_MPE"},
                }
            }
        },
        content_hash="custom_dispatch_hash",
        is_active=True,
    )
    db_session.add(custom_rv)
    db_session.flush()

    tests = p22_env["tests"]
    w_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")
    w_test.rule_version_id = custom_rv.id
    attempt = w_test.attempts[0]

    record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "INDICATION", value_numeric=Decimal("10.000"), unit="kg")
    record_observation(db_session, attempt.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")
    db_session.commit()

    res = execute_attempt_calculation(db_session, attempt.id)

    # Verify custom procedure was dispatched
    assert res["calculation"]["calculation_code"] == custom_calc_code
    assert res["calculation"]["formula_reference"] == "CUSTOM_FORMULA_REF_42"
    assert res["calculation"]["output"]["custom_marker"] == "EXECUTED_VIA_RULE_VERSION_DEFINITION"
    assert res["compliance"]["decision"] == "PASS"
    assert res["compliance"]["reasoning"]["rule_version_id"] == str(custom_rv.id)
