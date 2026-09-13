"""Integration tests for Phase 2 REST API endpoints under /api/v1.

Verifies:
- Complete workflow from Instrument -> Configuration -> Evaluation -> Plan Generation
- Observation capture and domain validation via REST
- Authoritative calculation and compliance result retrieval
- Audit traceability endpoint (/trace)
- Retest creation preserving previous attempt
- Evidence metadata attachment
- Multi-range configuration and plan expansion
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.rule import Rule, RuleVersion
from app.models.user import User, UserRole


@pytest.fixture
def test_setup(db_session: Session):
    """Seed prerequisite user and rule version in test DB."""
    user = User(email="api@test.com", full_name="API Evaluator", role=UserRole.LAB_ADMIN)
    db_session.add(user)

    rule = Rule(code="OIML_R76_2006", name="OIML R 76-1:2006", description="OIML R 76-1:2006 standard")
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
    db_session.commit()
    return {"user": user, "rule_version": rv}


def test_full_api_evaluation_workflow(client: TestClient, test_setup):
    """End-to-end integration test through the REST API."""
    # 1. Create Instrument
    inst_resp = client.post(
        "/api/v1/instruments",
        json={
            "manufacturer": "Sartorius Lab",
            "model_name": "CPA-30",
            "instrument_family": "Precision Balances",
            "serial_number": "REST-SN-001",
            "status": "DRAFT",
            "is_synthetic": True,
        },
    )
    assert inst_resp.status_code == 201, inst_resp.text
    inst_data = inst_resp.json()
    inst_id = inst_data["id"]

    # 2. Create Metrological Configuration
    config_resp = client.post(
        f"/api/v1/instruments/{inst_id}/configurations",
        json={
            "accuracy_class": "CLASS_III",
            "max_capacity": "30.000",
            "min_capacity": "0.200",
            "verification_scale_interval": "0.010",
            "actual_scale_interval": "0.010",
            "unit": "kg",
            "number_of_ranges": 1,
            "is_multiple_range": False,
            "tare_type": "SUBTRACTIVE",
            "is_electronic": True,
            "has_zero_setting": True,
        },
    )
    assert config_resp.status_code == 201, config_resp.text
    config_id = config_resp.json()["id"]

    # 3. Create Evaluation
    eval_resp = client.post(
        f"/api/v1/instruments/{inst_id}/evaluations",
        json={
            "instrument_configuration_id": config_id,
            "lab_name": "National Metrology Institute",
        },
    )
    assert eval_resp.status_code == 201, eval_resp.text
    eval_data = eval_resp.json()
    eval_id = eval_data["id"]
    assert Decimal(eval_data["configuration_snapshot"]["max_capacity"]) == Decimal("30.000")

    # 4. Generate Test Plan
    plan_resp = client.post(f"/api/v1/evaluations/{eval_id}/generate-plan")
    assert plan_resp.status_code == 200, plan_resp.text
    plan_data = plan_resp.json()
    assert plan_data["total_tests"] >= 8
    assert plan_data["applicable_tests_count"] >= 4

    # Calling generate-plan again should be idempotent
    plan_resp2 = client.post(f"/api/v1/evaluations/{eval_id}/generate-plan")
    assert plan_resp2.status_code == 200
    assert len(plan_resp2.json()["tests"]) == plan_data["total_tests"]

    # 5. Locate Weighing Performance test
    tests_resp = client.get(f"/api/v1/evaluations/{eval_id}/tests")
    assert tests_resp.status_code == 200
    tests_list = tests_resp.json()
    weighing_test = next(t for t in tests_list if t["test_code"] == "WEIGHING_PERFORMANCE")
    weighing_test_id = weighing_test["id"]

    # Inspect test details
    detail_resp = client.get(f"/api/v1/evaluation-tests/{weighing_test_id}")
    assert detail_resp.status_code == 200
    test_detail = detail_resp.json()
    assert len(test_detail["attempts"]) >= 1
    attempt1_id = test_detail["attempts"][0]["id"]

    # 6. Submit Raw Failing Observations for Attempt 1
    # Load = 10.00 kg, Indication = 10.03 kg -> Error = 0.030 kg (exceeds MPE 0.010 kg)
    client.post(
        f"/api/v1/test-attempts/{attempt1_id}/observations",
        json={"observation_code": "LOAD", "value_numeric": "10.00", "unit": "kg"},
    )
    client.post(
        f"/api/v1/test-attempts/{attempt1_id}/observations",
        json={"observation_code": "INDICATION", "value_numeric": "10.03", "unit": "kg"},
    )
    client.post(
        f"/api/v1/test-attempts/{attempt1_id}/observations",
        json={"observation_code": "ADDITIONAL_LOAD", "value_numeric": "0.005", "unit": "kg"},
    )
    client.post(
        f"/api/v1/test-attempts/{attempt1_id}/observations",
        json={"observation_code": "ZERO_ERROR", "value_numeric": "0.000", "unit": "kg"},
    )

    # 7. Execute Calculation on Attempt 1 -> FAIL
    calc_resp = client.post(f"/api/v1/test-attempts/{attempt1_id}/calculate")
    assert calc_resp.status_code == 200, calc_resp.text
    calc_data = calc_resp.json()
    assert calc_data["compliance"]["decision"] == "FAIL"

    # Get compliance result
    result_resp = client.get(f"/api/v1/test-attempts/{attempt1_id}/result")
    assert result_resp.status_code == 200
    assert result_resp.json()["decision"] == "FAIL"

    # 8. Fetch Trace for Attempt 1
    trace_resp = client.get(f"/api/v1/test-attempts/{attempt1_id}/trace")
    assert trace_resp.status_code == 200, trace_resp.text
    trace_data = trace_resp.json()
    assert trace_data["compliance"]["decision"] == "FAIL"
    assert "calculation" in trace_data
    assert len(trace_data["raw_observations"]) == 4
    assert trace_data["instrument"]["serial_number"] == "REST-SN-001"

    # 9. Create Retest (Attempt 2)
    retest_resp = client.post(
        f"/api/v1/evaluation-tests/{weighing_test_id}/attempts",
        json={"notes": "Recalibrated scale with verified standard weights."},
    )
    assert retest_resp.status_code == 201, retest_resp.text
    attempt2_data = retest_resp.json()
    attempt2_id = attempt2_data["id"]
    assert attempt2_data["attempt_number"] == 2
    assert attempt2_data["supersedes_attempt_id"] == attempt1_id

    # 10. Submit Passing Observations for Attempt 2
    # Load = 10.00 kg, Indication = 10.00 kg -> Error = 0.000 kg (within MPE 0.010 kg)
    client.post(
        f"/api/v1/test-attempts/{attempt2_id}/observations",
        json={"observation_code": "LOAD", "value_numeric": "10.00", "unit": "kg"},
    )
    client.post(
        f"/api/v1/test-attempts/{attempt2_id}/observations",
        json={"observation_code": "INDICATION", "value_numeric": "10.00", "unit": "kg"},
    )
    client.post(
        f"/api/v1/test-attempts/{attempt2_id}/observations",
        json={"observation_code": "ADDITIONAL_LOAD", "value_numeric": "0.005", "unit": "kg"},
    )
    client.post(
        f"/api/v1/test-attempts/{attempt2_id}/observations",
        json={"observation_code": "ZERO_ERROR", "value_numeric": "0.000", "unit": "kg"},
    )

    # 11. Calculate Attempt 2 -> PASS
    calc2_resp = client.post(f"/api/v1/test-attempts/{attempt2_id}/calculate")
    assert calc2_resp.status_code == 200
    assert calc2_resp.json()["compliance"]["decision"] == "PASS"

    # Verify Attempt 1 remains FAIL
    res1_check = client.get(f"/api/v1/test-attempts/{attempt1_id}/result")
    assert res1_check.status_code == 200
    assert res1_check.json()["decision"] == "FAIL"

    # 12. Upload Evidence Artifact
    ev_resp = client.post(
        f"/api/v1/test-attempts/{attempt2_id}/evidence",
        json={
            "evidence_type": "CALIBRATION_CERTIFICATE",
            "filename": "cert_standard_weights_10kg.pdf",
            "storage_key": "evidence/REST-SN-001/cert_standard_weights_10kg.pdf",
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "uploaded_by": "lab_technician",
        },
    )
    assert ev_resp.status_code == 201, ev_resp.text
    ev_id = ev_resp.json()["id"]

    # Verify evidence listed under evaluation
    ev_list_resp = client.get(f"/api/v1/evaluations/{eval_id}/evidence")
    assert ev_list_resp.status_code == 200
    assert any(e["id"] == ev_id for e in ev_list_resp.json())


def test_api_multi_range_plan_generation(client: TestClient, test_setup):
    """Multi-range configuration through API generates range-specific tests in the plan."""
    # 1. Create Instrument
    inst_resp = client.post(
        "/api/v1/instruments",
        json={
            "manufacturer": "Mettler Multi",
            "model_name": "MR-30",
            "instrument_family": "Multi-range Counter",
            "serial_number": "MR-SN-002",
            "status": "DRAFT",
            "is_synthetic": True,
        },
    )
    inst_id = inst_resp.json()["id"]

    # 2. Create Multi-range Configuration
    config_resp = client.post(
        f"/api/v1/instruments/{inst_id}/configurations",
        json={
            "accuracy_class": "CLASS_III",
            "max_capacity": "30.000",
            "min_capacity": "0.200",
            "verification_scale_interval": "0.010",
            "actual_scale_interval": "0.010",
            "unit": "kg",
            "number_of_ranges": 2,
            "is_multiple_range": True,
            "tare_type": "SUBTRACTIVE",
            "is_electronic": True,
            "has_zero_setting": True,
            "ranges": [
                {
                    "range_index": 1,
                    "min_capacity": "0.200",
                    "max_capacity": "15.000",
                    "verification_scale_interval": "0.005",
                    "actual_scale_interval": "0.005",
                    "unit": "kg",
                },
                {
                    "range_index": 2,
                    "min_capacity": "15.000",
                    "max_capacity": "30.000",
                    "verification_scale_interval": "0.010",
                    "actual_scale_interval": "0.010",
                    "unit": "kg",
                },
            ],
        },
    )
    assert config_resp.status_code == 201, config_resp.text
    config_id = config_resp.json()["id"]

    # 3. Create Evaluation and Generate Plan
    eval_resp = client.post(
        f"/api/v1/instruments/{inst_id}/evaluations",
        json={"instrument_configuration_id": config_id},
    )
    eval_id = eval_resp.json()["id"]

    plan_resp = client.post(f"/api/v1/evaluations/{eval_id}/generate-plan")
    assert plan_resp.status_code == 200, plan_resp.text
    plan_data = plan_resp.json()

    codes = [t["test_code"] for t in plan_data["tests"]]
    assert "WEIGHING_PERFORMANCE_RANGE_1" in codes
    assert "WEIGHING_PERFORMANCE_RANGE_2" in codes
    assert "WEIGHING_PERFORMANCE" not in codes
