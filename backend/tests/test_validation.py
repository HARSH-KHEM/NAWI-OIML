"""Tests for metrological domain and schema validation.

Verifies:
- min_capacity > max_capacity is rejected
- actual_scale_interval (d) > verification_scale_interval (e) is rejected
- e <= 0 is rejected
- Load exceeding Max + overload limit is rejected
- Negative or zero load is rejected
"""

from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.models.configuration import AccuracyClass
from app.models.instrument import Instrument
from app.models.rule import Rule, RuleVersion
from app.models.test_execution import EvaluationTest, TestAttempt
from app.models.user import User, UserRole
from app.schemas.configuration import InstrumentConfigurationCreate
from app.services.plan_service import generate_evaluation_plan
from app.services.test_service import record_observation


def test_validation_min_capacity_exceeds_max():
    """Min capacity exceeding Max capacity must raise a validation error."""
    with pytest.raises(ValidationError) as exc_info:
        InstrumentConfigurationCreate(
            accuracy_class=AccuracyClass.CLASS_III,
            max_capacity=Decimal("30.00"),
            min_capacity=Decimal("35.00"),  # Invalid: Min > Max
            verification_scale_interval=Decimal("0.01"),
            actual_scale_interval=Decimal("0.01"),
            unit="kg",
        )
    assert "cannot exceed max_capacity" in str(exc_info.value)


def test_validation_scale_interval_d_exceeds_e():
    """Actual scale interval (d) exceeding verification scale interval (e) is invalid."""
    with pytest.raises(ValidationError) as exc_info:
        InstrumentConfigurationCreate(
            accuracy_class=AccuracyClass.CLASS_III,
            max_capacity=Decimal("30.00"),
            min_capacity=Decimal("0.20"),
            verification_scale_interval=Decimal("0.01"),
            actual_scale_interval=Decimal("0.02"),  # Invalid: d > e
            unit="kg",
        )
    assert "cannot exceed verification_scale_interval" in str(exc_info.value)


def test_validation_non_positive_intervals():
    """Verification scale interval e <= 0 must fail validation."""
    with pytest.raises(ValidationError):
        InstrumentConfigurationCreate(
            accuracy_class=AccuracyClass.CLASS_III,
            max_capacity=Decimal("30.00"),
            min_capacity=Decimal("0.20"),
            verification_scale_interval=Decimal("-0.01"),  # Invalid: <= 0
            actual_scale_interval=Decimal("0.01"),
            unit="kg",
        )


def test_validation_load_exceeds_max(db_session):
    """Submitting an observation load that grossly exceeds Max is rejected by domain validation."""
    from app.models.evaluation import Evaluation, EvaluationStatus
    from app.models.configuration import InstrumentConfiguration

    user = User(email="val@test.com", full_name="Validator User", role=UserRole.LAB_ADMIN)
    db_session.add(user)
    db_session.flush()

    inst = Instrument(serial_number="LOAD-VAL-001", manufacturer="Test MFR", model_name="M-1", is_synthetic=True)
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
    )
    db_session.add(config)
    db_session.flush()

    rule = Rule(code="R76_VAL", name="R76", description="R76 validation")
    db_session.add(rule)
    db_session.flush()

    rv = RuleVersion(
        rule_id=rule.id,
        version_number="2006-01",
        standard_version="OIML R 76-1: 2006 (E)",
        clause="A.4.4",
        calculation_identifier="R76_A4_4_3_ERROR",
        applicability_identifier="R76_APPLICABILITY_V1",
        aggregation_strategy="ALL_POINTS_PASS",
        is_active=True,
    )
    db_session.add(rv)
    db_session.flush()

    eval_obj = Evaluation(
        evaluation_number="EVAL-VAL-001",
        instrument_id=inst.id,
        instrument_configuration_id=config.id,
        rule_version_id=rv.id,
        operator_id=user.id,
        status=EvaluationStatus.IN_PROGRESS,
        configuration_snapshot={
            "accuracy_class": config.accuracy_class.value,
            "max_capacity": str(config.max_capacity),
            "min_capacity": str(config.min_capacity),
            "verification_scale_interval": str(config.verification_scale_interval),
            "actual_scale_interval": str(config.actual_scale_interval),
            "unit": config.unit,
            "is_electronic": True,
            "is_multiple_range": False,
        },
    )
    db_session.add(eval_obj)
    db_session.flush()

    tests = generate_evaluation_plan(db_session, eval_obj.id)
    weighing_test = tests[0]
    attempt = weighing_test.attempts[0]

    # Max is 30 kg, allowable overload limit is 30 + 9*0.010 = 30.09 kg
    # Submitting 45 kg must fail
    with pytest.raises(ValueError) as exc_info:
        record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("45.00"), unit="kg")
    assert "exceeds allowable range limit" in str(exc_info.value)

    # Submitting negative or zero load must fail
    with pytest.raises(ValueError) as exc_info:
        record_observation(db_session, attempt.id, "LOAD", value_numeric=Decimal("-5.00"), unit="kg")
    assert "must be strictly positive" in str(exc_info.value)
