"""Tests verifying Retest audit preservation and Snapshot/RuleVersion immutability.

Verifies:
- Attempt 1 FAIL is permanently preserved when Attempt 2 PASS is created.
- Live configuration changes do not mutate existing evaluation snapshots.
- Test plan generation is strictly driven by the frozen snapshot.
"""

from decimal import Decimal
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.applicability import ApplicabilityEngine
from app.models.configuration import AccuracyClass, InstrumentConfiguration
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.instrument import Instrument
from app.models.metrology import ComplianceDecision, ComplianceResult
from app.models.rule import Rule, RuleVersion
from app.models.test_definition import ImplementationStatus, ScopeType, TestDefinition
from app.models.test_execution import EvaluationTest, TestAttempt, TestAttemptStatus
from app.models.user import User, UserRole
from app.services.calculation_service import execute_attempt_calculation
from app.services.plan_service import generate_evaluation_plan
from app.services.test_service import create_retest_attempt, record_observation


def test_retest_preserves_attempt_1_history(db_session: Session):
    """Attempt 1 FAIL must remain immutable and un-overwritten when Attempt 2 PASS is created."""
    # 1. Setup User and Instrument
    user = User(email="eval@test.com", full_name="Test Evaluator", role=UserRole.LAB_ADMIN)
    db_session.add(user)
    db_session.flush()

    inst = Instrument(serial_number="IMMUTABLE-001", manufacturer="Metrology Lab", model_name="ML-30", is_synthetic=True)
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
        is_electronic=True,
        has_zero_setting=True,
        tare_type="SUBTRACTIVE",
        is_multiple_range=False,
    )
    db_session.add(config)
    db_session.flush()

    rule = Rule(code="OIML_R76_2006", name="OIML R 76-1:2006", description="OIML standard")
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

    # 2. Create Evaluation and Plan
    eval_obj = Evaluation(
        evaluation_number="EVAL-RETEST-001",
        instrument_id=inst.id,
        instrument_configuration_id=config.id,
        rule_version_id=rv.id,
        operator_id=user.id,
        status=EvaluationStatus.IN_PROGRESS,
        configuration_snapshot={
            "accuracy_class": "CLASS_III",
            "max_capacity": "30.000",
            "min_capacity": "0.200",
            "verification_scale_interval": "0.010",
            "actual_scale_interval": "0.010",
            "unit": "kg",
            "is_electronic": True,
            "has_zero_setting": True,
            "tare_type": "SUBTRACTIVE",
            "is_multiple_range": False,
        },
    )
    db_session.add(eval_obj)
    db_session.flush()

    tests = generate_evaluation_plan(db_session, eval_obj.id)
    weighing_test = next(t for t in tests if t.test_definition.test_code == "WEIGHING_PERFORMANCE")

    # 3. Attempt 1 is active
    attempt1 = db_session.scalar(
        select(TestAttempt).where(TestAttempt.evaluation_test_id == weighing_test.id, TestAttempt.attempt_number == 1)
    )
    assert attempt1 is not None

    # Step 1: Zero error observation
    # Record raw failing observations:
    # Load = 10.00 kg, Indication = 10.03 kg -> Error = 0.030 kg > MPE (0.010 kg)
    record_observation(db_session, attempt1.id, "LOAD", value_numeric=Decimal("10.00"), unit="kg")
    record_observation(db_session, attempt1.id, "INDICATION", value_numeric=Decimal("10.03"), unit="kg")
    record_observation(db_session, attempt1.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt1.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")

    calc_res1 = execute_attempt_calculation(db_session, attempt1.id)
    db_session.commit()

    assert calc_res1["compliance"]["decision"] == "FAIL"
    assert "-0.020" in calc_res1["compliance"]["margin"]

    # 5. Create Retest (Attempt 2)
    attempt2 = create_retest_attempt(db_session, weighing_test.id, notes="Scale adjusted and recalibrated")
    assert attempt2.attempt_number == 2
    assert attempt2.supersedes_attempt_id == attempt1.id

    # Record passing observations for Attempt 2:
    # Load = 10.00 kg, Indication = 10.00 kg -> Error = 0.000 kg <= MPE (0.010 kg)
    record_observation(db_session, attempt2.id, "LOAD", value_numeric=Decimal("10.00"), unit="kg")
    record_observation(db_session, attempt2.id, "INDICATION", value_numeric=Decimal("10.00"), unit="kg")
    record_observation(db_session, attempt2.id, "ADDITIONAL_LOAD", value_numeric=Decimal("0.005"), unit="kg")
    record_observation(db_session, attempt2.id, "ZERO_ERROR", value_numeric=Decimal("0.000"), unit="kg")

    calc_res2 = execute_attempt_calculation(db_session, attempt2.id)
    db_session.commit()

    assert calc_res2["compliance"]["decision"] == "PASS"
    assert "+0.010" in calc_res2["compliance"]["margin"]

    # 6. CRITICAL VERIFICATION: Prove Attempt 1 was NOT mutated or overwritten!
    db_session.refresh(attempt1)
    attempt1_comp = db_session.scalar(
        select(ComplianceResult).where(ComplianceResult.test_attempt_id == attempt1.id)
    )
    assert attempt1_comp is not None
    assert attempt1_comp.decision == ComplianceDecision.FAIL
    assert "-0.020" in attempt1_comp.margin

    # Both attempts exist and are linked
    all_attempts = db_session.scalars(
        select(TestAttempt).where(TestAttempt.evaluation_test_id == weighing_test.id).order_by(TestAttempt.attempt_number)
    ).all()
    assert len(all_attempts) == 2
    assert all_attempts[0].attempt_number == 1
    assert all_attempts[1].attempt_number == 2
    assert all_attempts[1].supersedes_attempt_id == all_attempts[0].id


def test_configuration_snapshot_immutability(db_session: Session):
    """Modifying live instrument configuration must not alter historical evaluation snapshots."""
    user = User(email="adm@test.com", full_name="Admin User", role=UserRole.LAB_ADMIN)
    db_session.add(user)
    db_session.flush()

    inst = Instrument(serial_number="SNAPSHOT-001", manufacturer="Test MFR", model_name="M-1", is_synthetic=True)
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
        is_electronic=True,
        has_zero_setting=True,
        tare_type="SUBTRACTIVE",
        is_multiple_range=False,
    )
    db_session.add(config)
    db_session.flush()

    rule = Rule(code="R76_TEST", name="R76", description="R76 rule")
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

    # Create Evaluation 1 with snapshot of 30 kg single range
    snapshot_data = {
        "accuracy_class": "CLASS_III",
        "max_capacity": "30.000",
        "min_capacity": "0.200",
        "verification_scale_interval": "0.010",
        "actual_scale_interval": "0.010",
        "unit": "kg",
        "is_electronic": True,
        "tare_type": "SUBTRACTIVE",
        "is_multiple_range": False,
    }
    eval1 = Evaluation(
        evaluation_number="EVAL-SNAPSHOT-001",
        instrument_id=inst.id,
        instrument_configuration_id=config.id,
        rule_version_id=rv.id,
        operator_id=user.id,
        status=EvaluationStatus.IN_PROGRESS,
        configuration_snapshot=snapshot_data,
    )
    db_session.add(eval1)
    db_session.commit()

    # Generate plan for Evaluation 1
    tests_eval1 = generate_evaluation_plan(db_session, eval1.id)
    eval1_codes = [t.test_definition.test_code for t in tests_eval1]
    assert "WEIGHING_PERFORMANCE" in eval1_codes

    # Now mutate the LIVE configuration to multiple-range 150 kg
    config.max_capacity = Decimal("150.000")
    config.is_multiple_range = True
    db_session.commit()

    # Evaluation 1 snapshot MUST remain unchanged
    db_session.refresh(eval1)
    assert eval1.configuration_snapshot["max_capacity"] == "30.000"
    assert eval1.configuration_snapshot["is_multiple_range"] is False

    # Calling generate_evaluation_plan again on Evaluation 1 returns the original plan
    tests_recalled = generate_evaluation_plan(db_session, eval1.id)
    assert len(tests_recalled) == len(tests_eval1)
    recalled_codes = [t.test_definition.test_code for t in tests_recalled]
    assert "WEIGHING_PERFORMANCE" in recalled_codes
    assert "WEIGHING_PERFORMANCE_RANGE_1" not in recalled_codes
