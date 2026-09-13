"""Unit tests for ApplicabilityEngine under OIML R 76-1:2006.

Verifies:
- Class III <= 100kg: Endurance applicable
- Class I: Endurance inapplicable (clause 3.9.4.3)
- Class III > 100kg: Endurance inapplicable (clause 3.9.4.3)
- Tare enabled vs disabled
- Single-range vs Multiple-range plan generation
"""

from decimal import Decimal
import pytest
from app.engines.applicability import ApplicabilityEngine
from app.models.test_definition import ImplementationStatus, ScopeType


def test_applicability_class_iii_30kg():
    """Class III, 30 kg NAWI should have Weighing, Eccentricity, Repeatability, and Endurance applicable."""
    snapshot = {
        "accuracy_class": "CLASS_III",
        "max_capacity": "30",
        "min_capacity": "0.2",
        "verification_scale_interval": "0.01",
        "actual_scale_interval": "0.01",
        "unit": "kg",
        "is_electronic": True,
        "has_zero_setting": True,
        "tare_type": "SUBTRACTIVE",
        "is_multiple_range": False,
        "ranges": [],
        "extra_capabilities": {
            "load_receptor": {
                "support_count": 4,
                "special_receptor": False,
                "rolling_load": False,
            }
        },
    }

    plan = ApplicabilityEngine.evaluate_plan(snapshot)
    items_by_code = {item.test_code: item for item in plan}

    # Authoritative mandatory performance tests
    assert "WEIGHING_PERFORMANCE" in items_by_code
    assert items_by_code["WEIGHING_PERFORMANCE"].applicable is True
    assert items_by_code["WEIGHING_PERFORMANCE"].implementation_status == ImplementationStatus.IMPLEMENTED

    assert "ECCENTRICITY" in items_by_code
    assert items_by_code["ECCENTRICITY"].applicable is True

    assert "REPEATABILITY" in items_by_code
    assert items_by_code["REPEATABILITY"].applicable is True

    # Tare facility enabled
    assert "TARE" in items_by_code
    assert items_by_code["TARE"].applicable is True

    # Endurance test: Class III and Max <= 100 kg -> APPLICABLE
    assert "ENDURANCE" in items_by_code
    assert items_by_code["ENDURANCE"].applicable is True
    assert "3.9.4.3" in items_by_code["ENDURANCE"].r76_reference
    assert items_by_code["ENDURANCE"].implementation_status == ImplementationStatus.APPLICABILITY_ONLY


def test_applicability_class_i_endurance_inapplicable():
    """Class I instruments are exempt from endurance testing per OIML R 76-1 clause 3.9.4.3."""
    snapshot = {
        "accuracy_class": "CLASS_I",
        "max_capacity": "30",
        "min_capacity": "0.001",
        "verification_scale_interval": "0.0001",
        "actual_scale_interval": "0.0001",
        "unit": "kg",
        "is_electronic": True,
        "tare_type": "SUBTRACTIVE",
        "is_multiple_range": False,
    }

    plan = ApplicabilityEngine.evaluate_plan(snapshot)
    items_by_code = {item.test_code: item for item in plan}

    assert "ENDURANCE" in items_by_code
    assert items_by_code["ENDURANCE"].applicable is False
    assert "classes II, III, and IIII only" in items_by_code["ENDURANCE"].reason


def test_applicability_class_iii_above_100kg_endurance_inapplicable():
    """Class III instruments with Max > 100 kg are exempt from endurance testing per clause 3.9.4.3."""
    snapshot = {
        "accuracy_class": "CLASS_III",
        "max_capacity": "150",
        "min_capacity": "1.0",
        "verification_scale_interval": "0.05",
        "actual_scale_interval": "0.05",
        "unit": "kg",
        "is_electronic": True,
        "tare_type": "SUBTRACTIVE",
        "is_multiple_range": False,
    }

    plan = ApplicabilityEngine.evaluate_plan(snapshot)
    items_by_code = {item.test_code: item for item in plan}

    assert "ENDURANCE" in items_by_code
    assert items_by_code["ENDURANCE"].applicable is False
    assert "100 kg threshold" in items_by_code["ENDURANCE"].reason


def test_applicability_tare_disabled():
    """When tare_type is NONE, Tare test must be evaluated as NOT applicable."""
    snapshot = {
        "accuracy_class": "CLASS_III",
        "max_capacity": "30",
        "min_capacity": "0.2",
        "verification_scale_interval": "0.01",
        "actual_scale_interval": "0.01",
        "unit": "kg",
        "is_electronic": True,
        "tare_type": "NONE",
        "is_multiple_range": False,
    }

    plan = ApplicabilityEngine.evaluate_plan(snapshot)
    items_by_code = {item.test_code: item for item in plan}

    assert "TARE" in items_by_code
    assert items_by_code["TARE"].applicable is False
    assert "no tare mechanism" in items_by_code["TARE"].reason.lower()


def test_applicability_mechanical_warmup_and_voltage_inapplicable():
    """Non-electronic (mechanical) instruments do not require Warm-up or Voltage variation tests."""
    snapshot = {
        "accuracy_class": "CLASS_III",
        "max_capacity": "30",
        "min_capacity": "0.2",
        "verification_scale_interval": "0.01",
        "actual_scale_interval": "0.01",
        "unit": "kg",
        "is_electronic": False,
        "is_multiple_range": False,
    }

    plan = ApplicabilityEngine.evaluate_plan(snapshot)
    items_by_code = {item.test_code: item for item in plan}

    assert items_by_code["VOLTAGE_VARIATION"].applicable is False
    assert items_by_code["WARM_UP"].applicable is False


def test_applicability_multiple_range_expansion():
    """A multi-range instrument expands Weighing Performance into range-specific items."""
    snapshot = {
        "accuracy_class": "CLASS_III",
        "max_capacity": "30",
        "min_capacity": "0.2",
        "verification_scale_interval": "0.01",
        "actual_scale_interval": "0.01",
        "unit": "kg",
        "is_electronic": True,
        "is_multiple_range": True,
        "ranges": [
            {
                "range_index": 1,
                "min_capacity": "0.2",
                "max_capacity": "15",
                "verification_scale_interval": "0.005",
                "actual_scale_interval": "0.005",
                "unit": "kg",
            },
            {
                "range_index": 2,
                "min_capacity": "15",
                "max_capacity": "30",
                "verification_scale_interval": "0.010",
                "actual_scale_interval": "0.010",
                "unit": "kg",
            },
        ],
    }

    plan = ApplicabilityEngine.evaluate_plan(snapshot)
    codes = [item.test_code for item in plan]

    # Verify generic WEIGHING_PERFORMANCE is NOT present, replaced by range items
    assert "WEIGHING_PERFORMANCE" not in codes
    assert "WEIGHING_PERFORMANCE_RANGE_1" in codes
    assert "WEIGHING_PERFORMANCE_RANGE_2" in codes

    range1_item = next(item for item in plan if item.test_code == "WEIGHING_PERFORMANCE_RANGE_1")
    assert range1_item.scope_type == ScopeType.RANGE
    assert range1_item.range_index == 1
    assert range1_item.range_reference == "RANGE_1"
    assert "Range 1 (Max 15 kg)" in range1_item.title
    assert range1_item.applicable is True

    range2_item = next(item for item in plan if item.test_code == "WEIGHING_PERFORMANCE_RANGE_2")
    assert range2_item.scope_type == ScopeType.RANGE
    assert range2_item.range_index == 2
    assert range2_item.range_reference == "RANGE_2"
    assert "Range 2 (Max 30 kg)" in range2_item.title
    assert range2_item.applicable is True
