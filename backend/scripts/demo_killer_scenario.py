"""Killer Demo Script executing the 15-step Phase 2 evaluation scenario against real PostgreSQL.

Demonstrates:
1. Selection of Synthetic Class III NAWI
2. Evaluation creation with immutable frozen configuration snapshot
3. Deterministic R-76 test plan generation
4. Inspection of applicable tests, R-76 references, and implementation status
5. Weighing Performance test execution (Attempt 1)
6. Submitting raw observations (L, I, ΔL, E0)
7. Backend calculation of P, E, Ec, and Table 6 MPE
8. Intentionally failing Attempt 1 (Ec > MPE)
9. Retest creation (Attempt 2) preserving Attempt 1 FAIL history
10. Submitting corrected observations for Attempt 2
11. Attempt 2 calculation passing (Ec <= MPE)
12. Audit verification: Attempt 1 FAIL intact, Attempt 2 PASS intact
13. End-to-end traceability chain retrieval
14. Multi-range instrument evaluation and plan generation proving range-specific test expansion
"""

from decimal import Decimal
import json
import sys
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models.configuration import InstrumentConfiguration
from app.models.instrument import Instrument
from app.models.metrology import ComplianceDecision, ComplianceResult
from app.models.test_execution import TestAttempt


def print_step(step_num: int, title: str):
    print(f"\n{'='*70}")
    print(f"STEP {step_num}: {title}")
    print(f"{'='*70}")


def run_killer_demo():
    print("🚀 STARTING SIH26035 PHASE 2 KILLER DEMO AGAINST POSTGRESQL...")
    client = TestClient(app)

    # -------------------------------------------------------------
    # STEP 1: Select Synthetic Class III NAWI
    # -------------------------------------------------------------
    print_step(1, "Select Synthetic Class III Instrument from Catalog")
    with SessionLocal() as db:
        inst = db.scalar(
            select(Instrument)
            .where(Instrument.serial_number == "SYNTH-DEMO-NAWI-001-SN")
            .limit(1)
        )
        assert inst is not None, "SYNTH-DEMO-NAWI-001-SN not found in database. Run seed first."
        inst_id = str(inst.id)
        config = db.scalar(
            select(InstrumentConfiguration)
            .where(InstrumentConfiguration.instrument_id == inst.id, InstrumentConfiguration.is_active.is_(True))
            .limit(1)
        )
        assert config is not None
        config_id = str(config.id)

    print(f"✔ Found Instrument: {inst.manufacturer} {inst.model_name} (SN: {inst.serial_number})")
    print(f"✔ Configuration: Max={config.max_capacity} {config.unit}, e={config.verification_scale_interval} {config.unit}, Class={config.accuracy_class.value}")
    print(f"✔ Guardrail check: is_synthetic = {inst.is_synthetic}")

    # -------------------------------------------------------------
    # STEP 2 & 3: Create Evaluation & Freeze Configuration Snapshot
    # -------------------------------------------------------------
    print_step(2, "Create Evaluation & Freeze Configuration Snapshot")
    eval_resp = client.post(
        f"/api/v1/instruments/{inst_id}/evaluations",
        json={
            "instrument_configuration_id": config_id,
            "lab_name": "National Metrological Type Evaluation Authority",
        },
    )
    assert eval_resp.status_code == 201, eval_resp.text
    eval_data = eval_resp.json()
    eval_id = eval_data["id"]
    snapshot = eval_data["configuration_snapshot"]

    print(f"✔ Evaluation Created: ID={eval_id}, Number={eval_data['evaluation_number']}")
    print(f"✔ Frozen Snapshot Captured: Max={snapshot['max_capacity']} {snapshot['unit']}, e={snapshot['verification_scale_interval']} {snapshot['unit']}")
    print(f"✔ Snapshot Timestamp: {snapshot.get('snapshot_timestamp')}")

    # -------------------------------------------------------------
    # STEP 4 & 5: Generate Test Plan via Applicability Engine
    # -------------------------------------------------------------
    print_step(4, "Call POST /api/v1/evaluations/{id}/generate-plan")
    plan_resp = client.post(f"/api/v1/evaluations/{eval_id}/generate-plan")
    assert plan_resp.status_code == 200, plan_resp.text
    plan_data = plan_resp.json()

    print_step(5, "Inspect Dynamically Generated Applicable R-76 Tests")
    print(f"Total Tests Generated: {plan_data['total_tests']}")
    print(f"Applicable Tests Count: {plan_data['applicable_tests_count']}")
    print("\nGenerated Test Schedule:")
    for t in plan_data["tests"]:
        status_symbol = "✅ APPLICABLE" if t["status"] != "NOT_APPLICABLE" else "⚪ INAPPLICABLE"
        print(f" - [{t['sequence']:02d}] {t['test_code']:<25} | {t['r76_reference']:<15} | {t['implementation_status']:<18} | {status_symbol}")
        print(f"      Reason: {t['applicability_reason']}")

    weighing_test = next(t for t in plan_data["tests"] if t["test_code"] == "WEIGHING_PERFORMANCE")
    weighing_test_id = weighing_test["id"]

    # -------------------------------------------------------------
    # STEP 6 & 7: Open Weighing Performance & Inspect Attempt 1
    # -------------------------------------------------------------
    print_step(6, "Open WEIGHING PERFORMANCE Test & Inspect Attempt 1")
    test_detail_resp = client.get(f"/api/v1/evaluation-tests/{weighing_test_id}")
    assert test_detail_resp.status_code == 200
    test_detail = test_detail_resp.json()
    assert len(test_detail["attempts"]) >= 1
    attempt1 = test_detail["attempts"][0]
    attempt1_id = attempt1["id"]
    print(f"✔ Weighing Test ID: {weighing_test_id}")
    print(f"✔ Attempt #1 Initialized: ID={attempt1_id}, Status={attempt1['status']}")
    print(f"✔ Procedural Steps Count: {len(attempt1['steps'])}")
    for step in attempt1["steps"]:
        print(f"    Step {step['sequence']}: {step['title']} ({step['step_code']})")

    # -------------------------------------------------------------
    # STEP 8 & 9: Submit Raw Failing Observations for Attempt 1
    # -------------------------------------------------------------
    print_step(8, "Submit Raw Observations for Attempt 1 (Simulating Calibration Defect)")
    # Test point: Load L = 10.00 kg.
    # Verification interval e = 0.01 kg -> 1000 e (Band 2: MPE = 1.0 e = 0.010 kg).
    # Indication I = 10.025 kg, ΔL = 0.005 kg, E0 = 0.000 kg.
    # P = 10.025 + 0.005 - 0.005 = 10.025 kg.
    # E = 10.025 - 10.000 = +0.025 kg.
    # Ec = +0.025 kg > MPE (0.010 kg) -> MUST FAIL.
    obs_payloads = [
        {"observation_code": "LOAD", "value_numeric": "10.00", "unit": "kg", "notes": "Standard 10kg test weight applied"},
        {"observation_code": "INDICATION", "value_numeric": "10.025", "unit": "kg", "notes": "Instrument digital readout"},
        {"observation_code": "ADDITIONAL_LOAD", "value_numeric": "0.005", "unit": "kg", "notes": "Weights added to find changeover point (ΔL)"},
        {"observation_code": "ZERO_ERROR", "value_numeric": "0.000", "unit": "kg", "notes": "Zero error E0"},
    ]
    for obs in obs_payloads:
        resp = client.post(f"/api/v1/test-attempts/{attempt1_id}/observations", json=obs)
        assert resp.status_code == 201, resp.text
        print(f"  ✔ Recorded: {obs['observation_code']} = {obs['value_numeric']} {obs['unit']}")

    print_step(9, "Backend Executes Authoritative A.4.4.3 Calculation for Attempt 1")
    calc1_resp = client.post(f"/api/v1/test-attempts/{attempt1_id}/calculate")
    assert calc1_resp.status_code == 200, calc1_resp.text
    calc1_data = calc1_resp.json()

    out1 = calc1_data["calculation"]["output"]
    print(f"✔ Calculated Indication Prior to Rounding (P): {out1['P']} kg")
    print(f"✔ Calculated Error Prior to Rounding (E):       {out1['E']} kg")
    print(f"✔ Corrected Error (Ec = E - E0):                {out1['Ec']} kg")
    print(f"✔ Authoritative Table 6 MPE:                    {out1['mpe_mass']} kg ({out1['mpe_factor']} e)")

    # -------------------------------------------------------------
    # STEP 10, 11, 12: Compliance Decision for Attempt 1 -> FAIL
    # -------------------------------------------------------------
    print_step(10, "Compliance Engine Deterministic Evaluation (Attempt 1)")
    comp1 = calc1_data["compliance"]
    print(f"✔ DECISION:        {comp1['decision']}")
    print(f"✔ MEASURED VALUE:  {comp1['measured_value']}")
    print(f"✔ CRITERION:       {comp1['criterion_value']}")
    print(f"✔ TOLERANCE MARGIN:{comp1['margin']}")
    print(f"✔ EXPLANATION:     {comp1['reasoning']['explanation']}")
    print(f"✔ RULE REFERENCE:  {comp1['reasoning']['rule_reference']}")
    assert comp1["decision"] == "FAIL", "Attempt 1 was expected to FAIL"

    # -------------------------------------------------------------
    # STEP 13: Create Retest (Attempt 2) & Retest Execution
    # -------------------------------------------------------------
    print_step(13, "Create Retest (Attempt 2) Preserving Attempt 1 History")
    retest_resp = client.post(
        f"/api/v1/evaluation-tests/{weighing_test_id}/attempts",
        json={"notes": "Technician recalibrated span and verified zero switch point."},
    )
    assert retest_resp.status_code == 201, retest_resp.text
    attempt2_data = retest_resp.json()
    attempt2_id = attempt2_data["id"]

    print(f"✔ Created Retest Attempt: ID={attempt2_id}")
    print(f"✔ Attempt Number: {attempt2_data['attempt_number']}")
    print(f"✔ Supersedes Attempt ID: {attempt2_data['supersedes_attempt_id']}")

    # Submit passing observations for Attempt 2:
    # L = 10.00 kg, I = 10.00 kg, ΔL = 0.005 kg, E0 = 0.000 kg.
    # P = 10.000 kg, E = 0.000 kg, Ec = 0.000 kg <= MPE (0.010 kg) -> PASS.
    passing_obs = [
        {"observation_code": "LOAD", "value_numeric": "10.00", "unit": "kg"},
        {"observation_code": "INDICATION", "value_numeric": "10.00", "unit": "kg"},
        {"observation_code": "ADDITIONAL_LOAD", "value_numeric": "0.005", "unit": "kg"},
        {"observation_code": "ZERO_ERROR", "value_numeric": "0.000", "unit": "kg"},
    ]
    for obs in passing_obs:
        resp = client.post(f"/api/v1/test-attempts/{attempt2_id}/observations", json=obs)
        assert resp.status_code == 201

    calc2_resp = client.post(f"/api/v1/test-attempts/{attempt2_id}/calculate")
    assert calc2_resp.status_code == 200
    comp2 = calc2_resp.json()["compliance"]
    print(f"✔ Attempt 2 DECISION: {comp2['decision']}")
    print(f"✔ Attempt 2 Margin:   {comp2['margin']}")
    print(f"✔ Attempt 2 Reason:   {comp2['reasoning']['explanation']}")
    assert comp2["decision"] == "PASS", "Attempt 2 was expected to PASS"

    # Audit check: verify Attempt 1 was NOT overwritten
    with SessionLocal() as db:
        att1_uuid = uuid.UUID(attempt1_id)
        att2_uuid = uuid.UUID(attempt2_id)
        att1_db = db.get(TestAttempt, att1_uuid)
        assert att1_db is not None
        comp1_db = db.scalar(select(ComplianceResult).where(ComplianceResult.test_attempt_id == att1_uuid))
        assert comp1_db is not None
        assert comp1_db.decision == ComplianceDecision.FAIL

        att2_db = db.get(TestAttempt, att2_uuid)
        assert att2_db is not None
        comp2_db = db.scalar(select(ComplianceResult).where(ComplianceResult.test_attempt_id == att2_uuid))
        assert comp2_db is not None
        assert comp2_db.decision == ComplianceDecision.PASS

    print("✔ Audit check passed: Attempt 1 FAIL remains intact; Attempt 2 PASS is recorded alongside it.")

    # -------------------------------------------------------------
    # STEP 14: Traceability Chain Verification
    # -------------------------------------------------------------
    print_step(14, "Retrieve Audit Traceability Chain for Attempt 2")
    trace_resp = client.get(f"/api/v1/test-attempts/{attempt2_id}/trace")
    assert trace_resp.status_code == 200
    trace = trace_resp.json()

    print("Traceability Chain Graph:")
    print(f"  [Instrument]           Serial={trace['instrument']['serial_number']}, Model={trace['instrument']['model_name']}")
    print(f"     ↓")
    print(f"  [Snapshot]             Max={trace['configuration_snapshot']['max_capacity']}, e={trace['configuration_snapshot']['verification_scale_interval']}")
    print(f"     ↓")
    print(f"  [Evaluation]           Number={trace['evaluation']['evaluation_number']}")
    print(f"     ↓")
    print(f"  [Evaluation Test]      Code={trace['evaluation_test']['test_code']}, R-76 Clause={trace['evaluation_test']['r76_reference']}")
    print(f"     ↓")
    print(f"  [Rule Version]         Standard={trace['rule_version']['standard_version']}, Clause={trace['rule_version']['clause']}, SHA-256={trace['rule_version']['content_hash'][:16]}...")
    print(f"     ↓")
    print(f"  [Raw Observations]     {len(trace['raw_observations'])} observations recorded with timestamp and operator audit")
    print(f"     ↓")
    print(f"  [Calculation]          Code={trace['calculation']['code']}, Formula={trace['calculation']['formula_reference']}")
    print(f"     ↓")
    print(f"  [Compliance Decision]  {trace['compliance']['decision']} (Margin: {trace['compliance']['margin']})")

    # -------------------------------------------------------------
    # STEP 15: Multi-range Instrument Plan Generation USP
    # -------------------------------------------------------------
    print_step(15, "Multi-Range Configuration & Plan Expansion USP Demonstration")
    with SessionLocal() as db:
        multi_inst = db.scalar(
            select(Instrument)
            .where(Instrument.serial_number == "SYNTH-DEMO-MULTI-002-SN")
            .limit(1)
        )
        assert multi_inst is not None, "SYNTH-DEMO-MULTI-002-SN not found in database."
        multi_config = db.scalar(
            select(InstrumentConfiguration)
            .where(InstrumentConfiguration.instrument_id == multi_inst.id, InstrumentConfiguration.is_active.is_(True))
            .limit(1)
        )
        assert multi_config is not None
        multi_inst_id = str(multi_inst.id)
        multi_config_id = str(multi_config.id)

    multi_eval_resp = client.post(
        f"/api/v1/instruments/{multi_inst_id}/evaluations",
        json={"instrument_configuration_id": multi_config_id},
    )
    assert multi_eval_resp.status_code == 201
    multi_eval_id = multi_eval_resp.json()["id"]

    multi_plan_resp = client.post(f"/api/v1/evaluations/{multi_eval_id}/generate-plan")
    assert multi_plan_resp.status_code == 200
    multi_plan = multi_plan_resp.json()

    print(f"✔ Multi-range Instrument: {multi_inst.model_name} (Number of Ranges: {multi_config.number_of_ranges})")
    print(f"✔ Plan Generated for Multi-range NAWI:")
    for t in multi_plan["tests"]:
        if "WEIGHING_PERFORMANCE" in t["test_code"]:
            print(f"   ⭐ RANGE-SCOPED TEST: {t['test_code']} -> {t['title']}")
            print(f"        Reference: {t['r76_reference']}, Reason: {t['applicability_reason']}")

    multi_codes = [t["test_code"] for t in multi_plan["tests"]]
    assert "WEIGHING_PERFORMANCE_RANGE_1" in multi_codes
    assert "WEIGHING_PERFORMANCE_RANGE_2" in multi_codes
    assert "WEIGHING_PERFORMANCE" not in multi_codes

    print("\n🎉 KILLER DEMO COMPLETED SUCCESSFULLY WITH ZERO DEFECTS AGAINST REAL POSTGRESQL!")


if __name__ == "__main__":
    run_killer_demo()
