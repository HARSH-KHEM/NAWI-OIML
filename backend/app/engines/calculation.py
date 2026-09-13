"""Calculation Engine implementing authoritative OIML R-76 formulas via dispatch registry.

Ref:
- OIML R 76-1:2006 (E), A.4.4.3 (Evaluation of error prior to rounding)
- OIML R 76-1:2006 (E), A.4.7 (Eccentricity test)
- OIML R 76-1:2006 (E), 3.6.1 & A.4.10 (Repeatability test)

All arithmetic uses Python Decimal. Dynamic eval() is strictly forbidden.
"""

from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional
from app.engines.mpe import MPEEngine, convert_mass
from app.models.configuration import AccuracyClass


class CalculationOutput:
    """Standardized output container for calculation results."""

    def __init__(
        self,
        calculation_code: str,
        formula_reference: str,
        input_snapshot: Dict[str, Any],
        output: Dict[str, Any],
    ):
        self.calculation_code = calculation_code
        self.formula_reference = formula_reference
        self.input_snapshot = input_snapshot
        self.output = output

    def to_dict(self) -> Dict[str, Any]:
        return {
            "calculation_code": self.calculation_code,
            "formula_reference": self.formula_reference,
            "input_snapshot": self.input_snapshot,
            "output": self.output,
        }


class CalculationEngine:
    """Registry-based deterministic calculation engine for OIML R-76."""

    _registry: Dict[str, Callable[..., CalculationOutput]] = {}

    @classmethod
    def register(cls, code: str):
        """Decorator to register a calculation procedure."""
        def decorator(fn: Callable[..., CalculationOutput]):
            cls._registry[code] = fn
            return fn
        return decorator

    @classmethod
    def calculate(cls, calculation_code: str, inputs: Dict[str, Any]) -> CalculationOutput:
        """Execute a registered calculation procedure deterministically."""
        if calculation_code not in cls._registry:
            raise ValueError(f"Unknown or unregistered calculation procedure: {calculation_code!r}")
        return cls._registry[calculation_code](inputs)

    @classmethod
    def list_procedures(cls) -> List[str]:
        return sorted(list(cls._registry.keys()))


@CalculationEngine.register("R76_A4_4_3")
@CalculationEngine.register("R76_A4_4_3_ERROR")
def calculate_weighing_performance(inputs: Dict[str, Any]) -> CalculationOutput:
    """OIML R 76-1:2006 clause A.4.4.3: Evaluation of error prior to rounding.
    
    Formula:
        P = I + 0.5*e - ΔL   (Indication prior to rounding)
        E = P - L            (Error prior to rounding)
        Ec = E - E0          (Corrected error prior to rounding)
        
    MPE is determined according to 3.5.1, Table 6.
    Fails closed: requires explicit load, indication, e, additional_load (ΔL), zero_error (E0).
    """
    # Parse inputs as Decimal without synthetic fallbacks
    if "load" not in inputs or inputs["load"] is None:
        raise ValueError("Missing required observation: 'load' (L)")
    if "indication" not in inputs or inputs["indication"] is None:
        raise ValueError("Missing required observation: 'indication' (I)")
    if "verification_scale_interval" not in inputs or inputs["verification_scale_interval"] is None:
        raise ValueError("Missing required parameter: 'verification_scale_interval' (e)")
    if "additional_load" not in inputs or inputs["additional_load"] is None:
        raise ValueError("Missing required observation: 'additional_load' (ΔL)")
    if "zero_error" not in inputs or inputs["zero_error"] is None:
        raise ValueError("Missing required observation: 'zero_error' (E0)")

    L = Decimal(str(inputs["load"]))
    I = Decimal(str(inputs["indication"]))
    e = Decimal(str(inputs["verification_scale_interval"]))
    delta_L = Decimal(str(inputs["additional_load"]))
    E0 = Decimal(str(inputs["zero_error"]))
    unit = str(inputs.get("unit", "kg"))
    acc_class_str = str(inputs["accuracy_class"])
    acc_class = AccuracyClass(acc_class_str)

    # Calculate indication prior to rounding (P)
    # P = I + 1/2 e - ΔL
    P = I + (Decimal("0.5") * e) - delta_L

    # Calculate error prior to rounding (E)
    # E = P - L
    E = P - L

    # Calculate corrected error prior to rounding (Ec)
    # Ec = E - E0
    Ec = E - E0

    # Determine authoritative MPE for this load
    mpe_res = MPEEngine.calculate_mpe(
        accuracy_class=acc_class,
        load=L,
        e=e,
        load_unit=unit,
        e_unit=unit,
    )

    output = {
        "P": str(P),
        "E": str(E),
        "E0": str(E0),
        "Ec": str(Ec),
        "absolute_error": str(abs(Ec)),
        "mpe_factor": str(mpe_res.mpe_factor),
        "mpe_mass": str(mpe_res.mpe_mass),
        "unit": unit,
        "load_in_e": str(mpe_res.load_in_e),
        "accuracy_class": acc_class.value,
        "r76_clause": "OIML R 76-1:2006, A.4.4.3 & 3.5.1 Table 6",
    }

    input_snapshot = {
        "load": str(L),
        "indication": str(I),
        "verification_scale_interval": str(e),
        "additional_load": str(delta_L),
        "zero_error": str(E0),
        "unit": unit,
        "accuracy_class": acc_class.value,
    }
    if "normalization_trace" in inputs:
        input_snapshot["normalization_trace"] = inputs["normalization_trace"]

    return CalculationOutput(
        calculation_code="R76_A4_4_3_ERROR",
        formula_reference="OIML R 76-1:2006, A.4.4.3",
        input_snapshot=input_snapshot,
        output=output,
    )


@CalculationEngine.register("R76_A4_7")
@CalculationEngine.register("R76_ECCENTRICITY")
def calculate_eccentricity(inputs: Dict[str, Any]) -> CalculationOutput:
    """OIML R 76-1:2006 clause A.4.7: Eccentricity test.
    
    Evaluates error across procedure-configured positions (e.g. QUARTER_1..4, SUPPORT_1..N, ROLL_BEGIN..END).
    Each position error is evaluated according to A.4.4.3:
        P = I + 0.5*e - ΔL
        E = P - L
        Ec = E - E0
    """
    if "positions" not in inputs or not inputs["positions"]:
        raise ValueError("Eccentricity calculation requires 'positions' data")

    positions_data = inputs["positions"]
    e = Decimal(str(inputs["verification_scale_interval"]))
    unit = str(inputs.get("unit", "kg"))
    acc_class = AccuracyClass(str(inputs["accuracy_class"]))

    # Verify positions are present without duplicates
    positions_present = set()
    loads_seen = set()
    for pos in positions_data:
        pos_name = str(pos["position"]).upper()
        if pos_name in positions_present:
            raise ValueError(f"Duplicate eccentricity position: {pos_name}")
        positions_present.add(pos_name)
        if "load" in pos:
            loads_seen.add(Decimal(str(pos["load"])))

    # Enforce consistent test load across all positions
    if len(loads_seen) > 1:
        raise ValueError(f"Eccentricity positions have inconsistent test loads: {[str(x) for x in sorted(list(loads_seen))]}")

    position_results = []
    max_abs_ec = Decimal("0")
    mpe_mass = None

    for pos in positions_data:
        pos_name = str(pos["position"]).upper()
        L = Decimal(str(pos["load"]))
        I = Decimal(str(pos["indication"]))
        delta_L = Decimal(str(pos["additional_load"]))
        E0 = Decimal(str(pos["zero_error"]))

        # P = I + 0.5e - delta_L
        P = I + (Decimal("0.5") * e) - delta_L
        E = P - L
        Ec = E - E0
        abs_ec = abs(Ec)
        if abs_ec > max_abs_ec:
            max_abs_ec = abs_ec

        mpe_res = MPEEngine.calculate_mpe(
            accuracy_class=acc_class,
            load=L,
            e=e,
            load_unit=unit,
            e_unit=unit,
        )
        mpe_mass = mpe_res.mpe_mass

        position_results.append({
            "position": pos_name,
            "load": str(L),
            "indication": str(I),
            "additional_load": str(delta_L),
            "zero_error": str(E0),
            "P": str(P),
            "E": str(E),
            "Ec": str(Ec),
            "absolute_error": str(abs_ec),
            "mpe_mass": str(mpe_res.mpe_mass),
        })

    output = {
        "position_results": position_results,
        "max_absolute_error": str(max_abs_ec),
        "mpe_mass": str(mpe_mass) if mpe_mass else "0",
        "unit": unit,
        "accuracy_class": acc_class.value,
        "r76_clause": "OIML R 76-1:2006, A.4.7.1 & A.4.4.3",
    }

    return CalculationOutput(
        calculation_code="R76_ECCENTRICITY",
        formula_reference="OIML R 76-1:2006, A.4.7.1 & A.4.4.3",
        input_snapshot=inputs,
        output=output,
    )


@CalculationEngine.register("R76_A4_10")
@CalculationEngine.register("R76_REPEATABILITY")
def calculate_repeatability(inputs: Dict[str, Any]) -> CalculationOutput:
    """OIML R 76-1:2006 clause 3.6.1 & A.4.10: Repeatability test.
    
    The difference between the results of several weighings of the same load
    shall not be greater than the absolute value of the maximum permissible error
    of the instrument for that load:
        ΔE = max(I) - min(I) <= |mpe|
    """
    e = Decimal(str(inputs["verification_scale_interval"]))
    unit = str(inputs.get("unit", "kg"))
    acc_class = AccuracyClass(str(inputs["accuracy_class"]))

    # Check for dual-series structured repeatability
    series_50 = inputs.get("series_50")
    series_100 = inputs.get("series_100")

    if series_50 is not None and series_100 is not None:
        max_cap = Decimal(str(inputs["max_capacity"]))
        max_in_kg = convert_mass(max_cap, from_unit=unit, to_unit="kg")
        min_required = 3 if max_in_kg >= Decimal("1000") else 10

        if len(series_50) < min_required:
            raise ValueError(
                f"Series 50_PERCENT_MAX has {len(series_50)} weighings, requires minimum {min_required}"
            )
        if len(series_100) < min_required:
            raise ValueError(
                f"Series 100_PERCENT_MAX has {len(series_100)} weighings, requires minimum {min_required}"
            )

        # Validate that all entries in series_50 have the exact same test_load
        loads_50_set = set(Decimal(str(w["test_load"])) for w in series_50)
        if len(loads_50_set) > 1:
            raise ValueError(f"Series 50_PERCENT_MAX has inconsistent test loads: {[str(x) for x in sorted(list(loads_50_set))]}")
        load_50 = next(iter(loads_50_set))

        # Validate that all entries in series_100 have the exact same test_load
        loads_100_set = set(Decimal(str(w["test_load"])) for w in series_100)
        if len(loads_100_set) > 1:
            raise ValueError(f"Series 100_PERCENT_MAX has inconsistent test loads: {[str(x) for x in sorted(list(loads_100_set))]}")
        load_100 = next(iter(loads_100_set))

        # 50% and 100% series must be distinct
        if load_50 == load_100:
            raise ValueError(f"Series 50_PERCENT_MAX and 100_PERCENT_MAX must have distinct test loads, both are {load_50}")

        # 50% series indications and error
        ind_50 = [Decimal(str(w["loaded_indication"])) for w in series_50]
        span_50 = max(ind_50) - min(ind_50)
        mpe_50 = MPEEngine.calculate_mpe(acc_class, load=load_50, e=e, load_unit=unit, e_unit=unit).mpe_mass

        # 100% series indications and error
        ind_100 = [Decimal(str(w["loaded_indication"])) for w in series_100]
        span_100 = max(ind_100) - min(ind_100)
        mpe_100 = MPEEngine.calculate_mpe(acc_class, load=load_100, e=e, load_unit=unit, e_unit=unit).mpe_mass

        max_span = max(span_50, span_100)
        output = {
            "series_50": {
                "weighings_count": len(series_50),
                "test_load": str(load_50),
                "max_indication": str(max(ind_50)),
                "min_indication": str(min(ind_50)),
                "repeatability_error": str(span_50),
                "mpe_mass": str(mpe_50),
            },
            "series_100": {
                "weighings_count": len(series_100),
                "test_load": str(load_100),
                "max_indication": str(max(ind_100)),
                "min_indication": str(min(ind_100)),
                "repeatability_error": str(span_100),
                "mpe_mass": str(mpe_100),
            },
            "repeatability_error": str(max_span),
            "mpe_mass": str(min(mpe_50, mpe_100)),
            "unit": unit,
            "accuracy_class": acc_class.value,
            "r76_clause": "OIML R 76-1:2006, 3.6.1 & A.4.10",
        }
    else:
        # Single-series / flat weighings (for unit tests / single series invocation)
        series_data = inputs["weighings"]
        L = Decimal(str(inputs["target_load"]))
        indications = [Decimal(str(w["indication"])) for w in series_data]

        if not indications:
            raise ValueError("Repeatability test requires at least one weighing indication")

        max_ind = max(indications)
        min_ind = min(indications)
        range_span = max_ind - min_ind

        mpe_res = MPEEngine.calculate_mpe(
            accuracy_class=acc_class,
            load=L,
            e=e,
            load_unit=unit,
            e_unit=unit,
        )

        output = {
            "weighings_count": len(indications),
            "target_load": str(L),
            "max_indication": str(max_ind),
            "min_indication": str(min_ind),
            "repeatability_error": str(range_span),
            "mpe_mass": str(mpe_res.mpe_mass),
            "unit": unit,
            "accuracy_class": acc_class.value,
            "r76_clause": "OIML R 76-1:2006, 3.6.1 & A.4.10",
        }

    return CalculationOutput(
        calculation_code="R76_REPEATABILITY",
        formula_reference="OIML R 76-1:2006, 3.6.1 & A.4.10",
        input_snapshot=inputs,
        output=output,
    )
