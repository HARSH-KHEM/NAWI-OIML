"""Integration tests for Report generation and Test Definitions API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.rule import Rule, RuleVersion
from app.models.user import User, UserRole


@pytest.fixture
def test_setup(db_session: Session):
    """Seed prerequisite user and rule version in test DB."""
    user = User(email="report_tester@test.com", full_name="Report Evaluator", role=UserRole.LAB_ADMIN)
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


def test_list_test_definitions(client: TestClient, test_setup):
    """Verify GET /api/v1/test-definitions returns canonical test definitions."""
    # First ensure test definitions exist via generate-plan on any evaluation or seed
    # Create instrument & evaluation to trigger test definition initialization
    inst = client.post(
        "/api/v1/instruments",
        json={
            "manufacturer": "Test Lab",
            "model_name": "T-100",
            "instrument_family": "NAWI",
            "serial_number": "TD-001",
            "is_synthetic": True,
        },
    ).json()
    cfg = client.post(
        f"/api/v1/instruments/{inst['id']}/configurations",
        json={
            "accuracy_class": "CLASS_III",
            "max_capacity": "30.0",
            "min_capacity": "0.2",
            "verification_scale_interval": "0.01",
            "actual_scale_interval": "0.01",
            "unit": "kg",
            "number_of_ranges": 1,
            "is_multiple_range": False,
            "tare_type": "SUBTRACTIVE",
            "is_electronic": True,
            "has_zero_setting": True,
        },
    ).json()
    ev = client.post(
        f"/api/v1/instruments/{inst['id']}/evaluations",
        json={"instrument_configuration_id": cfg["id"]},
    ).json()
    client.post(f"/api/v1/evaluations/{ev['id']}/generate-plan")

    resp = client.get("/api/v1/test-definitions")
    assert resp.status_code == 200
    defs = resp.json()
    assert len(defs) >= 10
    codes = [d["test_code"] for d in defs]
    assert "WEIGHING_PERFORMANCE" in codes
    assert "ECCENTRICITY" in codes
    assert "REPEATABILITY" in codes


def test_get_evaluation_report(client: TestClient, test_setup):
    """Verify GET /api/v1/evaluations/{id}/report aggregates consistent report data."""
    # 1. Create Instrument
    inst = client.post(
        "/api/v1/instruments",
        json={
            "manufacturer": "Mettler Toledo",
            "model_name": "MT-600",
            "instrument_family": "NAWI",
            "serial_number": "REP-SN-001",
            "is_synthetic": True,
        },
    ).json()

    # 2. Attach Configuration
    cfg = client.post(
        f"/api/v1/instruments/{inst['id']}/configurations",
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
    ).json()

    # 3. Create Evaluation
    ev = client.post(
        f"/api/v1/instruments/{inst['id']}/evaluations",
        json={"instrument_configuration_id": cfg["id"], "lab_name": "Test Metrology Authority"},
    ).json()
    eval_id = ev["id"]

    # 4. Generate Plan
    plan_resp = client.post(f"/api/v1/evaluations/{eval_id}/generate-plan")
    assert plan_resp.status_code == 200
    plan = plan_resp.json()

    # 5. Fetch Report (before tests executed -> IN_PROGRESS)
    rep_resp = client.get(f"/api/v1/evaluations/{eval_id}/report")
    assert rep_resp.status_code == 200
    rep = rep_resp.json()

    assert rep["evaluation_id"] == eval_id
    assert rep["evaluation_number"] == ev["evaluation_number"]
    assert rep["instrument_model"] == "MT-600"
    assert rep["instrument_serial"] == "REP-SN-001"
    assert rep["accuracy_class"] == "CLASS_III"
    assert float(rep["max_capacity"]) == 30.0
    assert rep["total_procedures"] == plan["total_tests"]
    assert rep["applicable_procedures"] == plan["applicable_tests_count"]
    assert rep["overall_compliance"] == "IN_PROGRESS"
    assert rep["document_hash"].startswith("sha256:")
    assert len(rep["procedures"]) == plan["total_tests"]

    # 6. Record observation and calculation for WEIGHING_PERFORMANCE
    wp_test = next(t for t in plan["tests"] if t["test_code"] == "WEIGHING_PERFORMANCE")
    test_detail = client.get(f"/api/v1/evaluation-tests/{wp_test['id']}").json()
    att_id = test_detail["attempts"][0]["id"]

    # Submit passing observations
    client.post(f"/api/v1/test-attempts/{att_id}/observations", json={"observation_code": "LOAD", "value_numeric": "10.00", "unit": "kg"})
    client.post(f"/api/v1/test-attempts/{att_id}/observations", json={"observation_code": "INDICATION", "value_numeric": "10.00", "unit": "kg"})
    client.post(f"/api/v1/test-attempts/{att_id}/observations", json={"observation_code": "ADDITIONAL_LOAD", "value_numeric": "0.005", "unit": "kg"})
    client.post(f"/api/v1/test-attempts/{att_id}/observations", json={"observation_code": "ZERO_ERROR", "value_numeric": "0.000", "unit": "kg"})
    calc_res = client.post(f"/api/v1/test-attempts/{att_id}/calculate").json()
    assert calc_res["compliance"]["decision"] == "PASS"

    # 7. Fetch Report again
    rep_resp2 = client.get(f"/api/v1/evaluations/{eval_id}/report")
    assert rep_resp2.status_code == 200
    rep2 = rep_resp2.json()
    assert rep2["passed_procedures"] == 1
    wp_rep_item = next(p for p in rep2["procedures"] if p["test_code"] == "WEIGHING_PERFORMANCE")
    assert wp_rep_item["latest_decision"] == "PASS"
    assert wp_rep_item["attempt_count"] == 1
