"""
Tests for ProductPulse Phase 1 AI Reasoning Layer.
Tests:
1. Decision generation with relevant historical Hindsight memory (AI synthesis).
2. Decision generation with NO relevant historical memory (explicit absence, no fabrication).
3. Fallback and validation handling for malformed or unavailable LLM responses.
4. Action State Machine transitions and previous_state tracking fix.
5. Measurement engine generalization across different product areas and segments.
6. FastAPI endpoints for decide, transition, and measure.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from backend.data.schema import (
    DetectedProblem, ProductArea, CustomerSegment, Severity,
    RecalledMemory, ActionType, ActionState, ProductAction, OutcomeClassification
)
from backend.agent.decider import (
    generate_product_action, _fallback_decision_reasoning, _build_llm_prompt
)
from backend.agent.state_machine import ActionStateMachine, InvalidStateTransitionError
from backend.agent.measurer import evaluate_intervention_impact
from backend.app import app


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def checkout_problem():
    return DetectedProblem(
        id="prob-001",
        product_area=ProductArea.CHECKOUT_PAYMENTS,
        segment=CustomerSegment.ANDROID,
        title="Android Checkout Payment Failures & Gateway Timeout",
        complaint_count=14,
        prior_period_count=1,
        trend_pct=1300.0,
        sentiment_avg=-0.89,
        severity=Severity.CRITICAL,
        why_it_matters="Rapid surge in checkout failures blocking Android users from purchasing.",
        sample_feedback_ids=["fb-001", "fb-002"],
        detected_at=datetime.utcnow()
    )


@pytest.fixture
def search_problem():
    return DetectedProblem(
        id="prob-002",
        product_area=ProductArea.SEARCH_DISCOVERY,
        segment=CustomerSegment.WEB_DESKTOP,
        title="Web Desktop Search Latency & Empty Results",
        complaint_count=8,
        prior_period_count=3,
        trend_pct=166.7,
        sentiment_avg=-0.65,
        severity=Severity.HIGH,
        why_it_matters="Search queries taking over 3 seconds causing user drops on desktop.",
        sample_feedback_ids=["fb-050", "fb-051"],
        detected_at=datetime.utcnow()
    )


@pytest.fixture
def sample_historical_memories():
    return [
        RecalledMemory(
            id="mem-104-lesson",
            category="LESSON",
            content=(
                "Incident INC-104 [LESSON]: Android payment failure spikes after minor updates are almost always "
                "client-side tokenization wrapper timeouts rather than central gateway outages. Adding client fallback "
                "retry logic resolves the disruption within 48h without server deployment."
            ),
            metadata={"incident_id": "INC-104", "product_area": "checkout_payments", "segment": "android"},
            relevance_score=0.95
        ),
        RecalledMemory(
            id="mem-104-action",
            category="ACTION",
            content=(
                "Incident INC-104 [ACTION]: Patched Android GooglePay SDK wrapper with an asynchronous fallback retry handler."
            ),
            metadata={"incident_id": "INC-104", "product_area": "checkout_payments", "segment": "android"},
            relevance_score=0.91
        )
    ]


# ---------------------------------------------------------------------------
# TESTS: DECISION REASONING LAYER
# ---------------------------------------------------------------------------

def test_decision_with_relevant_memory(checkout_problem, sample_historical_memories):
    """Scenario A: Problem with relevant historical memory."""
    action = generate_product_action(
        problem=checkout_problem,
        recalled_memories=sample_historical_memories,
        action_id="ACT-TEST-001"
    )

    assert isinstance(action, ProductAction)
    assert action.id == "ACT-TEST-001"
    assert action.type in [ActionType.CREATE_INVESTIGATION, ActionType.CREATE_EXPERIMENT, ActionType.CREATE_PRODUCT_CHANGE]
    assert action.status == ActionState.RECOMMENDED
    assert action.affected_segment == CustomerSegment.ANDROID
    assert action.product_area == ProductArea.CHECKOUT_PAYMENTS
    assert len(action.recalled_memories) == 2
    assert len(action.reasoning_with_memory) > 0
    assert len(action.reasoning_without_memory) > 0
    assert len(action.memory_influence_summary) > 0
    # Memory must materially influence the reasoning
    assert "INC-104" in action.reasoning_with_memory or "token" in action.reasoning_with_memory.lower() or "retry" in action.reasoning_with_memory.lower() or "wrapper" in action.reasoning_with_memory.lower()


def test_decision_without_relevant_memory(search_problem):
    """Scenario B: Problem with NO relevant historical memory."""
    action = generate_product_action(
        problem=search_problem,
        recalled_memories=[],
        action_id="ACT-TEST-002"
    )

    assert isinstance(action, ProductAction)
    assert action.id == "ACT-TEST-002"
    assert action.type in [ActionType.CREATE_INVESTIGATION, ActionType.CREATE_EXPERIMENT, ActionType.CREATE_PRODUCT_CHANGE]
    assert len(action.recalled_memories) == 0
    assert len(action.reasoning_with_memory) > 0
    # Agent must explicitly handle absence of memory without hallucinating
    mem_influence_lower = action.memory_influence_summary.lower()
    reasoning_lower = action.reasoning_with_memory.lower()
    assert ("no " in mem_influence_lower or "none" in mem_influence_lower or "first-principles" in mem_influence_lower or "baseline" in mem_influence_lower or "not found" in mem_influence_lower or "no prior" in reasoning_lower or "no relevant" in reasoning_lower or "baseline" in reasoning_lower)


def test_fallback_reasoning_structure(checkout_problem, sample_historical_memories):
    """Verifies that fallback decision logic generates valid structured outputs."""
    result_with = _fallback_decision_reasoning(checkout_problem, sample_historical_memories)
    assert result_with["action_type"] in ["CREATE_INVESTIGATION", "CREATE_EXPERIMENT", "CREATE_PRODUCT_CHANGE"]
    assert "LESSON" in result_with["reasoning_with_memory"] or "checkout" in result_with["reasoning_with_memory"].lower()

    result_without = _fallback_decision_reasoning(checkout_problem, [])
    assert "No relevant historical memories" in result_without["reasoning_with_memory"]
    assert "No prior organizational memory" in result_without["memory_influence_summary"]


def test_prompt_builder_includes_all_required_inputs(checkout_problem, sample_historical_memories):
    """Prompt must include problem, evidence, segment, memories, and outcomes."""
    prompt = _build_llm_prompt(checkout_problem, sample_historical_memories)
    assert checkout_problem.id in prompt
    assert checkout_problem.product_area.value in prompt
    assert checkout_problem.segment.value in prompt
    assert "1300.0" in prompt
    assert "INC-104" in prompt


# ---------------------------------------------------------------------------
# TESTS: ACTION STATE MACHINE & TRANSITION BUG FIX
# ---------------------------------------------------------------------------

def test_state_machine_transitions(checkout_problem):
    action = ProductAction(
        id="ACT-STATE-TEST",
        type=ActionType.CREATE_INVESTIGATION,
        title="Test Action",
        problem_id=checkout_problem.id,
        problem_summary=checkout_problem.title,
        evidence_summary="14 complaints",
        reasoning_with_memory="Reasoning with",
        reasoning_without_memory="Reasoning without",
        memory_influence_summary="Influence",
        recalled_memories=[],
        expected_outcome="Expected",
        affected_segment=checkout_problem.segment,
        product_area=checkout_problem.product_area,
        priority=checkout_problem.severity,
        status=ActionState.RECOMMENDED
    )

    assert action.status == ActionState.RECOMMENDED

    # RECOMMENDED -> APPROVED
    action = ActionStateMachine.transition(action, ActionState.APPROVED)
    assert action.status == ActionState.APPROVED
    assert action.approved_at is not None

    # APPROVED -> EXECUTED
    action = ActionStateMachine.transition(action, ActionState.EXECUTED)
    assert action.status == ActionState.EXECUTED
    assert action.executed_at is not None

    # EXECUTED -> MEASURING
    action = ActionStateMachine.transition(action, ActionState.MEASURING)
    assert action.status == ActionState.MEASURING

    # MEASURING -> COMPLETED
    action = ActionStateMachine.transition(action, ActionState.COMPLETED)
    assert action.status == ActionState.COMPLETED
    assert action.completed_at is not None

    # Invalid transition from COMPLETED should raise
    with pytest.raises(InvalidStateTransitionError):
        ActionStateMachine.transition(action, ActionState.APPROVED)


def test_transition_endpoint_previous_state():
    """Verifies that the /api/agent/action/transition endpoint returns the correct previous_state."""
    client = TestClient(app)

    # Detect problems first so session is initialized
    detect_resp = client.post("/api/agent/detect?current_week=3&prior_week=2")
    assert detect_resp.status_code == 200
    problems = detect_resp.json()["problems"]
    assert len(problems) > 0

    # Decide
    decide_resp = client.post("/api/agent/decide", json={"problem_id": problems[0]["id"]})
    assert decide_resp.status_code == 200
    action_data = decide_resp.json()["action"]
    action_id = action_data["id"]

    # Transition RECOMMENDED -> APPROVED
    trans_resp = client.post("/api/agent/action/transition", json={
        "action_id": action_id,
        "target_state": "APPROVED"
    })
    assert trans_resp.status_code == 200
    body = trans_resp.json()
    assert body["previous_state"] == "RECOMMENDED"
    assert body["new_state"] == "APPROVED"


# ---------------------------------------------------------------------------
# TESTS: GENERALIZED MEASUREMENT ENGINE
# ---------------------------------------------------------------------------

def test_measurement_generalized_for_non_android(search_problem):
    """Verifies measurer works on non-Android problems without hardcoded Android text."""
    action = ProductAction(
        id="ACT-MEASURE-TEST",
        type=ActionType.CREATE_EXPERIMENT,
        title="A/B Test Edge Caching for Search",
        problem_id=search_problem.id,
        problem_summary=search_problem.title,
        evidence_summary="8 complaints",
        reasoning_with_memory="Edge caching experiment",
        reasoning_without_memory="Search profiling",
        memory_influence_summary="Guided by EXP-042",
        recalled_memories=[],
        expected_outcome="Reduce latency under 1.5s",
        affected_segment=search_problem.segment,
        product_area=search_problem.product_area,
        priority=search_problem.severity,
        status=ActionState.APPROVED
    )

    from backend.data.feedback_dataset import get_all_feedback
    feedback = get_all_feedback()

    result = evaluate_intervention_impact(action, feedback, pre_week=3, post_week=4)
    assert result.action_id == action.id
    assert result.outcome in list(OutcomeClassification)
    # Ensure no hardcoded Android / INC-104 references leaked into non-Android measurement
    assert "INC-104" not in result.lesson_learned
    assert "Android" not in result.lesson_learned
    assert "Search Discovery" in result.lesson_learned or "Search" in result.lesson_learned or "sample volume" in result.lesson_learned
