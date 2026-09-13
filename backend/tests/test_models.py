"""Tests for domain models, Decimal precision, and entity relationships."""

from decimal import Decimal
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base
from app.models.configuration import AccuracyClass, InstrumentConfiguration, TareType
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.instrument import Instrument, InstrumentStatus
from app.models.rule import Rule, RuleVersion
from app.models.user import User, UserRole
from scripts.seed import seed_synthetic_data


def test_models_importable():
    """Requirement 15: Verify all models can be imported and are registered in Base.metadata."""
    table_names = Base.metadata.tables.keys()
    assert "users" in table_names
    assert "instruments" in table_names
    assert "instrument_configurations" in table_names
    assert "rules" in table_names
    assert "rule_versions" in table_names
    assert "evaluations" in table_names


def test_user_creation_and_uuid(db_session: Session):
    """Verify User model creation with UUID primary key and role enum."""
    user = User(
        email="auditor@metrology.gov",
        full_name="Chief Metrology Auditor",
        role=UserRole.AUDITOR,
    )
    db_session.add(user)
    db_session.flush()

    assert isinstance(user.id, uuid.UUID)
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.role == UserRole.AUDITOR
    assert user.is_active is True


def test_instrument_and_configuration_decimal_precision(db_session: Session):
    """Requirement 9: Metrological quantities MUST use Python Decimal and not float."""
    instrument = Instrument(
        manufacturer="Mettler Toledo Test Mock",
        model_name="XP-205",
        instrument_family="NAWI",
        serial_number=f"SN-{uuid.uuid4().hex[:8]}",
        status=InstrumentStatus.ACTIVE,
        is_synthetic=False,
    )
    db_session.add(instrument)
    db_session.flush()

    # Exact decimal values for a high-precision Class I balance
    max_val = Decimal("220.000000")
    min_val = Decimal("0.001000")
    e_val = Decimal("0.001000")
    d_val = Decimal("0.000100")

    config = InstrumentConfiguration(
        instrument_id=instrument.id,
        accuracy_class=AccuracyClass.CLASS_I,
        max_capacity=max_val,
        min_capacity=min_val,
        verification_scale_interval=e_val,
        actual_scale_interval=d_val,
        unit="g",
        tare_type=TareType.SUBTRACTIVE,
        is_electronic=True,
        has_zero_setting=True,
    )
    db_session.add(config)
    db_session.flush()

    # Fetch fresh from database and verify Decimal type and precision
    fetched = db_session.get(InstrumentConfiguration, config.id)
    assert fetched is not None
    assert isinstance(fetched.max_capacity, Decimal)
    assert isinstance(fetched.min_capacity, Decimal)
    assert isinstance(fetched.verification_scale_interval, Decimal)
    assert isinstance(fetched.actual_scale_interval, Decimal)

    assert fetched.max_capacity == max_val
    assert fetched.min_capacity == min_val
    assert fetched.verification_scale_interval == e_val
    assert fetched.actual_scale_interval == d_val
    assert fetched.actual_scale_interval <= fetched.verification_scale_interval


def test_rule_and_rule_version_relationship(db_session: Session):
    """Requirement 10: Rule -> RuleVersion relationship."""
    rule = Rule(
        code=f"TEST-RULE-{uuid.uuid4().hex[:6]}",
        name="Test Weighing Evaluation Rule",
        description="Clause test specification",
    )
    db_session.add(rule)
    db_session.flush()

    rule_ver = RuleVersion(
        rule_id=rule.id,
        version_number="2026.1",
        standard_version="OIML R 76-1: 2006",
        clause="A.4.4",
        calculation_identifier="R76_WEIGHING_V1",
        applicability_identifier="R76_APP_V1",
        aggregation_strategy="ALL_POINTS_PASS",
    )
    db_session.add(rule_ver)
    db_session.flush()

    assert rule_ver.rule.code == rule.code
    assert rule.versions[0].version_number == "2026.1"


def test_evaluation_and_configuration_snapshot_immutability(db_session: Session):
    """Requirement 10: Evaluation preserves frozen snapshot and references RuleVersion."""
    # 1. Create Instrument & Configuration
    instrument = Instrument(
        manufacturer="Sartorius Test Bench",
        model_name="Cubis-II",
        instrument_family="NAWI",
        serial_number=f"SN-{uuid.uuid4().hex[:8]}",
        status=InstrumentStatus.ACTIVE,
    )
    db_session.add(instrument)
    db_session.flush()

    config = InstrumentConfiguration(
        instrument_id=instrument.id,
        accuracy_class=AccuracyClass.CLASS_II,
        max_capacity=Decimal("5000.00"),
        min_capacity=Decimal("5.00"),
        verification_scale_interval=Decimal("0.10"),
        actual_scale_interval=Decimal("0.01"),
        unit="g",
    )
    db_session.add(config)
    db_session.flush()

    # 2. Create Rule & Version
    rule = Rule(code=f"R76-{uuid.uuid4().hex[:6]}", name="R-76 Spec")
    db_session.add(rule)
    db_session.flush()

    rule_ver = RuleVersion(
        rule_id=rule.id,
        version_number="1.0.0",
        standard_version="OIML R 76-1",
        clause="A.4",
        calculation_identifier="CALC_V1",
        applicability_identifier="APP_V1",
    )
    db_session.add(rule_ver)
    db_session.flush()

    # 3. Create Evaluation with frozen configuration snapshot
    frozen_snapshot = {
        "accuracy_class": config.accuracy_class.value,
        "max_capacity": str(config.max_capacity),
        "min_capacity": str(config.min_capacity),
        "verification_scale_interval": str(config.verification_scale_interval),
        "actual_scale_interval": str(config.actual_scale_interval),
        "unit": config.unit,
        "snapshot_timestamp": "2026-09-13T12:00:00Z",
    }

    eval_record = Evaluation(
        evaluation_number=f"EVAL-{uuid.uuid4().hex[:8].upper()}",
        instrument_id=instrument.id,
        instrument_configuration_id=config.id,
        rule_version_id=rule_ver.id,
        configuration_snapshot=frozen_snapshot,
        status=EvaluationStatus.IN_PROGRESS,
        lab_name="National Metrology Institute",
    )
    db_session.add(eval_record)
    db_session.flush()

    # 4. Modify original configuration (simulate future edits to instrument configuration)
    config.max_capacity = Decimal("10000.00")
    db_session.flush()

    # 5. Verify Evaluation preserves original frozen snapshot intact!
    fetched_eval = db_session.get(Evaluation, eval_record.id)
    assert fetched_eval is not None
    assert fetched_eval.configuration_snapshot["max_capacity"] == "5000.00"
    assert fetched_eval.instrument_configuration.max_capacity == Decimal("10000.00")
    assert fetched_eval.rule_version.id == rule_ver.id


def test_synthetic_seed_mechanism(db_session: Session):
    """Requirement 17: Verify safe development seed mechanism creates synthetic demo instrument."""
    ids = seed_synthetic_data(db=db_session)
    assert "instrument_id" in ids
    assert "configuration_id" in ids

    # Verify synthetic demo instrument properties
    demo_inst = db_session.get(Instrument, uuid.UUID(ids["instrument_id"]))
    assert demo_inst is not None
    assert demo_inst.is_synthetic is True  # Synthetic guardrail verified
    assert "SYNTH-DEMO" in demo_inst.model_name
