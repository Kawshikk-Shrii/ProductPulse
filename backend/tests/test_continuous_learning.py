"""
Test Suite: Continuous Learning Loop & Challenge Incident Adaptation.

Verifies:
1. First incident lesson is retained into persistent Hindsight organizational memory.
2. Second incident retrieves the historical lesson.
3. Historical memory is passed into AI reasoning.
4. Relevant memory dynamically adapts the reasoning and proposed action.
5. Irrelevant memory does not force reuse of the historical action.
6. Second decision is generated successfully via /api/agent/challenge and /api/agent/decide.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app import app
from backend.data.schema import (
    DetectedProblem, ProductArea, CustomerSegment, Severity,
    RecalledMemory, ActionType, ActionState, ProductAction
)
from backend.memory.hindsight_manager import hindsight_manager
from backend.agent.decider import generate_product_action


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def challenge_problem():
    return DetectedProblem(
        id="prob-challenge-002",
        product_area=ProductArea.CHECKOUT_PAYMENTS,
        segment=CustomerSegment.ANDROID,
        title="Android Biometric Checkout Failure & 3DS Auth Timeout",
        complaint_count=18,
        prior_period_count=2,
        trend_pct=800.0,
        sentiment_avg=-0.84,
        severity=Severity.CRITICAL,
        why_it_matters="High drop-off on biometric checkout re-authentication during 3DS step-up verification.",
        sample_feedback_ids=["fb-3ds-01", "fb-3ds-02"],
        detected_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def irrelevant_problem():
    return DetectedProblem(
        id="prob-irrelevant-003",
        product_area=ProductArea.NOTIFICATIONS,
        segment=CustomerSegment.WEB_DESKTOP,
        title="Desktop Chrome Web Push Notification Delay",
        complaint_count=9,
        prior_period_count=3,
        trend_pct=200.0,
        sentiment_avg=-0.65,
        severity=Severity.MEDIUM,
        why_it_matters="Push notifications arriving with 15-minute delay on Chrome desktop.",
        sample_feedback_ids=["fb-notif-01"],
        detected_at=datetime.now(timezone.utc)
    )


def test_1_first_incident_lesson_retained(client):
    """Verify first incident lesson is stored into Hindsight organizational memory."""
    hindsight_manager.seed_initial_knowledge()
    
    # Store first incident lesson
    mem_id = hindsight_manager.retain_decision_lifecycle(
        category="LESSON",
        content="Incident INC-104 [LESSON]: Isolating the Android SDK tokenization wrapper and adding asynchronous re-auth prevents checkout dropouts (Action ACT-2026-001: -92.9% complaints).",
        tags=["LESSON", "checkout_payments", "android", "ACT-2026-001", "COMPLETED"],
        metadata={
            "action_id": "ACT-2026-001",
            "incident_id": "INC-104",
            "product_area": "checkout_payments",
            "affected_segment": "android",
            "category": "LESSON",
            "outcome": "SUCCESS",
            "complaint_delta_pct": -92.9,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "source": "lifecycle_completion"
        }
    )
    assert mem_id is not None
    assert "mem-" in mem_id or "id" in str(mem_id) or len(str(mem_id)) > 0


def test_2_second_incident_retrieves_historical_lesson(challenge_problem):
    """Verify that querying for the second incident recalls the lesson from the first incident."""
    memories = hindsight_manager.recall_relevant_experience(
        query=f"{challenge_problem.title} {challenge_problem.why_it_matters}",
        tags=[challenge_problem.product_area.value, challenge_problem.segment.value],
        max_tokens=4096
    )
    assert len(memories) > 0
    # Must retrieve Android/checkout experience
    has_android_context = any(
        "Android" in m.content or "token" in m.content.lower() or "checkout" in m.content.lower()
        for m in memories
    )
    assert has_android_context, "Hindsight failed to recall historical Android checkout memory"


def test_3_historical_memory_passed_into_reasoning(challenge_problem):
    """Verify historical memory is passed into reasoning and populates adaptation fields."""
    recalled = [
        RecalledMemory(
            id="mem-test-001",
            content="Historical Incident INC-104: Android GooglePay tokenization latency resolved by patching token wrapper (Action ACT-2026-001: -92.9% complaints).",
            relevance_score=0.92,
            category="HISTORICAL_INCIDENT",
            metadata={"incident_id": "INC-104", "action_id": "ACT-2026-001"}
        )
    ]
    
    action = generate_product_action(challenge_problem, recalled)
    
    assert action is not None
    assert action.relevance_assessment in ["HIGHLY_RELEVANT", "PARTIALLY_RELEVANT"]
    assert len(action.memory_similarities) > 0
    assert len(action.memory_differences) > 0
    assert action.adaptation_rationale is not None
    assert len(action.adaptation_rationale) > 10


def test_4_relevant_memory_changes_reasoning(challenge_problem):
    """Verify relevant memory materially changes the reasoning compared to baseline."""
    recalled = [
        RecalledMemory(
            id="mem-test-001",
            content="Historical Action ACT-2026-001: Patched Android tokenization wrapper yielding verified 92.9% complaint reduction.",
            relevance_score=0.95,
            category="HISTORICAL_ACTION",
            metadata={"action_id": "ACT-2026-001"}
        )
    ]
    
    action_with = generate_product_action(challenge_problem, recalled)
    action_without = generate_product_action(challenge_problem, [])
    
    # Reasoning with memory must reference the organizational experience
    assert action_with.reasoning_with_memory != action_without.reasoning_without_memory
    assert "token" in action_with.reasoning_with_memory.lower() or "android" in action_with.reasoning_with_memory.lower()
    assert action_with.memory_influence_summary != "No historical memories were available to influence this decision."


def test_5_irrelevant_memory_does_not_force_reuse(irrelevant_problem):
    """Verify that an irrelevant memory (Android checkout) is not blindly reused for notifications."""
    recalled = [
        RecalledMemory(
            id="mem-android-checkout",
            content="Historical Action ACT-2026-001: Patched Android GooglePay tokenization wrapper for checkout.",
            relevance_score=0.30,
            category="HISTORICAL_ACTION",
            metadata={"action_id": "ACT-2026-001"}
        )
    ]
    
    action = generate_product_action(irrelevant_problem, recalled)
    
    # Must assess as NOT_RELEVANT or not propose payment wrapper for notifications
    assert action.product_area == ProductArea.NOTIFICATIONS
    assert "googlepay" not in action.title.lower()
    assert "3ds" not in action.title.lower()
    if action.relevance_assessment:
        assert action.relevance_assessment in ["NOT_RELEVANT", "PARTIALLY_RELEVANT"]


def test_6_second_decision_generated_via_endpoint(client):
    """Verify the full Challenge API endpoint flow works end-to-end."""
    # Step 1: Challenge endpoint creates the incident
    challenge_res = client.post("/api/agent/challenge")
    assert challenge_res.status_code == 200
    data = challenge_res.json()
    assert data["status"] == "success"
    assert data["problem"]["id"] == "prob-challenge-002"
    
    # Step 2: Agent decides on the challenge incident
    decide_res = client.post("/api/agent/decide", json={"problem_id": "prob-challenge-002"})
    assert decide_res.status_code == 200
    decide_data = decide_res.json()
    action = decide_data["action"]
    
    assert action["status"] == "RECOMMENDED"
    assert action["relevance_assessment"] in ["HIGHLY_RELEVANT", "PARTIALLY_RELEVANT"]
    assert "adaptation_rationale" in action
    assert len(action["memory_similarities"]) > 0
    assert len(action["memory_differences"]) > 0
