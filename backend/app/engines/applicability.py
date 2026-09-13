"""Applicability Engine evaluating R-76 test procedures from frozen configuration snapshots.

Authoritative source:
- OIML R 76-1:2006 (E), Section 3.10 (Type evaluation tests and examinations)
- OIML R 76-1:2006 (E), A.4 (Metrological performance tests)
- OIML R 76-1:2006 (E), A.5 (Factors influencing performance)
- OIML R 76-1:2006 (E), A.6 & 3.9.4.3 (Endurance test)
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.engines.mpe import convert_mass, UNIT_RATIOS_TO_GRAM
from app.models.configuration import AccuracyClass
from app.models.test_definition import ImplementationStatus, ScopeType


class ConfigurationValidationError(ValueError):
    """Raised when a configuration snapshot is invalid or missing required metrological attributes."""
    pass


def validate_configuration_snapshot(snapshot: Dict[str, Any]) -> None:
    """Validate configuration snapshot covering metrological correctness.

    Ensures configuration fails closed:
    - accuracy class is present and valid
    - Max > 0
    - Min > 0
    - Min <= Max
    - e > 0
    - d > 0
    - d <= e
    - supported unit
    - is_electronic is present and boolean
    - multiple-range consistency (ranges exist, number_of_ranges, unique indexes, range Max/Min/e/d valid, strictly increasing Max)
    """
    if not isinstance(snapshot, dict) or not snapshot:
        raise ConfigurationValidationError("Configuration snapshot is empty or not a dictionary")

    # 1. Accuracy class
    if "accuracy_class" not in snapshot or snapshot["accuracy_class"] is None:
        raise ConfigurationValidationError("Missing required configuration attribute: 'accuracy_class'")
    try:
        AccuracyClass(str(snapshot["accuracy_class"]))
    except ValueError:
        valid_classes = [c.value for c in AccuracyClass]
        raise ConfigurationValidationError(
            f"Invalid accuracy class: {snapshot['accuracy_class']}. Must be one of {valid_classes}"
        )

    # 2. Supported unit
    if "unit" not in snapshot or not snapshot["unit"]:
        raise ConfigurationValidationError("Missing required configuration attribute: 'unit'")
    unit = str(snapshot["unit"]).lower()
    if unit not in UNIT_RATIOS_TO_GRAM:
        raise ConfigurationValidationError(
            f"Unsupported unit: '{snapshot['unit']}'. Supported units: {sorted(list(UNIT_RATIOS_TO_GRAM.keys()))}"
        )

    # 3. Max capacity > 0
    if "max_capacity" not in snapshot or snapshot["max_capacity"] is None:
        raise ConfigurationValidationError("Missing required configuration attribute: 'max_capacity'")
    try:
        max_cap = Decimal(str(snapshot["max_capacity"]))
    except Exception:
        raise ConfigurationValidationError(f"Invalid max_capacity: '{snapshot['max_capacity']}'. Must be a valid decimal.")
    if max_cap <= Decimal("0"):
        raise ConfigurationValidationError(f"max_capacity must be strictly positive (> 0), got {max_cap}")

    # 4. Min capacity > 0 and Min <= Max
    if "min_capacity" not in snapshot or snapshot["min_capacity"] is None:
        raise ConfigurationValidationError("Missing required configuration attribute: 'min_capacity'")
    try:
        min_cap = Decimal(str(snapshot["min_capacity"]))
    except Exception:
        raise ConfigurationValidationError(f"Invalid min_capacity: '{snapshot['min_capacity']}'. Must be a valid decimal.")
    if min_cap <= Decimal("0"):
        raise ConfigurationValidationError(f"min_capacity must be strictly positive (> 0), got {min_cap}")
    if min_cap > max_cap:
        raise ConfigurationValidationError(f"min_capacity ({min_cap}) cannot exceed max_capacity ({max_cap})")

    # 5. Verification scale interval e > 0
    if "verification_scale_interval" not in snapshot or snapshot["verification_scale_interval"] is None:
        raise ConfigurationValidationError("Missing required configuration attribute: 'verification_scale_interval'")
    try:
        e_val = Decimal(str(snapshot["verification_scale_interval"]))
    except Exception:
        raise ConfigurationValidationError(
            f"Invalid verification_scale_interval: '{snapshot['verification_scale_interval']}'. Must be a valid decimal."
        )
    if e_val <= Decimal("0"):
        raise ConfigurationValidationError(f"verification_scale_interval must be strictly positive (> 0), got {e_val}")

    # 6. Actual scale interval d > 0 and d <= e
    if "actual_scale_interval" not in snapshot or snapshot["actual_scale_interval"] is None:
        raise ConfigurationValidationError("Missing required configuration attribute: 'actual_scale_interval'")
    try:
        d_val = Decimal(str(snapshot["actual_scale_interval"]))
    except Exception:
        raise ConfigurationValidationError(
            f"Invalid actual_scale_interval: '{snapshot['actual_scale_interval']}'. Must be a valid decimal."
        )
    if d_val <= Decimal("0"):
        raise ConfigurationValidationError(f"actual_scale_interval must be strictly positive (> 0), got {d_val}")
    if d_val > e_val:
        raise ConfigurationValidationError(f"actual_scale_interval d ({d_val}) cannot exceed verification_scale_interval e ({e_val})")

    # 7. Electronic flag - must be strict boolean (True or False), NOT string or int
    if "is_electronic" not in snapshot or snapshot["is_electronic"] is None:
        raise ConfigurationValidationError("Missing required configuration attribute: 'is_electronic'")
    if not isinstance(snapshot["is_electronic"], bool):
        raise ConfigurationValidationError(
            f"'is_electronic' must be a strict boolean (True or False), got {type(snapshot['is_electronic']).__name__}: '{snapshot['is_electronic']}'"
        )

    # 8. Multiple-range consistency - must be strict boolean if present
    if "is_multiple_range" in snapshot and snapshot["is_multiple_range"] is not None:
        if not isinstance(snapshot["is_multiple_range"], bool):
            raise ConfigurationValidationError(
                f"'is_multiple_range' must be a strict boolean (True or False), got {type(snapshot['is_multiple_range']).__name__}: '{snapshot['is_multiple_range']}'"
            )
    is_mr = snapshot.get("is_multiple_range", False)

    # 9. Zero-setting flag - must be strict boolean if present
    if "has_zero_setting" in snapshot and snapshot["has_zero_setting"] is not None:
        if not isinstance(snapshot["has_zero_setting"], bool):
            raise ConfigurationValidationError(
                f"'has_zero_setting' must be a strict boolean (True or False), got {type(snapshot['has_zero_setting']).__name__}: '{snapshot['has_zero_setting']}'"
            )
    if is_mr:
        ranges = snapshot.get("ranges")
        if not ranges or not isinstance(ranges, list):
            raise ConfigurationValidationError("Multiple-range configuration must provide a non-empty 'ranges' list")
        if len(ranges) < 2:
            raise ConfigurationValidationError(f"Multiple-range configuration requires at least 2 ranges, got {len(ranges)}")
        num_ranges = snapshot.get("number_of_ranges")
        if num_ranges is not None and int(num_ranges) != len(ranges):
            raise ConfigurationValidationError(
                f"Multiple-range inconsistency: number_of_ranges is {num_ranges} but {len(ranges)} range entries provided"
            )

        seen_indices = set()
        prev_max = Decimal("-1")
        for idx, r in enumerate(ranges):
            r_idx = r.get("range_index")
            if r_idx is None:
                raise ConfigurationValidationError(f"Range entry at index {idx} missing 'range_index'")
            try:
                r_idx_int = int(r_idx)
            except (ValueError, TypeError):
                raise ConfigurationValidationError(f"Invalid range_index '{r_idx}' at index {idx}")
            if r_idx_int in seen_indices:
                raise ConfigurationValidationError(f"Duplicate range_index {r_idx_int} in multiple-range configuration")
            seen_indices.add(r_idx_int)

            for req_field in ("max_capacity", "min_capacity", "verification_scale_interval", "actual_scale_interval"):
                if req_field not in r or r[req_field] is None:
                    raise ConfigurationValidationError(f"Range {r_idx_int} missing required field '{req_field}'")

            try:
                r_max = Decimal(str(r["max_capacity"]))
                r_min = Decimal(str(r["min_capacity"]))
                r_e = Decimal(str(r["verification_scale_interval"]))
                r_d = Decimal(str(r["actual_scale_interval"]))
            except Exception as ex:
                raise ConfigurationValidationError(f"Range {r_idx_int} contains invalid decimal values: {ex}")

            if r_max <= Decimal("0") or r_min <= Decimal("0") or r_e <= Decimal("0") or r_d <= Decimal("0"):
                raise ConfigurationValidationError(f"Range {r_idx_int} values (Max, Min, e, d) must be strictly positive")
            if r_min > r_max:
                raise ConfigurationValidationError(f"Range {r_idx_int} min_capacity ({r_min}) exceeds max_capacity ({r_max})")
            if r_d > r_e:
                raise ConfigurationValidationError(
                    f"Range {r_idx_int} actual_scale_interval d ({r_d}) exceeds verification_scale_interval e ({r_e})"
                )
            if "unit" in r and str(r["unit"]).lower() not in UNIT_RATIOS_TO_GRAM:
                raise ConfigurationValidationError(f"Range {r_idx_int} has unsupported unit: '{r['unit']}'")

            if r_max <= prev_max:
                raise ConfigurationValidationError(
                    f"Multiple-range capacities must be strictly increasing: range {r_idx_int} Max ({r_max}) <= previous Max ({prev_max})"
                )
            prev_max = r_max


def determine_eccentricity_procedure(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Determine the OIML R 76-1:2006 clause A.4.7 eccentricity procedure from load receptor configuration.
    
    Reads load_receptor metadata from extra_capabilities (or top-level snapshot):
    {
      "load_receptor": {
        "support_count": 4,
        "special_receptor": false,
        "rolling_load": false
      }
    }
    """
    extra_caps = snapshot.get("extra_capabilities") or {}
    load_rec = extra_caps.get("load_receptor") or snapshot.get("load_receptor")
    
    if not load_rec or not isinstance(load_rec, dict):
        return {
            "status": "UNSUPPORTED",
            "procedure": None,
            "positions": [],
            "reason": "Missing required 'load_receptor' geometry metadata in configuration extra_capabilities.",
        }

    special_receptor = bool(load_rec.get("special_receptor", False))
    rolling_load = bool(load_rec.get("rolling_load", False))
    support_count_raw = load_rec.get("support_count")

    # CASE 4: Rolling load (clause A.4.7.4)
    if rolling_load:
        return {
            "status": "SUPPORTED",
            "procedure": "ROLLING_LOAD",
            "positions": ["ROLL_BEGIN", "ROLL_MIDDLE", "ROLL_END"],
            "support_count": int(support_count_raw) if support_count_raw is not None else 4,
            "reverse_direction_supported": bool(load_rec.get("reverse_direction", False)),
        }

    # CASE 3: Special receptor supports
    if special_receptor:
        if support_count_raw is None:
            return {
                "status": "UNSUPPORTED",
                "procedure": None,
                "positions": [],
                "reason": "Special receptor requires a positive support_count.",
            }
        try:
            support_count = int(support_count_raw)
            if support_count < 1:
                raise ValueError()
        except (ValueError, TypeError):
            return {
                "status": "UNSUPPORTED",
                "procedure": None,
                "positions": [],
                "reason": f"Invalid support_count '{support_count_raw}'. Must be an integer >= 1.",
            }
        return {
            "status": "SUPPORTED",
            "procedure": "SPECIAL_RECEPTOR_SUPPORTS",
            "positions": [f"SUPPORT_{i}" for i in range(1, support_count + 1)],
            "support_count": support_count,
        }

    # Standard receptor: requires support_count
    if support_count_raw is None:
        return {
            "status": "UNSUPPORTED",
            "procedure": None,
            "positions": [],
            "reason": "Missing 'support_count' in load_receptor geometry metadata.",
        }

    try:
        support_count = int(support_count_raw)
        if support_count < 1:
            raise ValueError()
    except (ValueError, TypeError):
        return {
            "status": "UNSUPPORTED",
            "procedure": None,
            "positions": [],
            "reason": f"Invalid support_count '{support_count_raw}'. Must be an integer >= 1.",
        }

    # CASE 1: support_count <= 4 -> FOUR_QUARTER_SEGMENTS (clause A.4.7.1)
    if support_count <= 4:
        return {
            "status": "SUPPORTED",
            "procedure": "FOUR_QUARTER_SEGMENTS",
            "positions": ["QUARTER_1", "QUARTER_2", "QUARTER_3", "QUARTER_4"],
            "support_count": support_count,
        }
    else:
        # CASE 2: support_count > 4 -> SUPPORT_SPECIFIC (clause A.4.7.2)
        return {
            "status": "SUPPORTED",
            "procedure": "SUPPORT_SPECIFIC",
            "positions": [f"SUPPORT_{i}" for i in range(1, support_count + 1)],
            "support_count": support_count,
        }


def calculate_required_eccentricity_load(
    snapshot: Dict[str, Any],
    procedure_info: Optional[Dict[str, Any]] = None,
) -> Decimal:
    """Calculate the authoritative OIML R 76-1:2006 required eccentricity test load.
    
    Under clause A.4.7.1 / A.4.7.2:
        eccentricity_load = (Max + maximum_additive_tare_effect) / (N - 1)
    For ordinary receptor with N <= 4 (FOUR_QUARTER_SEGMENTS), fraction is 1/3:
        eccentricity_load = (Max + maximum_additive_tare_effect) / 3
    For support-specific receptor with N > 4:
        eccentricity_load = (Max + maximum_additive_tare_effect) / (N - 1)
    For rolling load:
        eccentricity_load = (Max + maximum_additive_tare_effect) / 3
    
    If no additive tare exists:
        maximum_additive_tare_effect = 0
    """
    max_cap = Decimal(str(snapshot["max_capacity"]))
    extra_caps = snapshot.get("extra_capabilities") or {}
    
    additive_tare = Decimal("0")
    tare_raw = snapshot.get("maximum_additive_tare_effect") or extra_caps.get("maximum_additive_tare_effect")
    if tare_raw is not None:
        try:
            additive_tare = Decimal(str(tare_raw))
        except Exception:
            pass

    if procedure_info is None:
        procedure_info = determine_eccentricity_procedure(snapshot)

    procedure = procedure_info.get("procedure")
    support_count = procedure_info.get("support_count", 4)

    if procedure == "FOUR_QUARTER_SEGMENTS":
        return (max_cap + additive_tare) / Decimal("3")
    elif procedure in ("SUPPORT_SPECIFIC", "SPECIAL_RECEPTOR_SUPPORTS"):
        denominator = Decimal(str(support_count - 1)) if support_count > 1 else Decimal("1")
        return (max_cap + additive_tare) / denominator
    elif procedure == "ROLLING_LOAD":
        return (max_cap + additive_tare) / Decimal("3")
    else:
        return (max_cap + additive_tare) / Decimal("3")


class ApplicableTestItem:
    """Represents a generated test evaluation requirement."""

    def __init__(
        self,
        test_code: str,
        title: str,
        r76_reference: str,
        applicable: bool,
        reason: str,
        implementation_status: ImplementationStatus,
        scope_type: ScopeType = ScopeType.INSTRUMENT,
        sequence: int = 10,
        range_index: Optional[int] = None,
        range_reference: Optional[str] = None,
    ):
        self.test_code = test_code
        self.title = title
        self.r76_reference = r76_reference
        self.applicable = applicable
        self.reason = reason
        self.implementation_status = implementation_status
        self.scope_type = scope_type
        self.sequence = sequence
        self.range_index = range_index
        self.range_reference = range_reference

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_code": self.test_code,
            "title": self.title,
            "r76_reference": self.r76_reference,
            "applicable": self.applicable,
            "reason": self.reason,
            "implementation_status": self.implementation_status.value,
            "scope_type": self.scope_type.value,
            "sequence": self.sequence,
            "range_index": self.range_index,
            "range_reference": self.range_reference,
        }


class ApplicabilityEngine:
    """Determines applicable OIML R-76 test procedures based on configuration."""

    @classmethod
    def evaluate_plan(cls, snapshot: Dict[str, Any]) -> List[ApplicableTestItem]:
        """Evaluate configuration snapshot and return complete test plan with reasoning.

        Fails closed: missing required configuration data raises ConfigurationValidationError.
        """
        # Validate configuration snapshot fail-closed
        validate_configuration_snapshot(snapshot)

        items: List[ApplicableTestItem] = []

        # Extract authoritative configuration attributes without silent fallbacks
        acc_class = AccuracyClass(str(snapshot["accuracy_class"]))
        max_cap = Decimal(str(snapshot["max_capacity"]))
        unit = str(snapshot["unit"]).lower()
        is_electronic = snapshot["is_electronic"]
        has_zero_setting = snapshot.get("has_zero_setting", False)
        tare_type = str(snapshot.get("tare_type", "NONE")).upper()
        has_tare = tare_type != "NONE"
        is_multiple_range = snapshot.get("is_multiple_range", False)
        ranges_data = snapshot.get("ranges", [])

        # Convert Max to kg for standard threshold evaluations (e.g. 100 kg endurance limit)
        max_in_kg = convert_mass(max_cap, from_unit=unit, to_unit="kg")

        seq = 10

        # 1. WEIGHING PERFORMANCE (A.4.4)
        if is_multiple_range and ranges_data:
            for r in ranges_data:
                r_idx = int(r["range_index"])
                r_ref = f"RANGE_{r_idx}"
                r_max = Decimal(str(r["max_capacity"]))
                r_unit = str(r.get("unit", unit)).lower()
                items.append(
                    ApplicableTestItem(
                        test_code=f"WEIGHING_PERFORMANCE_{r_ref}",
                        title=f"Weighing Performance — Range {r_idx} (Max {r_max} {r_unit})",
                        r76_reference="A.4.4",
                        applicable=True,
                        reason=f"Mandatory weighing performance test under OIML R 76-1:2006 A.4.4 for partial weighing range {r_idx}.",
                        implementation_status=ImplementationStatus.IMPLEMENTED,
                        scope_type=ScopeType.RANGE,
                        sequence=seq,
                        range_index=r_idx,
                        range_reference=r_ref,
                    )
                )
                seq += 5
        else:
            items.append(
                ApplicableTestItem(
                    test_code="WEIGHING_PERFORMANCE",
                    title="Weighing Performance",
                    r76_reference="A.4.4",
                    applicable=True,
                    reason="Mandatory primary error evaluation test under OIML R 76-1:2006 clause A.4.4.",
                    implementation_status=ImplementationStatus.IMPLEMENTED,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
            seq += 10

        # 2. ECCENTRICITY (A.4.7) - Configuration-Driven Procedure Selection
        ecc_proc = determine_eccentricity_procedure(snapshot)
        if ecc_proc["status"] == "SUPPORTED":
            req_load = calculate_required_eccentricity_load(snapshot, ecc_proc)
            items.append(
                ApplicableTestItem(
                    test_code="ECCENTRICITY",
                    title=f"Eccentricity Test ({ecc_proc['procedure']})",
                    r76_reference="A.4.7",
                    applicable=True,
                    reason=(
                        f"Mandatory eccentricity test under OIML R 76-1:2006 clause A.4.7 "
                        f"(Procedure: {ecc_proc['procedure']}, positions: {', '.join(ecc_proc['positions'])}, "
                        f"required load: {req_load} {unit})."
                    ),
                    implementation_status=ImplementationStatus.IMPLEMENTED,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        else:
            items.append(
                ApplicableTestItem(
                    test_code="ECCENTRICITY",
                    title="Eccentricity Test",
                    r76_reference="A.4.7",
                    applicable=False,
                    reason=f"BLOCKED: Eccentricity procedure cannot be determined. {ecc_proc.get('reason', 'Missing geometry metadata')}.",
                    implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        seq += 10

        # 3. REPEATABILITY (A.4.10)
        items.append(
            ApplicableTestItem(
                test_code="REPEATABILITY",
                title="Repeatability Test",
                r76_reference="A.4.10",
                applicable=True,
                reason="Mandatory repeatability test under clause A.4.10 (series at ~50% Max and ~100% Max).",
                implementation_status=ImplementationStatus.IMPLEMENTED,
                scope_type=ScopeType.INSTRUMENT,
                sequence=seq,
            )
        )
        seq += 10

        # 4. TARE TEST (A.4.6)
        if has_tare:
            items.append(
                ApplicableTestItem(
                    test_code="TARE",
                    title="Tare Balancing & Weighing",
                    r76_reference="A.4.6",
                    applicable=True,
                    reason=f"Applicable because instrument is configured with {tare_type} tare facility under clause A.4.6.",
                    implementation_status=ImplementationStatus.PARTIAL,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        else:
            items.append(
                ApplicableTestItem(
                    test_code="TARE",
                    title="Tare Balancing & Weighing",
                    r76_reference="A.4.6",
                    applicable=False,
                    reason="Inapplicable: instrument has no tare mechanism configured (tare_type is NONE).",
                    implementation_status=ImplementationStatus.PARTIAL,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        seq += 10

        # 5. ZERO SETTING & ZERO RETURN (A.4.2 / 3.9.4.2)
        if has_zero_setting:
            items.append(
                ApplicableTestItem(
                    test_code="ZERO_SETTING",
                    title="Zero-Setting Range & Accuracy",
                    r76_reference="A.4.2",
                    applicable=True,
                    reason="Applicable because zero-setting device is enabled under clause A.4.2.",
                    implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        else:
            items.append(
                ApplicableTestItem(
                    test_code="ZERO_SETTING",
                    title="Zero-Setting Range & Accuracy",
                    r76_reference="A.4.2",
                    applicable=False,
                    reason="Inapplicable: instrument has no zero-setting device configured.",
                    implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        seq += 10

        # 6. CREEP TEST (3.9.4.1 / A.4.11.1)
        if acc_class in (AccuracyClass.CLASS_II, AccuracyClass.CLASS_III, AccuracyClass.CLASS_IIII):
            items.append(
                ApplicableTestItem(
                    test_code="CREEP",
                    title="Creep Test",
                    r76_reference="3.9.4.1 / A.4.11.1",
                    applicable=True,
                    reason=f"Applicable to {acc_class.value} instruments under clause 3.9.4.1 (load kept on receptor for 30 minutes).",
                    implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        else:
            items.append(
                ApplicableTestItem(
                    test_code="CREEP",
                    title="Creep Test",
                    r76_reference="3.9.4.1 / A.4.11.1",
                    applicable=False,
                    reason="Inapplicable: Creep requirements under 3.9.4 apply to classes II, III, and IIII only.",
                    implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        seq += 10

        # 7. TEMPERATURE INFLUENCE (A.5.3.1)
        items.append(
            ApplicableTestItem(
                test_code="TEMPERATURE",
                title="Static Temperatures Test",
                r76_reference="A.5.3.1",
                applicable=True,
                reason="Standard climatic influence factor evaluation under clause A.5.3.1.",
                implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                scope_type=ScopeType.INSTRUMENT,
                sequence=seq,
            )
        )
        seq += 10

        # 8. VOLTAGE VARIATIONS (A.5.4)
        if is_electronic:
            items.append(
                ApplicableTestItem(
                    test_code="VOLTAGE_VARIATION",
                    title="Voltage Variations Test",
                    r76_reference="A.5.4",
                    applicable=True,
                    reason="Applicable to electronic weighing instruments under clause A.5.4.",
                    implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        else:
            items.append(
                ApplicableTestItem(
                    test_code="VOLTAGE_VARIATION",
                    title="Voltage Variations Test",
                    r76_reference="A.5.4",
                    applicable=False,
                    reason="Inapplicable: Instrument is mechanical / non-electronic.",
                    implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        seq += 10

        # 9. WARM-UP TEST (A.5.2)
        if is_electronic:
            items.append(
                ApplicableTestItem(
                    test_code="WARM_UP",
                    title="Warm-up Test",
                    r76_reference="A.5.2",
                    applicable=True,
                    reason="Applicable to electronic instruments with mains/battery power under clause A.5.2.",
                    implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        else:
            items.append(
                ApplicableTestItem(
                    test_code="WARM_UP",
                    title="Warm-up Test",
                    r76_reference="A.5.2",
                    applicable=False,
                    reason="Inapplicable: Instrument is mechanical / non-electronic.",
                    implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        seq += 10

        # 10. ENDURANCE TEST (3.9.4.3 & A.6)
        # Authoritative condition: Clause 3.9.4.3 & A.6 Note:
        # "Applicable only to instruments of classes II, III and IIII with Max <= 100 kg."
        if acc_class == AccuracyClass.CLASS_I:
            items.append(
                ApplicableTestItem(
                    test_code="ENDURANCE",
                    title="Endurance Test",
                    r76_reference="3.9.4.3 & A.6",
                    applicable=False,
                    reason="Inapplicable: OIML R 76-1:2006 clause 3.9.4.3 restricts endurance testing to classes II, III, and IIII only.",
                    implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        elif max_in_kg > Decimal("100"):
            items.append(
                ApplicableTestItem(
                    test_code="ENDURANCE",
                    title="Endurance Test",
                    r76_reference="3.9.4.3 & A.6",
                    applicable=False,
                    reason=f"Inapplicable: Max capacity ({max_in_kg} kg) exceeds the 100 kg threshold specified in clause 3.9.4.3.",
                    implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        else:
            items.append(
                ApplicableTestItem(
                    test_code="ENDURANCE",
                    title="Endurance Test",
                    r76_reference="3.9.4.3 & A.6",
                    applicable=True,
                    reason=f"Applicable under clause 3.9.4.3 ({acc_class.value} with Max {max_in_kg} kg <= 100 kg).",
                    implementation_status=ImplementationStatus.APPLICABILITY_ONLY,
                    scope_type=ScopeType.INSTRUMENT,
                    sequence=seq,
                )
            )
        seq += 10

        return items
