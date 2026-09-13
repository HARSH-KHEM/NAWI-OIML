"""Authoritative Maximum Permissible Error (MPE) Engine based on OIML R 76-1:2006, 3.5.1, Table 6."""

from decimal import Decimal
from typing import NamedTuple, Optional
from app.models.configuration import AccuracyClass


# Exact unit conversion ratios relative to grams (base unit for decimal conversion)
UNIT_RATIOS_TO_GRAM = {
    "kg": Decimal("1000"),
    "g": Decimal("1"),
    "mg": Decimal("0.001"),
    "t": Decimal("1000000"),
}


def normalize_to_grams(value: Decimal, unit: str) -> Decimal:
    """Normalize any mass value to grams using exact Decimal arithmetic."""
    clean_unit = unit.strip().lower()
    if clean_unit not in UNIT_RATIOS_TO_GRAM:
        raise ValueError(f"Unsupported metrological unit: {unit!r}. Supported units: kg, g, mg, t")
    return value * UNIT_RATIOS_TO_GRAM[clean_unit]


def convert_mass(value: Decimal, from_unit: str, to_unit: str) -> Decimal:
    """Convert mass from one unit to another using exact Decimal arithmetic."""
    from_u = from_unit.strip().lower()
    to_u = to_unit.strip().lower()
    if from_u == to_u:
        return value
    grams = normalize_to_grams(value, from_u)
    return grams / UNIT_RATIOS_TO_GRAM[to_u]


class MPEResult(NamedTuple):
    """Result of an authoritative R-76 MPE evaluation."""
    accuracy_class: AccuracyClass
    load_in_e: Decimal
    mpe_factor: Decimal               # 0.5, 1.0, or 1.5 intervals
    mpe_mass: Decimal                 # Absolute MPE in the instrument's unit
    unit: str
    band_lower_e: Decimal
    band_upper_e: Optional[Decimal]
    r76_reference: str


class MPEEngine:
    """Authoritative single source of truth for OIML R-76 Table 6 MPE determination.
    
    Ref: OIML R 76-1:2006 (E), Section 3.5.1, Table 6.
    All calculations use Decimal arithmetic. Floating-point arithmetic is prohibited.
    """

    @classmethod
    def calculate_mpe(
        cls,
        accuracy_class: AccuracyClass,
        load: Decimal,
        e: Decimal,
        load_unit: str = "kg",
        e_unit: str = "kg",
    ) -> MPEResult:
        """Calculate the maximum permissible error for a given load and verification scale interval e.
        
        Args:
            accuracy_class: OIML accuracy class (CLASS_I, CLASS_II, CLASS_III, CLASS_IIII)
            load: Test load applied (L)
            e: Verification scale interval (e)
            load_unit: Unit of measurement for load
            e_unit: Unit of measurement for verification scale interval
            
        Returns:
            MPEResult with exact MPE in intervals and mass.
        """
        if e <= Decimal("0"):
            raise ValueError("Verification scale interval e must be strictly positive")
        if load < Decimal("0"):
            raise ValueError("Load cannot be negative")

        # Convert load to the same unit as e
        load_normalized = convert_mass(load, from_unit=load_unit, to_unit=e_unit)
        m = load_normalized / e  # Load expressed in verification scale intervals (m = L / e)

        # Apply Table 6 criteria based on accuracy class
        if accuracy_class == AccuracyClass.CLASS_I:
            # Class I:
            # 0 <= m <= 50 000        -> +/- 0.5 e
            # 50 000 < m <= 200 000    -> +/- 1.0 e
            # 200 000 < m              -> +/- 1.5 e
            if m <= Decimal("50000"):
                factor = Decimal("0.5")
                lower_e = Decimal("0")
                upper_e = Decimal("50000")
            elif m <= Decimal("200000"):
                factor = Decimal("1.0")
                lower_e = Decimal("50000")
                upper_e = Decimal("200000")
            else:
                factor = Decimal("1.5")
                lower_e = Decimal("200000")
                upper_e = None

        elif accuracy_class == AccuracyClass.CLASS_II:
            # Class II:
            # 0 <= m <= 5 000          -> +/- 0.5 e
            # 5 000 < m <= 20 000      -> +/- 1.0 e
            # 20 000 < m <= 100 000    -> +/- 1.5 e
            if m <= Decimal("5000"):
                factor = Decimal("0.5")
                lower_e = Decimal("0")
                upper_e = Decimal("5000")
            elif m <= Decimal("20000"):
                factor = Decimal("1.0")
                lower_e = Decimal("5000")
                upper_e = Decimal("20000")
            elif m <= Decimal("100000"):
                factor = Decimal("1.5")
                lower_e = Decimal("20000")
                upper_e = Decimal("100000")
            else:
                raise ValueError(
                    f"Load {load} {load_unit} ({m:.4f} e) exceeds maximum Table 6 boundary (100000 e) for accuracy class {accuracy_class.value}"
                )

        elif accuracy_class == AccuracyClass.CLASS_III:
            # Class III:
            # 0 <= m <= 500            -> +/- 0.5 e
            # 500 < m <= 2 000         -> +/- 1.0 e
            # 2 000 < m <= 10 000      -> +/- 1.5 e
            if m <= Decimal("500"):
                factor = Decimal("0.5")
                lower_e = Decimal("0")
                upper_e = Decimal("500")
            elif m <= Decimal("2000"):
                factor = Decimal("1.0")
                lower_e = Decimal("500")
                upper_e = Decimal("2000")
            elif m <= Decimal("10000"):
                factor = Decimal("1.5")
                lower_e = Decimal("2000")
                upper_e = Decimal("10000")
            else:
                raise ValueError(
                    f"Load {load} {load_unit} ({m:.4f} e) exceeds maximum Table 6 boundary (10000 e) for accuracy class {accuracy_class.value}"
                )

        elif accuracy_class == AccuracyClass.CLASS_IIII:
            # Class IIII:
            # 0 <= m <= 50             -> +/- 0.5 e
            # 50 < m <= 200            -> +/- 1.0 e
            # 200 < m <= 1 000         -> +/- 1.5 e
            if m <= Decimal("50"):
                factor = Decimal("0.5")
                lower_e = Decimal("0")
                upper_e = Decimal("50")
            elif m <= Decimal("200"):
                factor = Decimal("1.0")
                lower_e = Decimal("50")
                upper_e = Decimal("200")
            elif m <= Decimal("1000"):
                factor = Decimal("1.5")
                lower_e = Decimal("200")
                upper_e = Decimal("1000")
            else:
                raise ValueError(
                    f"Load {load} {load_unit} ({m:.4f} e) exceeds maximum Table 6 boundary (1000 e) for accuracy class {accuracy_class.value}"
                )
        else:
            raise ValueError(f"Unknown accuracy class: {accuracy_class}")

        mpe_mass = factor * e
        return MPEResult(
            accuracy_class=accuracy_class,
            load_in_e=m,
            mpe_factor=factor,
            mpe_mass=mpe_mass,
            unit=e_unit,
            band_lower_e=lower_e,
            band_upper_e=upper_e,
            r76_reference="OIML R 76-1:2006, 3.5.1, Table 6",
        )
