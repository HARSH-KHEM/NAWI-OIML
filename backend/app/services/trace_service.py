"""Service building end-to-end audit traceability graphs."""

from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.metrology import Calculation, ComplianceResult
from app.models.test_execution import Observation, TestAttempt


def get_test_attempt_trace(db: Session, attempt_id: uuid.UUID) -> Dict[str, Any]:
    """Construct complete traceability chain for a test attempt.
    
    Trace hierarchy:
    Compliance Result -> Criterion -> Rule Version -> Calculation -> Raw Observations -> Test Attempt -> Evaluation Test -> Evaluation -> Configuration Snapshot -> Instrument
    """
    attempt = db.get(TestAttempt, attempt_id)
    if not attempt:
        raise ValueError(f"TestAttempt {attempt_id} not found")

    eval_test = attempt.evaluation_test
    evaluation = eval_test.evaluation
    instrument = evaluation.instrument
    rule_ver = eval_test.rule_version

    # Latest compliance result and calculation queried reliably from session/DB
    compliance = db.scalars(
        select(ComplianceResult)
        .where(ComplianceResult.test_attempt_id == attempt.id)
        .order_by(ComplianceResult.created_at.desc())
    ).first()

    calc = db.scalars(
        select(Calculation)
        .where(Calculation.test_attempt_id == attempt.id)
        .order_by(Calculation.created_at.desc())
    ).first()

    obs_list = db.scalars(
        select(Observation)
        .where(Observation.test_attempt_id == attempt.id)
        .order_by(Observation.observed_at.asc())
    ).all()

    observations_data: List[Dict[str, Any]] = [
        {
            "id": str(obs.id),
            "code": obs.observation_code,
            "numeric_value": str(obs.value_numeric) if obs.value_numeric is not None else None,
            "text_value": obs.value_text,
            "unit": obs.unit,
            "value_json": obs.value_json,
            "observed_at": obs.observed_at.isoformat(),
            "entered_by": obs.entered_by,
        }
        for obs in obs_list
    ]

    trace = {
        "test_attempt_id": str(attempt.id),
        "attempt_number": attempt.attempt_number,
        "attempt_status": attempt.status.value,
        "compliance": {
            "id": str(compliance.id) if compliance else None,
            "decision": compliance.decision.value if compliance else None,
            "measured_value": compliance.measured_value if compliance else None,
            "criterion_value": compliance.criterion_value if compliance else None,
            "margin": compliance.margin if compliance else None,
            "reasoning": compliance.reasoning_json if compliance else None,
            "decided_at": compliance.decided_at.isoformat() if compliance else None,
        } if compliance else None,
        "calculation": {
            "id": str(calc.id) if calc else None,
            "code": calc.calculation_code if calc else None,
            "formula_reference": calc.formula_reference if calc else None,
            "input_snapshot": calc.input_snapshot_json if calc else None,
            "output": calc.output_json if calc else None,
            "calculated_at": calc.calculated_at.isoformat() if calc else None,
        } if calc else None,
        "raw_observations": observations_data,
        "rule_version": {
            "id": str(rule_ver.id),
            "version_number": rule_ver.version_number,
            "standard_version": rule_ver.standard_version,
            "clause": rule_ver.clause,
            "calculation_identifier": rule_ver.calculation_identifier,
            "content_hash": rule_ver.content_hash,
        } if rule_ver else None,
        "evaluation_test": {
            "id": str(eval_test.id),
            "test_code": eval_test.test_definition.test_code,
            "title": eval_test.test_definition.title,
            "r76_reference": eval_test.test_definition.r76_reference,
            "sequence": eval_test.sequence,
            "status": eval_test.status.value,
            "scope_type": eval_test.scope_type,
            "range_reference": eval_test.range_reference,
            "range_index": eval_test.range_index,
        },
        "evaluation": {
            "id": str(evaluation.id),
            "evaluation_number": evaluation.evaluation_number,
            "status": evaluation.status.value,
            "created_at": evaluation.created_at.isoformat(),
        },
        "configuration_snapshot": evaluation.configuration_snapshot,
        "instrument": {
            "id": str(instrument.id),
            "manufacturer": instrument.manufacturer,
            "model_name": instrument.model_name,
            "serial_number": instrument.serial_number,
            "is_synthetic": instrument.is_synthetic,
        },
    }

    return trace
