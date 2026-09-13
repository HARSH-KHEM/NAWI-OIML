"""Service coordinating observation aggregation, calculation execution, and compliance decisions."""

from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.calculation import CalculationEngine, CalculationOutput
from app.engines.compliance import ComplianceEngine, ComplianceEvaluation
from app.engines.mpe import convert_mass
from app.models.metrology import AuditEvent, Calculation, ComplianceDecision, ComplianceResult
from app.models.rule import RuleVersion
from app.models.test_execution import (
    EvaluationTest,
    EvaluationTestStatus,
    Observation,
    TestAttempt,
)

logger = logging.getLogger(__name__)


def normalize_mass_observation(
    value: Optional[Decimal],
    obs_unit: Optional[str],
    target_unit: str,
    field_name: str,
) -> Tuple[Decimal, Dict[str, Any]]:
    """Convert a mass observation to the target unit and produce a trace record.
    
    Fails closed if unit is missing or unknown.
    Never mutates the raw observation.
    """
    if value is None:
        raise ValueError(f"Measurement value for '{field_name}' is None")
    if not obs_unit or not str(obs_unit).strip():
        raise ValueError(f"Missing required unit on observation for '{field_name}'")
    clean_obs = str(obs_unit).strip().lower()
    clean_target = str(target_unit).strip().lower()
    try:
        normalized_value = convert_mass(value, from_unit=clean_obs, to_unit=clean_target)
    except Exception as exc:
        raise ValueError(f"Cannot convert '{field_name}' from unit '{obs_unit}' to '{target_unit}': {exc}")

    trace_entry = {
        "field": field_name,
        "original_value": str(value),
        "original_unit": clean_obs,
        "normalized_value": str(normalized_value),
        "normalized_unit": clean_target,
    }
    return normalized_value, trace_entry


def serialize_for_json(data: Any) -> Any:
    """Recursively convert Decimals and UUIDs to strings or standard types for JSON storage."""
    if isinstance(data, Decimal):
        return str(data)
    elif isinstance(data, uuid.UUID):
        return str(data)
    elif isinstance(data, dict):
        return {k: serialize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_for_json(x) for x in data]
    return data


def _handle_incomplete_attempt(
    db: Session,
    attempt: TestAttempt,
    eval_test: EvaluationTest,
    eval_record: Any,
    test_code: str,
    reason: str,
    missing_observations: List[str],
    rule_version_id: Optional[uuid.UUID],
    content_hash: Optional[str],
    actor_id: Optional[str],
) -> Dict[str, Any]:
    """Persist an authoritative INCOMPLETE compliance result when required observations are missing.
    
    Ensures zero fabricated measurement values enter the calculation engine.
    Calculation entity is not executed or persisted.
    """
    comp_eval = ComplianceEngine.create_incomplete_evaluation(
        test_code=test_code,
        reason=reason,
        missing_observations=missing_observations,
        rule_version_id=rule_version_id,
        content_hash=content_hash,
    )

    comp_record = ComplianceResult(
        test_attempt_id=attempt.id,
        calculation_id=None,  # Calculation did not execute
        decision=ComplianceDecision.INCOMPLETE,
        criterion_value="N/A",
        measured_value="INCOMPLETE",
        margin=None,
        rule_version_id=rule_version_id,
        reasoning_json=comp_eval.reasoning_json,
    )
    db.add(comp_record)
    db.flush()

    # Update EvaluationTest status to INCOMPLETE
    eval_test.status = EvaluationTestStatus.INCOMPLETE

    # Record AuditEvent
    audit_evt = AuditEvent(
        evaluation_id=eval_record.id,
        entity_type="COMPLIANCE",
        entity_id=comp_record.id,
        action="COMPLIANCE_DECIDED",
        actor_id=actor_id,
        metadata_json={
            "decision": ComplianceDecision.INCOMPLETE.value,
            "attempt_id": str(attempt.id),
            "reason": reason,
            "missing_observations": missing_observations,
        },
    )
    db.add(audit_evt)
    db.commit()

    logger.info(
        "Attempt %s marked INCOMPLETE: %s (missing: %s)",
        attempt.id,
        reason,
        missing_observations,
    )

    return {
        "calculation": None,
        "compliance": {
            "id": str(comp_record.id),
            "decision": comp_record.decision.value,
            "measured_value": comp_record.measured_value,
            "criterion_value": comp_record.criterion_value,
            "margin": comp_record.margin,
            "reasoning": comp_record.reasoning_json,
            "decided_at": comp_record.decided_at.isoformat(),
        },
    }


def execute_attempt_calculation(
    db: Session,
    attempt_id: uuid.UUID,
    actor_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute authoritative R-76 calculations and compliance evaluation for a test attempt.
    
    1. Gathers observations for the attempt.
    2. Validates observations completeness:
       - Missing required observations -> calculation must NOT execute; compliance decision = INCOMPLETE.
    3. Resolves RuleVersion, calculation_identifier, and structured criterion contract.
    4. Invokes CalculationEngine (deterministic trusted dispatch, Decimal arithmetic).
    5. Persists Calculation entity.
    6. Invokes ComplianceEngine with structured criterion metadata.
    7. Persists ComplianceResult entity.
    8. Updates test status.
    9. Records AuditEvents inside an atomic transaction (rolls back entirely on failure).
    """
    attempt = db.get(TestAttempt, attempt_id)
    if not attempt:
        raise ValueError(f"TestAttempt {attempt_id} not found")

    eval_test = attempt.evaluation_test
    test_def = eval_test.test_definition
    eval_record = eval_test.evaluation
    snapshot = eval_record.configuration_snapshot or {}
    test_code = test_def.test_code

    # 1. Resolve RuleVersion explicitly - fail closed if missing or unresolvable
    target_rule_version_id = eval_test.rule_version_id or eval_record.rule_version_id
    if not target_rule_version_id:
        raise ValueError(
            f"EvaluationTest {eval_test.id} (evaluation {eval_record.id}) has no associated RuleVersion"
        )

    rule_ver = db.get(RuleVersion, target_rule_version_id)
    if not rule_ver:
        raise ValueError(
            f"Frozen RuleVersion {target_rule_version_id} for test {eval_test.id} cannot be resolved in database"
        )

    rule_version_id = rule_ver.id
    content_hash = rule_ver.content_hash
    rule_def = rule_ver.definition_json
    if not rule_def or not isinstance(rule_def, dict):
        raise ValueError(
            f"RuleVersion '{rule_ver.version_number}' has missing or malformed definition_json"
        )

    # 2. Extract base lookup code (e.g. WEIGHING_PERFORMANCE from WEIGHING_PERFORMANCE_RANGE_1)
    lookup_code = test_code
    if "_RANGE_" in lookup_code:
        lookup_code = lookup_code.split("_RANGE_")[0]

    # 3. Resolve test configuration from RuleVersion structured definition_json
    test_rule_config = None
    if "tests" in rule_def and isinstance(rule_def["tests"], dict) and lookup_code in rule_def["tests"]:
        test_rule_config = rule_def["tests"][lookup_code]
    elif rule_def.get("test_code") == lookup_code:
        test_rule_config = rule_def

    if not test_rule_config or not isinstance(test_rule_config, dict):
        raise ValueError(
            f"RuleVersion '{rule_ver.version_number}' definition_json is missing configuration for test '{lookup_code}'"
        )

    calc_id = test_rule_config.get("calculation_identifier")
    if not calc_id:
        raise ValueError(
            f"RuleVersion '{rule_ver.version_number}' definition_json for test '{lookup_code}' is missing 'calculation_identifier'"
        )

    criterion_config = test_rule_config.get("criterion")
    if not criterion_config or not isinstance(criterion_config, dict) or "type" not in criterion_config:
        raise ValueError(
            f"RuleVersion '{rule_ver.version_number}' definition_json for test '{lookup_code}' is missing structured 'criterion.type'"
        )

    # Gather observations for this attempt
    observations = db.scalars(
        select(Observation).where(Observation.test_attempt_id == attempt.id)
    ).all()

    if not observations:
        return _handle_incomplete_attempt(
            db=db,
            attempt=attempt,
            eval_test=eval_test,
            eval_record=eval_record,
            test_code=test_code,
            reason="No observations recorded for test attempt",
            missing_observations=["ALL_OBSERVATIONS"],
            rule_version_id=rule_version_id,
            content_hash=content_hash,
            actor_id=actor_id,
        )

    obs_map = {obs.observation_code: obs for obs in observations}

    # Resolve active scale interval, capacity, and unit from range or global configuration
    # Use explicit None check for range_index (0 is a valid range index)
    if eval_test.range_index is not None and snapshot.get("ranges"):
        matching_range = next(
            (r for r in snapshot["ranges"] if int(r["range_index"]) == eval_test.range_index),
            None,
        )
        if not matching_range:
            raise ValueError(f"Range index {eval_test.range_index} not found in configuration snapshot ranges")
        e_val = Decimal(str(matching_range["verification_scale_interval"]))
        max_cap = Decimal(str(matching_range["max_capacity"]))
        target_unit = str(matching_range.get("unit", snapshot.get("unit", "kg"))).lower()
    else:
        if "max_capacity" not in snapshot or "verification_scale_interval" not in snapshot:
            raise ValueError("Configuration snapshot missing required max_capacity or verification_scale_interval")
        e_val = Decimal(str(snapshot["verification_scale_interval"]))
        max_cap = Decimal(str(snapshot["max_capacity"]))
        target_unit = str(snapshot.get("unit", "kg")).lower()

    acc_class_str = str(snapshot["accuracy_class"])

    # -------------------------------------------------------------
    # 1. WEIGHING PERFORMANCE VALIDATION & INPUT PREPARATION
    # -------------------------------------------------------------
    if "WEIGHING_PERFORMANCE" in test_code:
        required_obs = ["LOAD", "INDICATION", "ADDITIONAL_LOAD", "ZERO_ERROR"]
        missing_obs = [
            code for code in required_obs
            if code not in obs_map or obs_map[code].value_numeric is None
        ]
        if missing_obs:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Weighing performance test is incomplete. Missing required observation(s): {', '.join(missing_obs)}",
                missing_observations=missing_obs,
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        norm_trace = []
        try:
            norm_load, t_load = normalize_mass_observation(obs_map["LOAD"].value_numeric, obs_map["LOAD"].unit, target_unit, "LOAD")
            norm_indication, t_ind = normalize_mass_observation(obs_map["INDICATION"].value_numeric, obs_map["INDICATION"].unit, target_unit, "INDICATION")
            norm_delta_l, t_del = normalize_mass_observation(obs_map["ADDITIONAL_LOAD"].value_numeric, obs_map["ADDITIONAL_LOAD"].unit, target_unit, "ADDITIONAL_LOAD")
            norm_zero_err, t_zero = normalize_mass_observation(obs_map["ZERO_ERROR"].value_numeric, obs_map["ZERO_ERROR"].unit, target_unit, "ZERO_ERROR")
            norm_trace.extend([t_load, t_ind, t_del, t_zero])
        except ValueError as ve:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Weighing performance observation unit normalization failed: {ve}",
                missing_observations=["VALID_UNIT_OBSERVATIONS"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        calc_inputs = {
            "load": norm_load,
            "indication": norm_indication,
            "verification_scale_interval": e_val,
            "additional_load": norm_delta_l,
            "zero_error": norm_zero_err,
            "accuracy_class": acc_class_str,
            "unit": target_unit,
            "normalization_trace": norm_trace,
        }

    # -------------------------------------------------------------
    # 2. ECCENTRICITY VALIDATION & INPUT PREPARATION
    # -------------------------------------------------------------
    elif test_code == "ECCENTRICITY":
        from app.engines.applicability import (
            calculate_required_eccentricity_load,
            determine_eccentricity_procedure,
        )

        proc_info = determine_eccentricity_procedure(snapshot)
        if proc_info["status"] != "SUPPORTED":
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Eccentricity procedure cannot be determined. {proc_info.get('reason', 'Missing geometry metadata')}",
                missing_observations=["VALID_LOAD_RECEPTOR_GEOMETRY"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        procedure_name = proc_info["procedure"]
        expected_positions = set(proc_info["positions"])
        req_load = calculate_required_eccentricity_load(snapshot, proc_info)

        positions_list = []
        found_positions = set()
        missing_fields_by_position = {}
        non_numeric_positions = {}
        unit_errors = {}
        norm_trace = []
        duplicate_positions = set()

        for obs in observations:
            pos_data = obs.value_json or {}
            pos_name = pos_data.get("position")
            if not pos_name and obs.observation_code.startswith("POS_"):
                pos_name = obs.observation_code.replace("POS_", "")

            if pos_name:
                pos_name_upper = str(pos_name).upper()
                if pos_name_upper in found_positions:
                    duplicate_positions.add(pos_name_upper)
                found_positions.add(pos_name_upper)

                # Check required eccentricity fields: load, indication, additional_load, zero_error
                missing_for_pos = []
                for field in ("load", "indication", "additional_load", "zero_error"):
                    val = pos_data.get(field)
                    if val is None or str(val).strip() == "":
                        missing_for_pos.append(field)

                if missing_for_pos:
                    missing_fields_by_position[pos_name_upper] = missing_for_pos
                    continue

                # Validate unit
                pos_unit = pos_data.get("unit") or obs.unit
                if not pos_unit or not str(pos_unit).strip():
                    unit_errors[pos_name_upper] = "Missing unit on eccentricity observation"
                    continue

                try:
                    raw_load = Decimal(str(pos_data["load"]))
                    raw_ind = Decimal(str(pos_data["indication"]))
                    raw_del = Decimal(str(pos_data["additional_load"]))
                    raw_zero = Decimal(str(pos_data["zero_error"]))
                except Exception as ex:
                    non_numeric_positions[pos_name_upper] = str(ex)
                    continue

                try:
                    n_load, t_l = normalize_mass_observation(raw_load, pos_unit, target_unit, f"{pos_name_upper}.load")
                    n_ind, t_i = normalize_mass_observation(raw_ind, pos_unit, target_unit, f"{pos_name_upper}.indication")
                    n_del, t_d = normalize_mass_observation(raw_del, pos_unit, target_unit, f"{pos_name_upper}.additional_load")
                    n_zero, t_z = normalize_mass_observation(raw_zero, pos_unit, target_unit, f"{pos_name_upper}.zero_error")
                    norm_trace.extend([t_l, t_i, t_d, t_z])
                except Exception as ex:
                    unit_errors[pos_name_upper] = str(ex)
                    continue

                positions_list.append({
                    "position": pos_name_upper,
                    "load": n_load,
                    "indication": n_ind,
                    "additional_load": n_del,
                    "zero_error": n_zero,
                })

        if duplicate_positions:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Duplicate eccentricity positions recorded: {sorted(list(duplicate_positions))}",
                missing_observations=["UNIQUE_ECCENTRICITY_POSITIONS"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        if unit_errors:
            details = [f"{p}: {err}" for p, err in sorted(unit_errors.items())]
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Eccentricity unit error(s): {'; '.join(details)}",
                missing_observations=["VALID_UNIT_ECCENTRICITY"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        if non_numeric_positions:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Eccentricity positions contain non-numeric values: {non_numeric_positions}",
                missing_observations=[f"VALID_NUMERIC_{p}" for p in sorted(non_numeric_positions.keys())],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        if missing_fields_by_position:
            details = [f"{pos} missing: {', '.join(fields)}" for pos, fields in sorted(missing_fields_by_position.items())]
            missing_flat = [f"{pos}_{f.upper()}" for pos, fields in sorted(missing_fields_by_position.items()) for f in fields]
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Eccentricity test is incomplete. Missing required measurement values: {'; '.join(details)}",
                missing_observations=missing_flat,
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        missing_positions = expected_positions - found_positions
        if missing_positions:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Eccentricity test is incomplete for procedure '{procedure_name}'. Missing required positions: {', '.join(sorted(missing_positions))}",
                missing_observations=sorted(list(missing_positions)),
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        extra_positions = found_positions - expected_positions
        if extra_positions:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Unrecognized positions for procedure '{procedure_name}': {', '.join(sorted(extra_positions))}",
                missing_observations=["VALID_PROCEDURE_POSITIONS"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        # Validate that all positions have a consistent test load
        pos_loads = set(p["load"] for p in positions_list)
        if len(pos_loads) > 1:
            details = {p["position"]: str(p["load"]) for p in positions_list}
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Eccentricity test requires consistent test load across all positions. Inconsistent loads found: {details}",
                missing_observations=["CONSISTENT_ECCENTRICITY_LOAD"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        ecc_load = next(iter(pos_loads))
        if ecc_load <= Decimal("0"):
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Eccentricity test load must be strictly positive, got {ecc_load}",
                missing_observations=["POSITIVE_ECCENTRICITY_LOAD"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        if ecc_load > max_cap:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Eccentricity test load ({ecc_load} {target_unit}) exceeds maximum capacity Max ({max_cap} {target_unit})",
                missing_observations=["VALID_ECCENTRICITY_LOAD_WITHIN_MAX"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        # Validate observed load matches required procedure load within tolerance (±2%)
        load_tolerance = req_load * Decimal("0.02")
        if abs(ecc_load - req_load) > load_tolerance:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=(
                    f"Incorrect eccentricity test load: observed {ecc_load} {target_unit}, "
                    f"required {req_load} {target_unit} (tolerance ±{load_tolerance} {target_unit}) "
                    f"for procedure {procedure_name}. No compliance calculation permitted from an invalid load."
                ),
                missing_observations=["CORRECT_ECCENTRICITY_LOAD"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        calc_inputs = {
            "procedure": procedure_name,
            "positions": positions_list,
            "verification_scale_interval": e_val,
            "accuracy_class": acc_class_str,
            "unit": target_unit,
            "required_test_load": req_load,
            "normalization_trace": norm_trace,
        }

    # -------------------------------------------------------------
    # 3. REPEATABILITY VALIDATION & INPUT PREPARATION
    # -------------------------------------------------------------
    elif test_code == "REPEATABILITY":
        max_in_kg = convert_mass(max_cap, from_unit=target_unit, to_unit="kg")
        min_required_weighings = 3 if max_in_kg >= Decimal("1000") else 10

        series_50 = []
        series_100 = []
        invalid_numeric_entries = []
        unit_errors = []
        norm_trace = []
        seen_indices_50 = set()
        seen_indices_100 = set()

        for obs in observations:
            v_json = obs.value_json or {}
            s_type = v_json.get("series")
            if not s_type:
                continue

            obs_unit = obs.unit or v_json.get("unit")
            if not obs_unit or not str(obs_unit).strip():
                unit_errors.append(f"Observation {obs.observation_code} missing unit")
                continue

            # Validate required numeric fields
            missing_or_invalid = []
            raw_vals = {}
            for num_field in ("test_load", "loaded_indication", "unloaded_indication"):
                raw_val = v_json.get(num_field)
                if raw_val is None or str(raw_val).strip() == "":
                    missing_or_invalid.append(f"{num_field} missing")
                else:
                    try:
                        d_val = Decimal(str(raw_val))
                        if num_field == "test_load" and d_val <= Decimal("0"):
                            missing_or_invalid.append(f"{num_field} must be > 0")
                        else:
                            raw_vals[num_field] = d_val
                    except Exception:
                        missing_or_invalid.append(f"{num_field} non-numeric ('{raw_val}')")

            if missing_or_invalid:
                idx = v_json.get("weighing_index", "unknown")
                invalid_numeric_entries.append(f"{s_type} weighing {idx}: {', '.join(missing_or_invalid)}")
                continue

            # Normalize units to target_unit
            try:
                norm_load, t_l = normalize_mass_observation(raw_vals["test_load"], obs_unit, target_unit, f"{s_type}.weighing_{v_json.get('weighing_index')}.test_load")
                norm_loaded, t_i = normalize_mass_observation(raw_vals["loaded_indication"], obs_unit, target_unit, f"{s_type}.weighing_{v_json.get('weighing_index')}.loaded_indication")
                norm_unloaded, t_u = normalize_mass_observation(raw_vals["unloaded_indication"], obs_unit, target_unit, f"{s_type}.weighing_{v_json.get('weighing_index')}.unloaded_indication")
                norm_trace.extend([t_l, t_i, t_u])
            except Exception as e:
                unit_errors.append(str(e))
                continue

            normalized_entry = {
                "series": s_type,
                "weighing_index": int(v_json["weighing_index"]),
                "test_load": norm_load,
                "loaded_indication": norm_loaded,
                "unloaded_indication": norm_unloaded,
                "unit": target_unit,
            }

            if s_type == "50_PERCENT_MAX":
                idx = normalized_entry["weighing_index"]
                if idx in seen_indices_50:
                    invalid_numeric_entries.append(f"Duplicate weighing_index {idx} in 50_PERCENT_MAX")
                seen_indices_50.add(idx)
                series_50.append(normalized_entry)
            elif s_type == "100_PERCENT_MAX":
                idx = normalized_entry["weighing_index"]
                if idx in seen_indices_100:
                    invalid_numeric_entries.append(f"Duplicate weighing_index {idx} in 100_PERCENT_MAX")
                seen_indices_100.add(idx)
                series_100.append(normalized_entry)

        # 1. Reject unit errors
        if unit_errors:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Repeatability weighings contain unit errors: {'; '.join(unit_errors)}",
                missing_observations=["VALID_UNIT_WEIGHINGS"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        # 2. Reject invalid or missing numeric fields / duplicate indices
        if invalid_numeric_entries:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Repeatability weighings contain invalid or missing numeric fields: {'; '.join(invalid_numeric_entries)}",
                missing_observations=["VALID_NUMERIC_WEIGHINGS"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        # 3. Check for series count completeness
        missing_series_info = []
        if len(series_50) < min_required_weighings:
            missing_series_info.append(
                f"50_PERCENT_MAX has {len(series_50)}/{min_required_weighings} required weighings"
            )
        if len(series_100) < min_required_weighings:
            missing_series_info.append(
                f"100_PERCENT_MAX has {len(series_100)}/{min_required_weighings} required weighings"
            )

        if missing_series_info:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Repeatability test is incomplete: {', '.join(missing_series_info)}",
                missing_observations=missing_series_info,
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        # 4. Check test_load consistency within series_50
        loads_50 = [Decimal(str(w["test_load"])) for w in series_50]
        distinct_loads_50 = sorted(list(set(loads_50)))
        if len(distinct_loads_50) > 1:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Repeatability 50% Max series has inconsistent test loads: {[str(x) for x in distinct_loads_50]}",
                missing_observations=["CONSISTENT_LOAD_50_PERCENT_MAX"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        # 5. Check test_load consistency within series_100
        loads_100 = [Decimal(str(w["test_load"])) for w in series_100]
        distinct_loads_100 = sorted(list(set(loads_100)))
        if len(distinct_loads_100) > 1:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Repeatability 100% Max series has inconsistent test loads: {[str(x) for x in distinct_loads_100]}",
                missing_observations=["CONSISTENT_LOAD_100_PERCENT_MAX"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        # 6. Check that 50% Max and 100% Max series are distinct
        if distinct_loads_50[0] == distinct_loads_100[0]:
            return _handle_incomplete_attempt(
                db=db,
                attempt=attempt,
                eval_test=eval_test,
                eval_record=eval_record,
                test_code=test_code,
                reason=f"Repeatability 50% Max and 100% Max series must have distinct test loads (both are {distinct_loads_50[0]} {target_unit})",
                missing_observations=["DISTINCT_SERIES_LOADS"],
                rule_version_id=rule_version_id,
                content_hash=content_hash,
                actor_id=actor_id,
            )

        calc_inputs = {
            "series_50": series_50,
            "series_100": series_100,
            "max_capacity": max_cap,
            "verification_scale_interval": e_val,
            "accuracy_class": acc_class_str,
            "unit": target_unit,
            "normalization_trace": norm_trace,
        }

    else:
        calc_inputs = {"observations_count": len(observations), "unit": target_unit}

    # -------------------------------------------------------------
    # ATOMIC TRANSACTION BLOCK FOR AUTHORITATIVE PERSISTENCE
    # -------------------------------------------------------------
    try:
        # 1. Execute Calculation
        calc_output: CalculationOutput = CalculationEngine.calculate(calc_id, calc_inputs)

        # 2. Persist Calculation
        input_snap = dict(calc_output.input_snapshot)
        if "normalization_trace" in calc_inputs and "normalization_trace" not in input_snap:
            input_snap["normalization_trace"] = calc_inputs["normalization_trace"]

        calc_record = Calculation(
            test_attempt_id=attempt.id,
            calculation_code=calc_output.calculation_code,
            input_snapshot_json=serialize_for_json(input_snap),
            output_json=serialize_for_json(calc_output.output),
            formula_reference=calc_output.formula_reference,
            rule_version_id=rule_version_id,
        )
        db.add(calc_record)
        db.flush()

        # 3. Execute Compliance Evaluation using RuleVersion criterion config
        compliance_eval: ComplianceEvaluation = ComplianceEngine.evaluate(
            calculation_code=calc_output.calculation_code,
            output_data=calc_output.output,
            criterion_config=criterion_config,
            rule_version_id=rule_version_id,
            content_hash=content_hash,
        )

        # 4. Persist ComplianceResult
        comp_record = ComplianceResult(
            test_attempt_id=attempt.id,
            calculation_id=calc_record.id,
            decision=compliance_eval.decision,
            criterion_value=compliance_eval.criterion_value,
            measured_value=compliance_eval.measured_value,
            margin=compliance_eval.margin,
            rule_version_id=rule_version_id,
            reasoning_json=compliance_eval.reasoning_json,
        )
        db.add(comp_record)
        db.flush()

        # 5. Update EvaluationTest status to COMPLETED
        eval_test.status = EvaluationTestStatus.COMPLETED

        # 6. Record AuditEvents
        db.add(
            AuditEvent(
                evaluation_id=eval_record.id,
                entity_type="CALCULATION",
                entity_id=calc_record.id,
                action="CALCULATION_EXECUTED",
                actor_id=actor_id,
                metadata_json={"code": calc_record.calculation_code, "attempt_id": str(attempt.id)},
            )
        )
        db.add(
            AuditEvent(
                evaluation_id=eval_record.id,
                entity_type="COMPLIANCE",
                entity_id=comp_record.id,
                action="COMPLIANCE_DECIDED",
                actor_id=actor_id,
                metadata_json={"decision": comp_record.decision.value, "attempt_id": str(attempt.id)},
            )
        )

        db.commit()

        logger.info(
            "Calculation executed for attempt %s: Decision=%s, Measured=%s, Criterion=%s",
            attempt.id,
            comp_record.decision.value,
            comp_record.measured_value,
            comp_record.criterion_value,
        )

        return {
            "calculation": {
                "id": str(calc_record.id),
                "code": calc_record.calculation_code,
                "calculation_code": calc_record.calculation_code,
                "formula_reference": calc_record.formula_reference,
                "input_snapshot": calc_record.input_snapshot_json,
                "output": calc_record.output_json,
                "calculated_at": calc_record.calculated_at.isoformat(),
            },
            "compliance": {
                "id": str(comp_record.id),
                "decision": comp_record.decision.value,
                "measured_value": comp_record.measured_value,
                "criterion_value": comp_record.criterion_value,
                "margin": comp_record.margin,
                "reasoning": comp_record.reasoning_json,
                "decided_at": comp_record.decided_at.isoformat(),
            },
        }

    except Exception as exc:
        db.rollback()
        logger.error("Failed to execute attempt calculation for attempt %s: %s", attempt_id, exc)
        raise
