"""
Phase 4 End-to-End Integration Test Suite.
Tests the full fresh-start lifecycle and human rejection governance flow.
"""

from fastapi.testclient import TestClient
from backend.app import app
from backend.data.schema import ActionState, OutcomeClassification


def test_full_fresh_start_lifecycle_flow():
    """
    Simulates the exact click-by-click user flow from a fresh application start:
    1. System Status & Health check
    2. Seed Hindsight Memory Bank
    3. Detect emerging anomalies from Week 3 vs Week 2 feedback
    4. Select top problem and request AI decision (Recall + Gemini reasoning)
    5. Approve recommended action
    6. Transition through state machine to Executed & Measuring
    7. Measure longitudinal outcome (Week 3 vs Week 4)
    8. Distill and Retain lesson into Hindsight
    9. Reflect across accumulated organizational memory
    """
    client = TestClient(app)

    # 1. System Health
    status_resp = client.get("/api/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["app_name"] == "ProductPulse"
    assert status_data["total_feedback_items"] > 0

    # 2. Seed Memory Bank
    seed_resp = client.post("/api/memory/seed")
    assert seed_resp.status_code == 200
    assert seed_resp.json()["status"] == "success"

    # 3. Detect Anomalies
    detect_resp = client.post("/api/agent/detect?current_week=3&prior_week=2")
    assert detect_resp.status_code == 200
    detect_data = detect_resp.json()
    assert detect_data["problems_count"] >= 1
    top_problem = detect_data["problems"][0]
    assert top_problem["id"] is not None
    assert top_problem["complaint_count"] > 0

    # 4. Decide (Remember + Reason + Decide)
    decide_resp = client.post("/api/agent/decide", json={"problem_id": top_problem["id"]})
    assert decide_resp.status_code == 200
    decide_data = decide_resp.json()
    action = decide_data["action"]
    assert action["status"] == "RECOMMENDED"
    assert action["type"] in ["CREATE_INVESTIGATION", "CREATE_EXPERIMENT", "CREATE_PRODUCT_CHANGE"]
    assert len(action["reasoning_with_memory"]) > 0
    assert len(action["reasoning_without_memory"]) > 0
    assert len(action["memory_influence_summary"]) > 0

    # 5. Human Approval
    approve_resp = client.post("/api/agent/action/transition", json={
        "action_id": action["id"],
        "target_state": "APPROVED"
    })
    assert approve_resp.status_code == 200
    approve_data = approve_resp.json()
    assert approve_data["previous_state"] == "RECOMMENDED"
    assert approve_data["new_state"] == "APPROVED"

    # 6. Execute & Measure Transition
    exec_resp = client.post("/api/agent/action/transition", json={
        "action_id": action["id"],
        "target_state": "EXECUTED"
    })
    assert exec_resp.status_code == 200
    assert exec_resp.json()["new_state"] == "EXECUTED"

    meas_trans_resp = client.post("/api/agent/action/transition", json={
        "action_id": action["id"],
        "target_state": "MEASURING"
    })
    assert meas_trans_resp.status_code == 200
    assert meas_trans_resp.json()["new_state"] == "MEASURING"

    # 7. Measure Impact
    measure_resp = client.post("/api/agent/measure", json={
        "action_id": action["id"],
        "pre_week": 3,
        "post_week": 4
    })
    assert measure_resp.status_code == 200
    measure_data = measure_resp.json()["measurement"]
    assert measure_data["outcome"] in [o.value for o in OutcomeClassification]
    assert measure_data["complaint_delta_pct"] <= -60.0

    # 8. Learn (Retain into Hindsight)
    learn_resp = client.post("/api/agent/learn", json={"action_id": action["id"]})
    assert learn_resp.status_code == 200
    learn_data = learn_resp.json()
    assert learn_data["status"] == "success"
    assert learn_data["action_status"] == "COMPLETED"

    # 9. Reflect
    reflect_resp = client.post("/api/agent/reflect", json={
        "query": "Summarize organizational learnings regarding Android checkout tokenization."
    })
    assert reflect_resp.status_code == 200
    assert len(reflect_resp.json()["reflection"]) > 20


def test_rejection_flow_and_governance():
    """
    Verifies human governance gate:
    AI recommends -> Human rejects -> Action marked REJECTED -> Execution is blocked.
    """
    client = TestClient(app)

    # 1. Detect
    detect_resp = client.post("/api/agent/detect?current_week=3&prior_week=2")
    problem = detect_resp.json()["problems"][0]

    # 2. Decide
    decide_resp = client.post("/api/agent/decide", json={"problem_id": problem["id"]})
    action = decide_resp.json()["action"]
    assert action["status"] == "RECOMMENDED"

    # 3. Reject
    reject_resp = client.post("/api/agent/action/transition", json={
        "action_id": action["id"],
        "target_state": "REJECTED"
    })
    assert reject_resp.status_code == 200
    reject_data = reject_resp.json()
    assert reject_data["previous_state"] == "RECOMMENDED"
    assert reject_data["new_state"] == "REJECTED"

    # 4. Attempt invalid transition on rejected action (must be rejected by State Machine)
    invalid_exec_resp = client.post("/api/agent/action/transition", json={
        "action_id": action["id"],
        "target_state": "EXECUTED"
    })
    assert invalid_exec_resp.status_code == 400
    assert "Cannot transition" in invalid_exec_resp.json()["detail"]
