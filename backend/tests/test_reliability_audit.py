"""
Phase 5 Reliability & Behavioral Audit Test Suite.

Explicitly tests:
A. Relevant historical memory exists and materially shapes the recommendation.
B. No relevant historical memory exists and agent explicitly notes absence without fabricating.
C. Human rejection stops execution lifecycle and rejects invalid forward transitions.
D. Gemini API failure/timeout is handled gracefully via structured fallback.
E. Malformed/null LLM output fields are sanitized and bounded without crashes.
F. Insufficient measurement evidence returns INSUFFICIENT_EVIDENCE without artificial positive outcome.
"""

import pytest
from unittest.mock import patch
from datetime import datetime
from fastapi.testclient import TestClient

from backend.app import app
from backend.data.schema import (
    DetectedProblem, ProductArea, CustomerSegment, Severity,
    RecalledMemory, ActionType, ActionState, OutcomeClassification, ProductAction, FeedbackItem
)
from backend.agent.decider import generate_product_action
from backend.agent.measurer import evaluate_intervention_impact
from backend.agent.state_machine import ActionStateMachine, InvalidStateTransitionError
from backend.memory.hindsight_manager import hindsight_manager


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_problem():
    return DetectedProblem(
        id="prob-auth-001",
        product_area=ProductArea.AUTH_ONBOARDING,
        segment=CustomerSegment.ENTERPRISE,
        title="Enterprise SSO Login Token Timeout",
        complaint_count=12,
        prior_period_count=1,
        trend_pct=1100.0,
        sentiment_avg=-0.82,
        severity=Severity.CRITICAL,
        why_it_matters="Enterprise users unable to complete SAML token exchange.",
        sample_feedback_ids=["fb-auth-1"],
        detected_at=datetime.utcnow()
    )


@pytest.fixture
def sparse_problem():
    return DetectedProblem(
        id="prob-sparse-001",
        product_area=ProductArea.NOTIFICATIONS,
        segment=CustomerSegment.WEB_DESKTOP,
        title="Occasional Notification Delay",
        complaint_count=1,
        prior_period_count=1,
        trend_pct=0.0,
        sentiment_avg=-0.1,
        severity=Severity.LOW,
        why_it_matters="One user reported notification arrived 20 seconds late.",
        sample_feedback_ids=["fb-notif-1"],
        detected_at=datetime.utcnow()
    )


# ---------------------------------------------------------------------------
# BEHAVIOR TEST A: Relevant Historical Memory Exists
# ---------------------------------------------------------------------------
def test_behavior_a_relevant_memory_influence(auth_problem):
    """Verify historical memory is recalled and materially influences recommendation."""
    memories = [
        RecalledMemory(
            id="mem-auth-lesson",
            category="LESSON",
            content="Incident INC-108 [LESSON]: Enterprise SAML SSO token timeouts after key rotation require flushing Redis token cache.",
            metadata={"incident_id": "INC-108", "product_area": "auth_onboarding"},
            relevance_score=0.96
        )
    ]
    action = generate_product_action(auth_problem, memories, action_id="ACT-AUDIT-A")
    assert action.status == ActionState.RECOMMENDED
    assert len(action.recalled_memories) == 1
    assert "redis" in action.reasoning_with_memory.lower() or "inc-108" in action.reasoning_with_memory.lower() or "saml" in action.reasoning_with_memory.lower() or "flush" in action.reasoning_with_memory.lower()
    assert action.type in [ActionType.CREATE_INVESTIGATION, ActionType.CREATE_EXPERIMENT, ActionType.CREATE_PRODUCT_CHANGE]


# ---------------------------------------------------------------------------
# BEHAVIOR TEST B: No Relevant Historical Memory Exists
# ---------------------------------------------------------------------------
def test_behavior_b_no_memory_fabrication(sparse_problem):
    """Verify that when no memory exists, agent does not invent historical incidents."""
    action = generate_product_action(sparse_problem, recalled_memories=[], action_id="ACT-AUDIT-B")
    assert len(action.recalled_memories) == 0
    reasoning_lower = action.reasoning_with_memory.lower()
    influence_lower = action.memory_influence_summary.lower()
    # Must explicitly state no prior memory
    assert ("no " in influence_lower or "baseline" in influence_lower or "not found" in influence_lower or "first-principles" in influence_lower or "no prior" in reasoning_lower or "baseline" in reasoning_lower)
    # Must NOT hallucinate non-existent incidents
    assert "inc-999" not in reasoning_lower


# ---------------------------------------------------------------------------
# BEHAVIOR TEST C: Human Rejects Action
# ---------------------------------------------------------------------------
def test_behavior_c_rejection_blocks_execution(auth_problem):
    """Verify that human rejection moves to REJECTED and execution is strictly blocked."""
    action = generate_product_action(auth_problem, [], action_id="ACT-AUDIT-C")
    assert action.status == ActionState.RECOMMENDED

    # Reject
    rejected_action = ActionStateMachine.transition(action, ActionState.REJECTED)
    assert rejected_action.status == ActionState.REJECTED

    # Attempting to execute a rejected action must fail
    with pytest.raises(InvalidStateTransitionError):
        ActionStateMachine.transition(rejected_action, ActionState.EXECUTED)

    # Attempting to approve a rejected action must fail
    with pytest.raises(InvalidStateTransitionError):
        ActionStateMachine.transition(rejected_action, ActionState.APPROVED)


# ---------------------------------------------------------------------------
# BEHAVIOR TEST D: Gemini / API Failure Graceful Fallback
# ---------------------------------------------------------------------------
def test_behavior_d_gemini_api_failure_handling(auth_problem):
    """Verify system handles LLM call exceptions without crashing."""
    with patch("backend.agent.decider._call_gemini_decider", return_value=None):
        action = generate_product_action(auth_problem, [], action_id="ACT-AUDIT-D")
        assert action is not None
        assert action.id == "ACT-AUDIT-D"
        assert action.type in list(ActionType)
        assert len(action.title) > 0
        assert len(action.reasoning_without_memory) > 0
        assert len(action.reasoning_with_memory) > 0


# ---------------------------------------------------------------------------
# BEHAVIOR TEST E: Malformed / Null Output Fields from LLM
# ---------------------------------------------------------------------------
def test_behavior_e_malformed_llm_response(auth_problem):
    """Verify that missing, empty, or invalid fields from LLM do not crash the system."""
    malformed_responses = [
        {},  # empty dict
        {"action_type": "UNKNOWN_ACTION", "title": ""},  # invalid action type and empty title
        {"action_type": None, "priority": "SUPER_URGENT", "title": None, "reasoning_with_memory": None},  # null fields
        {"action_type": "CREATE_INVESTIGATION", "title": "   "}  # whitespace
    ]

    for malformed in malformed_responses:
        with patch("backend.agent.decider._call_gemini_decider", return_value=malformed):
            action = generate_product_action(auth_problem, [], action_id="ACT-AUDIT-E")
            assert action.type in [ActionType.CREATE_INVESTIGATION, ActionType.CREATE_EXPERIMENT, ActionType.CREATE_PRODUCT_CHANGE]
            assert action.priority in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
            assert len(action.title) > 0
            assert len(action.reasoning_without_memory) > 0
            assert len(action.reasoning_with_memory) > 0
            assert len(action.memory_influence_summary) > 0


# ---------------------------------------------------------------------------
# BEHAVIOR TEST F: Insufficient Measurement Evidence
# ---------------------------------------------------------------------------
def test_behavior_f_insufficient_evidence_reporting(sparse_problem):
    """Verify that sparse feedback data yields INSUFFICIENT_EVIDENCE rather than false success."""
    action = generate_product_action(sparse_problem, [], action_id="ACT-AUDIT-F")
    action = ActionStateMachine.transition(action, ActionState.APPROVED)

    # Sparse feedback (only 1 complaint pre, 1 complaint post)
    sparse_feedback = [
        FeedbackItem(
            id="sp-1", date="2026-09-01", week=3,
            product_area=sparse_problem.product_area, segment=sparse_problem.segment,
            title="Slight delay", body="Notification arrived a bit late",
            sentiment_score=-0.2, is_complaint=True
        ),
        FeedbackItem(
            id="sp-2", date="2026-09-08", week=4,
            product_area=sparse_problem.product_area, segment=sparse_problem.segment,
            title="Slight delay", body="Notification arrived a bit late",
            sentiment_score=-0.1, is_complaint=True
        )
    ]

    result = evaluate_intervention_impact(action, sparse_feedback, pre_week=3, post_week=4)
    assert result.outcome == OutcomeClassification.INSUFFICIENT_EVIDENCE
    assert "too sparse" in result.reasoning.lower() or "insufficient" in result.lesson_learned.lower()
