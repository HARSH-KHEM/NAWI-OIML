"""Tests for Authoritative MPE Engine (OIML R 76-1:2006, Section 3.5.1, Table 6)."""

from decimal import Decimal
import pytest
from app.engines.mpe import MPEEngine, convert_mass
from app.models.configuration import AccuracyClass


def test_class_iii_mpe_boundaries():
    """Verify Table 6 boundaries for Class III instruments:
    0 <= m <= 500       -> +/- 0.5 e
    500 < m <= 2 000    -> +/- 1.0 e
    2 000 < m <= 10 000 -> +/- 1.5 e
    """
    e = Decimal("0.010")  # e = 10 g = 0.01 kg

    # 1. At lower limit: m = 0
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, Decimal("0"), e, "kg", "kg")
    assert res.mpe_factor == Decimal("0.5")
    assert res.mpe_mass == Decimal("0.005")

    # 2. Exactly at upper boundary 1: m = 500 (load = 5 kg)
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, Decimal("5.000"), e, "kg", "kg")
    assert res.load_in_e == Decimal("500")
    assert res.mpe_factor == Decimal("0.5")
    assert res.mpe_mass == Decimal("0.005")

    # 3. Just above boundary 1: m = 501 (load = 5.01 kg)
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, Decimal("5.010"), e, "kg", "kg")
    assert res.load_in_e == Decimal("501")
    assert res.mpe_factor == Decimal("1.0")
    assert res.mpe_mass == Decimal("0.010")

    # 4. Exactly at upper boundary 2: m = 2000 (load = 20 kg)
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, Decimal("20.000"), e, "kg", "kg")
    assert res.load_in_e == Decimal("2000")
    assert res.mpe_factor == Decimal("1.0")
    assert res.mpe_mass == Decimal("0.010")

    # 5. Just above boundary 2: m = 2001 (load = 20.01 kg)
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, Decimal("20.010"), e, "kg", "kg")
    assert res.load_in_e == Decimal("2001")
    assert res.mpe_factor == Decimal("1.5")
    assert res.mpe_mass == Decimal("0.015")

    # 6. Near Max: m = 3000 (load = 30 kg)
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, Decimal("30.000"), e, "kg", "kg")
    assert res.load_in_e == Decimal("3000")
    assert res.mpe_factor == Decimal("1.5")
    assert res.mpe_mass == Decimal("0.015")


def test_class_i_mpe_boundaries():
    """Verify Table 6 boundaries for Class I instruments:
    0 <= m <= 50 000     -> +/- 0.5 e
    50 000 < m <= 200 000 -> +/- 1.0 e
    200 000 < m          -> +/- 1.5 e
    """
    e = Decimal("0.001")  # e = 1 mg = 0.001 g

    # m = 50 000 (load = 50 g)
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_I, Decimal("50"), e, "g", "g")
    assert res.mpe_factor == Decimal("0.5")

    # m = 50 001 (load = 50.001 g)
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_I, Decimal("50.001"), e, "g", "g")
    assert res.mpe_factor == Decimal("1.0")

    # m = 200 000 (load = 200 g)
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_I, Decimal("200"), e, "g", "g")
    assert res.mpe_factor == Decimal("1.0")

    # m = 200 001 (load = 200.001 g)
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_I, Decimal("200.001"), e, "g", "g")
    assert res.mpe_factor == Decimal("1.5")


def test_class_ii_and_iiii_boundaries():
    """Verify boundaries for Class II and Class IIII."""
    # Class II: 5000 and 20000
    e2 = Decimal("0.05")
    res_ii = MPEEngine.calculate_mpe(AccuracyClass.CLASS_II, Decimal("250"), e2, "g", "g")  # m = 5000
    assert res_ii.mpe_factor == Decimal("0.5")

    res_ii_over = MPEEngine.calculate_mpe(AccuracyClass.CLASS_II, Decimal("250.05"), e2, "g", "g")  # m = 5001
    assert res_ii_over.mpe_factor == Decimal("1.0")

    # Class IIII: 50 and 200
    e4 = Decimal("5")  # e = 5 kg
    res_iiii = MPEEngine.calculate_mpe(AccuracyClass.CLASS_IIII, Decimal("250"), e4, "kg", "kg")  # m = 50
    assert res_iiii.mpe_factor == Decimal("0.5")

    res_iiii_over = MPEEngine.calculate_mpe(AccuracyClass.CLASS_IIII, Decimal("255"), e4, "kg", "kg")  # m = 51
    assert res_iiii_over.mpe_factor == Decimal("1.0")


def test_mpe_unit_conversions():
    """Verify load in kg with e in grams converts accurately without precision loss."""
    load_kg = Decimal("2.5")  # 2.5 kg = 2500 g
    e_g = Decimal("5")        # 5 g -> m = 500
    res = MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, load_kg, e_g, "kg", "g")
    assert res.load_in_e == Decimal("500")
    assert res.mpe_factor == Decimal("0.5")
    assert res.mpe_mass == Decimal("2.5")  # 2.5 g
    assert res.unit == "g"


def test_mpe_invalid_inputs():
    """Verify strict validation on non-positive e or negative load."""
    with pytest.raises(ValueError, match="strictly positive"):
        MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, Decimal("10"), Decimal("0"))

    with pytest.raises(ValueError, match="cannot be negative"):
        MPEEngine.calculate_mpe(AccuracyClass.CLASS_III, Decimal("-5"), Decimal("0.01"))
