import uuid
from decimal import Decimal
from typing import Any, Callable, Dict, NamedTuple, Optional
from app.models.metrology import ComplianceDecision


class ComplianceEvaluation(NamedTuple):
    """Container for compliance evaluation result."""
    decision: ComplianceDecision
    criterion_value: str
    measured_value: str
    margin: Optional[str]
    rule_reference: str
    calculation_code: str
    reasoning_json: Dict[str, Any]


class ComplianceEngine:
    """Deterministic metrological compliance evaluator using a trusted Python dispatch registry."""

    _criterion_registry: Dict[str, Callable[..., ComplianceEvaluation]] = {}

    @classmethod
    def register_criterion(cls, criterion_type: str):
        """Decorator to register a trusted criterion evaluator."""
        def decorator(fn: Callable[..., ComplianceEvaluation]):
            cls._criterion_registry[criterion_type] = fn
            return fn
        return decorator

    @classmethod
    def evaluate(
        cls,
        calculation_code: str,
        output_data: Dict[str, Any],
        criterion_config: Optional[Dict[str, Any]] = None,
        rule_version_id: Optional[uuid.UUID] = None,
        content_hash: Optional[str] = None,
    ) -> ComplianceEvaluation:
        """Evaluate calculation output against OIML R-76 acceptance criteria.
        
        Uses RuleVersion structured criterion metadata when provided, with trusted Python dispatch.
        Zero eval() invocation.
        """
        criterion_type = (criterion_config or {}).get("type")

        # Map calculation code if criterion_type not explicitly given
        if not criterion_type:
            if calculation_code in ("R76_A4_4_3", "R76_A4_4_3_ERROR"):
                criterion_type = "ABS_LE_MPE"
            elif calculation_code in ("R76_A4_7", "R76_ECCENTRICITY"):
                criterion_type = "MAX_POS_ABS_LE_MPE"
            elif calculation_code in ("R76_A4_10", "R76_REPEATABILITY"):
                criterion_type = "SPAN_LE_MPE"
            else:
                criterion_type = "UNKNOWN"

        if criterion_type in cls._criterion_registry:
            eval_res = cls._criterion_registry[criterion_type](output_data, criterion_config or {})
        else:
            eval_res = ComplianceEvaluation(
                decision=ComplianceDecision.INCOMPLETE,
                criterion_value="N/A",
                measured_value="N/A",
                margin=None,
                rule_reference="OIML R 76-1:2006",
                calculation_code=calculation_code,
                reasoning_json={
                    "decision": ComplianceDecision.INCOMPLETE.value,
                    "explanation": f"Evaluation procedure {calculation_code} (criterion {criterion_type}) is not recognized",
                },
            )

        # Inject RuleVersion audit traceability into reasoning_json
        if rule_version_id is not None or content_hash is not None:
            eval_res.reasoning_json["rule_version_id"] = str(rule_version_id) if rule_version_id else None
            eval_res.reasoning_json["rule_content_hash"] = content_hash

        return eval_res

    @classmethod
    def create_incomplete_evaluation(
        cls,
        test_code: str,
        reason: str,
        missing_observations: Optional[list] = None,
        rule_version_id: Optional[uuid.UUID] = None,
        content_hash: Optional[str] = None,
    ) -> ComplianceEvaluation:
        """Helper to create an authoritative INCOMPLETE decision without fabricated calculations."""
        reasoning = {
            "decision": ComplianceDecision.INCOMPLETE.value,
            "test_code": test_code,
            "explanation": reason,
            "reason": reason,
            "missing_observations": missing_observations or [],
            "rule_version_id": str(rule_version_id) if rule_version_id else None,
            "rule_content_hash": content_hash,
        }
        return ComplianceEvaluation(
            decision=ComplianceDecision.INCOMPLETE,
            criterion_value="N/A",
            measured_value="INCOMPLETE",
            margin=None,
            rule_reference="OIML R 76-1:2006",
            calculation_code=test_code,
            reasoning_json=reasoning,
        )


@ComplianceEngine.register_criterion("ABS_LE_MPE")
def evaluate_weighing_performance(out: Dict[str, Any], criterion_config: Dict[str, Any]) -> ComplianceEvaluation:
    """Evaluate Weighing Performance against Table 6 MPE (|Ec| <= mpe)."""
    abs_ec = Decimal(str(out["absolute_error"]))
    mpe_mass = Decimal(str(out["mpe_mass"]))
    unit = str(out.get("unit", "kg"))
    rule_ref = out.get("r76_clause", "OIML R 76-1:2006, A.4.4.3 & Table 6")

    margin_dec = mpe_mass - abs_ec
    margin_str = f"{'+' if margin_dec >= 0 else ''}{margin_dec:.6f} {unit}"
    measured_str = f"{abs_ec:.6f} {unit}"
    criterion_str = f"<= {mpe_mass:.6f} {unit}"

    if abs_ec <= mpe_mass:
        decision = ComplianceDecision.PASS
        explanation = (
            f"Corrected error ({measured_str}) is within maximum permissible error ({criterion_str}). "
            f"Tolerance margin is {margin_str}."
        )
    else:
        decision = ComplianceDecision.FAIL
        explanation = (
            f"Corrected error ({measured_str}) exceeds maximum permissible error ({criterion_str}) "
            f"by {abs(margin_dec):.6f} {unit}."
        )

    reasoning = {
        "decision": decision.value,
        "measured": measured_str,
        "criterion": criterion_str,
        "margin": margin_str,
        "rule_reference": rule_ref,
        "calculation_reference": "R76_A4_4_3_ERROR",
        "explanation": explanation,
        "criterion_type": "ABS_LE_MPE",
    }

    return ComplianceEvaluation(
        decision=decision,
        criterion_value=criterion_str,
        measured_value=measured_str,
        margin=margin_str,
        rule_reference=rule_ref,
        calculation_code="R76_A4_4_3_ERROR",
        reasoning_json=reasoning,
    )


@ComplianceEngine.register_criterion("MAX_POS_ABS_LE_MPE")
@ComplianceEngine.register_criterion("MAX_ABS_LE_MPE")
def evaluate_eccentricity(out: Dict[str, Any], criterion_config: Dict[str, Any]) -> ComplianceEvaluation:
    """Evaluate Eccentricity test (max |Ec| across all positions <= mpe)."""
    max_abs = Decimal(str(out["max_absolute_error"]))
    mpe_mass = Decimal(str(out["mpe_mass"]))
    unit = str(out.get("unit", "kg"))
    rule_ref = out.get("r76_clause", "OIML R 76-1:2006, A.4.7.1 & A.4.4.3")

    margin_dec = mpe_mass - max_abs
    margin_str = f"{'+' if margin_dec >= 0 else ''}{margin_dec:.6f} {unit}"
    measured_str = f"{max_abs:.6f} {unit}"
    criterion_str = f"<= {mpe_mass:.6f} {unit}"

    if max_abs <= mpe_mass:
        decision = ComplianceDecision.PASS
        explanation = (
            f"Maximum eccentricity error ({measured_str}) across all 5 positions is within MPE ({criterion_str})."
        )
    else:
        decision = ComplianceDecision.FAIL
        explanation = (
            f"Maximum eccentricity error ({measured_str}) exceeds MPE ({criterion_str}) by {abs(margin_dec):.6f} {unit}."
        )

    reasoning = {
        "decision": decision.value,
        "measured": measured_str,
        "criterion": criterion_str,
        "margin": margin_str,
        "rule_reference": rule_ref,
        "calculation_reference": "R76_ECCENTRICITY",
        "explanation": explanation,
        "criterion_type": "MAX_POS_ABS_LE_MPE",
    }

    return ComplianceEvaluation(
        decision=decision,
        criterion_value=criterion_str,
        measured_value=measured_str,
        margin=margin_str,
        rule_reference=rule_ref,
        calculation_code="R76_ECCENTRICITY",
        reasoning_json=reasoning,
    )


@ComplianceEngine.register_criterion("SPAN_LE_MPE")
def evaluate_repeatability(out: Dict[str, Any], criterion_config: Dict[str, Any]) -> ComplianceEvaluation:
    """Evaluate Repeatability test (range span ΔE <= |mpe|)."""
    unit = str(out.get("unit", "kg"))
    rule_ref = out.get("r76_clause", "OIML R 76-1:2006, 3.6.1 & A.4.10")

    # Check if dual series are present
    if "series_50" in out and "series_100" in out:
        s50 = out["series_50"]
        s100 = out["series_100"]
        span_50 = Decimal(str(s50["repeatability_error"]))
        mpe_50 = Decimal(str(s50["mpe_mass"]))
        span_100 = Decimal(str(s100["repeatability_error"]))
        mpe_100 = Decimal(str(s100["mpe_mass"]))

        pass_50 = span_50 <= mpe_50
        pass_100 = span_100 <= mpe_100

        measured_str = f"50% Max: {span_50:.6f} {unit}, 100% Max: {span_100:.6f} {unit}"
        criterion_str = f"50% Max: <= {mpe_50:.6f} {unit}, 100% Max: <= {mpe_100:.6f} {unit}"
        margin_dec = min(mpe_50 - span_50, mpe_100 - span_100)
        margin_str = f"{'+' if margin_dec >= 0 else ''}{margin_dec:.6f} {unit}"

        if pass_50 and pass_100:
            decision = ComplianceDecision.PASS
            explanation = (
                f"Both repeatability series passed: "
                f"50% Max span ({span_50:.6f} {unit}) <= MPE ({mpe_50:.6f} {unit}) and "
                f"100% Max span ({span_100:.6f} {unit}) <= MPE ({mpe_100:.6f} {unit})."
            )
        else:
            decision = ComplianceDecision.FAIL
            failures = []
            if not pass_50:
                failures.append(f"50% Max span ({span_50:.6f} {unit}) exceeds MPE ({mpe_50:.6f} {unit})")
            if not pass_100:
                failures.append(f"100% Max span ({span_100:.6f} {unit}) exceeds MPE ({mpe_100:.6f} {unit})")
            explanation = f"Repeatability test failed: {'; '.join(failures)}."

        reasoning = {
            "decision": decision.value,
            "measured": measured_str,
            "criterion": criterion_str,
            "margin": margin_str,
            "series_50": s50,
            "series_100": s100,
            "rule_reference": rule_ref,
            "calculation_reference": "R76_REPEATABILITY",
            "explanation": explanation,
            "criterion_type": "SPAN_LE_MPE",
        }

        return ComplianceEvaluation(
            decision=decision,
            criterion_value=criterion_str,
            measured_value=measured_str,
            margin=margin_str,
            rule_reference=rule_ref,
            calculation_code="R76_REPEATABILITY",
            reasoning_json=reasoning,
        )

    # Single series fallback
    span = Decimal(str(out["repeatability_error"]))
    mpe_mass = Decimal(str(out["mpe_mass"]))

    margin_dec = mpe_mass - span
    margin_str = f"{'+' if margin_dec >= 0 else ''}{margin_dec:.6f} {unit}"
    measured_str = f"{span:.6f} {unit}"
    criterion_str = f"<= {mpe_mass:.6f} {unit}"

    if span <= mpe_mass:
        decision = ComplianceDecision.PASS
        explanation = (
            f"Repeatability error span ({measured_str}) between weighings is within |mpe| ({criterion_str})."
        )
    else:
        decision = ComplianceDecision.FAIL
        explanation = (
            f"Repeatability error span ({measured_str}) exceeds |mpe| ({criterion_str}) by {abs(margin_dec):.6f} {unit}."
        )

    reasoning = {
        "decision": decision.value,
        "measured": measured_str,
        "criterion": criterion_str,
        "margin": margin_str,
        "rule_reference": rule_ref,
        "calculation_reference": "R76_REPEATABILITY",
        "explanation": explanation,
        "criterion_type": "SPAN_LE_MPE",
    }

    return ComplianceEvaluation(
        decision=decision,
        criterion_value=criterion_str,
        measured_value=measured_str,
        margin=margin_str,
        rule_reference=rule_ref,
        calculation_code="R76_REPEATABILITY",
        reasoning_json=reasoning,
    )
