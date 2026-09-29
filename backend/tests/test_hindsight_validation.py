"""
Phase 2 Hindsight Memory Validation & Improvement Test Suite.

Demonstrates:
1. Persistent organizational memory across lifecycle stages (PROBLEM, EVIDENCE, DECISION, ACTION, OUTCOME, LESSON).
2. Metadata completeness (date, product_area, affected_segment, issue, action_id, source).
3. Distilled lifecycle memories rather than raw feedback dumps.
4. Recall of relevant historical experience given a problem.
5. Reflection synthesis across multiple historical memories.
6. CASE A (No Memory) vs CASE B (With Memory) agent decision divergence:
   - CASE A: Novel problem without memory -> baseline first-principles reasoning.
   - CASE B: Problem with relevant memory (INC-104) -> targeted reasoning informed by past outcomes and lessons.
"""

import pytest
from datetime import datetime
from backend.data.schema import (
    DetectedProblem, ProductArea, CustomerSegment, Severity,
    RecalledMemory, ActionType, ActionState, ProductAction, OutcomeClassification
)
from backend.memory.hindsight_manager import hindsight_manager
from backend.agent.decider import generate_product_action
from backend.agent.measurer import evaluate_intervention_impact
from backend.agent.state_machine import ActionStateMachine
from backend.data.feedback_dataset import get_all_feedback


def test_seed_memories_structure_and_metadata():
    """Verify seeded memories contain valid lifecycle categories and complete metadata."""
    seeded_count = hindsight_manager.seed_initial_knowledge()
    assert seeded_count >= 10

    records = hindsight_manager.get_seed_records()
    categories = {r["category"] for r in records}
    expected_categories = {"PROBLEM", "EVIDENCE", "DECISION", "ACTION", "OUTCOME", "LESSON"}
    assert expected_categories.issubset(categories)

    # Verify metadata fields
    for r in records:
        meta = r.get("metadata", {})
        assert "date" in meta
        assert "product_area" in meta
        assert "affected_segment" in meta
        assert "issue" in meta
        assert "action_id" in meta
        assert "source" in meta


def test_hindsight_recall_precision():
    """Verify that querying for Android checkout yields relevant INC-104 memories."""
    hindsight_manager.seed_initial_knowledge()

    # Query for Android checkout failure
    recalled = hindsight_manager.recall_relevant_experience("checkout_payments android checkout failure")
    assert len(recalled) > 0

    recalled_categories = {m.category for m in recalled}
    assert "LESSON" in recalled_categories or "DECISION" in recalled_categories or "OUTCOME" in recalled_categories

    top_memory = recalled[0]
    assert top_memory.relevance_score > 0.5
    assert "checkout_payments" in str(top_memory.metadata.get("product_area"))
    assert "android" in str(top_memory.metadata.get("affected_segment"))


def test_hindsight_reflection_synthesis():
    """Verify that Hindsight reflect synthesizes multi-memory organizational wisdom."""
    hindsight_manager.seed_initial_knowledge()

    reflection = hindsight_manager.reflect_on_decision(
        "What are our organizational learnings on Android checkout and payment tokenization failures?"
    )

    assert isinstance(reflection, str)
    assert len(reflection) > 50
    assert "Android" in reflection or "checkout" in reflection.lower() or "token" in reflection.lower()


def test_case_a_vs_case_b_decision_divergence():
    """
    Demonstrates that memory materially changes agent behavior.

    CASE A: A problem with NO relevant historical memory (Notifications on iOS).
    CASE B: A problem with relevant historical memory (INC-104 Android Checkout).
    """
    hindsight_manager.seed_initial_knowledge()

    # --- CASE A: Problem with NO relevant historical memory ---
    problem_a = DetectedProblem(
        id="prob-novel-001",
        product_area=ProductArea.NOTIFICATIONS,
        segment=CustomerSegment.IOS,
        title="iOS Push Notification Delivery Delays",
        complaint_count=9,
        prior_period_count=1,
        trend_pct=800.0,
        sentiment_avg=-0.72,
        severity=Severity.HIGH,
        why_it_matters="Users report delayed order update notifications on iOS 18.",
        sample_feedback_ids=["fb-notif-1"],
        detected_at=datetime.utcnow()
    )

    recalled_a = hindsight_manager.recall_relevant_experience(
        f"{problem_a.product_area.value} {problem_a.segment.value} {problem_a.title}"
    )
    # Query for notifications should find no relevant payment/search memories
    action_a = generate_product_action(problem_a, recalled_a, action_id="ACT-CASE-A")

    # --- CASE B: Problem WITH relevant historical memory (INC-104) ---
    problem_b = DetectedProblem(
        id="prob-incident-002",
        product_area=ProductArea.CHECKOUT_PAYMENTS,
        segment=CustomerSegment.ANDROID,
        title="Android Checkout Payment Failures & Gateway Timeout",
        complaint_count=14,
        prior_period_count=1,
        trend_pct=1300.0,
        sentiment_avg=-0.89,
        severity=Severity.CRITICAL,
        why_it_matters="Rapid increase in checkout failures concentrated in Android v4.12.0.",
        sample_feedback_ids=["fb-pay-1", "fb-pay-2"],
        detected_at=datetime.utcnow()
    )

    recalled_b = hindsight_manager.recall_relevant_experience(
        f"{problem_b.product_area.value} {problem_b.segment.value} {problem_b.title}"
    )
    assert len(recalled_b) > 0, "CASE B must recall historical INC-104 memories"
    action_b = generate_product_action(problem_b, recalled_b, action_id="ACT-CASE-B")

    # --- VERIFY DIVERGENCE & MEMORY INFLUENCE ---
    # CASE A: Explicit absence of memory, generic diagnostics
    assert len(action_a.recalled_memories) == 0
    reasoning_a_lower = action_a.reasoning_with_memory.lower()
    influence_a_lower = action_a.memory_influence_summary.lower()
    assert (
        "no " in influence_a_lower or "baseline" in influence_a_lower or
        "first-principles" in influence_a_lower or "not found" in influence_a_lower or
        "no " in reasoning_a_lower or "baseline" in reasoning_a_lower
    )

    # CASE B: Materially influenced by past experience
    assert len(action_b.recalled_memories) > 0
    reasoning_b_lower = action_b.reasoning_with_memory.lower()
    influence_b_lower = action_b.memory_influence_summary.lower()

    # The reasoning in CASE B must reference past learnings (INC-104 / token / wrapper / retry / sdk)
    has_past_reference = (
        "inc-104" in reasoning_b_lower or "token" in reasoning_b_lower or
        "wrapper" in reasoning_b_lower or "retry" in reasoning_b_lower or
        "sdk" in reasoning_b_lower or "prior" in reasoning_b_lower or
        "past" in reasoning_b_lower or "historical" in reasoning_b_lower
    )
    assert has_past_reference, f"CASE B reasoning was not influenced by memory: {action_b.reasoning_with_memory}"

    # Confirm CASE A and CASE B produced distinctly different reasoning
    assert action_a.reasoning_with_memory != action_b.reasoning_with_memory
    assert action_a.title != action_b.title


def test_full_lifecycle_distillation_and_retention():
    """
    Verifies complete lifecycle:
    Feedback -> Problem -> Action -> State Machine Approval -> Measure -> Distilled Retention in Hindsight.
    """
    feedback = get_all_feedback()

    # 1. Problem
    problem = DetectedProblem(
        id="prob-lifecycle-001",
        product_area=ProductArea.CHECKOUT_PAYMENTS,
        segment=CustomerSegment.ANDROID,
        title="Android Checkout Payment Failures",
        complaint_count=14,
        prior_period_count=1,
        trend_pct=1300.0,
        sentiment_avg=-0.89,
        severity=Severity.CRITICAL,
        why_it_matters="Surge in Android checkout timeouts.",
        sample_feedback_ids=["fb-001"],
        detected_at=datetime.utcnow()
    )

    # 2. Decision / Action
    recalled = hindsight_manager.recall_relevant_experience("checkout_payments android")
    action = generate_product_action(problem, recalled, action_id="ACT-LIFECYCLE-001")
    assert action.status == ActionState.RECOMMENDED

    # 3. Human Approval & Execution
    action = ActionStateMachine.transition(action, ActionState.APPROVED)
    action = ActionStateMachine.transition(action, ActionState.EXECUTED)
    action = ActionStateMachine.transition(action, ActionState.MEASURING)

    # 4. Measure
    measurement = evaluate_intervention_impact(action, feedback, pre_week=3, post_week=4)
    assert measurement.outcome == OutcomeClassification.SUCCESS

    # 5. Distill & Retain into Hindsight (NOT raw feedback rows)
    content = (
        f"Action {action.id} [{measurement.outcome.value}]: Intervention '{action.title}' "
        f"for {action.product_area.value} ({action.affected_segment.value}). "
        f"Complaints shifted by {measurement.complaint_delta_pct}%. Lesson: {measurement.lesson_learned}"
    )
    tags = [action.id, "OUTCOME", "LESSON", action.product_area.value, action.affected_segment.value, measurement.outcome.value]
    metadata = {
        "action_id": action.id,
        "issue": action.problem_summary,
        "category": "LESSON",
        "product_area": action.product_area.value,
        "affected_segment": action.affected_segment.value,
        "outcome": measurement.outcome.value,
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "source": "productpulse_measurement"
    }

    retain_id = hindsight_manager.retain_decision_lifecycle(
        category="LESSON",
        content=content,
        tags=tags,
        metadata=metadata
    )
    assert retain_id is not None

    action = ActionStateMachine.transition(action, ActionState.COMPLETED)
    assert action.status == ActionState.COMPLETED

    # 6. Verify newly retained lesson is searchable in Hindsight
    recalled_after = hindsight_manager.recall_relevant_experience(action.id)
    assert any(action.id in m.content or action.id in m.id for m in recalled_after)
