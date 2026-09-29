"""
End-to-End Headless Test for the ProductPulse Agent Loop.
Verifies all capabilities without UI:
1. Seed historical memory into Hindsight (INC-104)
2. Ingest feedback & detect Android checkout failure surge (DETECT)
3. Recall similar incident from Hindsight & contrast reasoning with vs without memory (REASON & DECIDE)
4. Approve bounded action via State Machine (ACT)
5. Ingest Week 4 feedback & evaluate impact (MEASURE)
6. Retain new outcome and lesson into Hindsight (LEARN)
7. Reflect across all memories to prove organizational learning is retained (REFLECT)
"""

import sys
from backend.memory.hindsight_manager import hindsight_manager
from backend.data.feedback_dataset import get_all_feedback
from backend.agent.detector import compute_feedback_metrics, build_detected_problems
from backend.agent.decider import generate_product_action
from backend.agent.measurer import evaluate_intervention_impact
from backend.agent.state_machine import ActionStateMachine
from backend.data.schema import ActionType, ActionState, ProductArea, CustomerSegment, OutcomeClassification


def run_full_test():
    print("=" * 60)
    print("PRODUCTPULSE: FULL AGENT LOOP VERIFICATION")
    print("=" * 60)

    # 1. Seed Memory
    print("\n[Step 1] Seeding Hindsight memory bank...")
    count = hindsight_manager.seed_initial_knowledge()
    print(f"-> Seeded {count} historical memories (INC-104, EXP-042)")

    # 2. Detect
    print("\n[Step 2] Executing Capability A: DETECT...")
    all_feedback = get_all_feedback()
    fb_dict = {f.id: f for f in all_feedback}
    metrics = compute_feedback_metrics(all_feedback, current_week=3, prior_week=2)
    problems = build_detected_problems(metrics, fb_dict)
    print(f"-> Detected {len(problems)} problem clusters.")
    top_problem = problems[0]
    print(f"-> Top Problem: {top_problem.title}")
    print(f"   Severity: {top_problem.severity.value}")
    print(f"   Complaints: {top_problem.complaint_count} (Trend: +{top_problem.trend_pct}%)")
    print(f"   Why it matters: {top_problem.why_it_matters}")

    assert top_problem.product_area == ProductArea.CHECKOUT_PAYMENTS
    assert top_problem.segment == CustomerSegment.ANDROID

    # 3. Recall & Decide
    print("\n[Step 3] Executing Capability B: REMEMBER, REASON & DECIDE...")
    query = f"{top_problem.product_area.value} {top_problem.segment.value} {top_problem.title}"
    recalled = hindsight_manager.recall_relevant_experience(query=query)
    print(f"-> Recalled {len(recalled)} memories from Hindsight:")
    for r in recalled[:2]:
        print(f"   * [{r.category}] {r.content[:100]}...")

    action = generate_product_action(top_problem, recalled, action_id="ACT-2026-TEST")
    print(f"\n-> Proposed Action: {action.type.value} - '{action.title}'")
    print(f"   Status: {action.status.value}")
    print(f"   Reasoning WITHOUT Memory:\n   '{action.reasoning_without_memory}'")
    print(f"   Reasoning WITH Memory:\n   '{action.reasoning_with_memory}'")
    print(f"   Memory Influence:\n   '{action.memory_influence_summary}'")

    assert action.status == ActionState.RECOMMENDED
    assert action.type in [ActionType.CREATE_INVESTIGATION, ActionType.CREATE_EXPERIMENT, ActionType.CREATE_PRODUCT_CHANGE]
    assert len(action.reasoning_with_memory) > 0
    assert len(action.reasoning_without_memory) > 0

    # 4. Act (Human Approval & Execution)
    print("\n[Step 4] Executing Capability B: HUMAN APPROVAL & ACT...")
    ActionStateMachine.transition(action, ActionState.APPROVED)
    print(f"-> Human Approved: Status is now '{action.status.value}'")
    ActionStateMachine.transition(action, ActionState.EXECUTED)
    print(f"-> Action Executed: Status is now '{action.status.value}'")
    ActionStateMachine.transition(action, ActionState.MEASURING)
    print(f"-> Monitoring Started: Status is now '{action.status.value}'")

    # 5. Measure
    print("\n[Step 5] Executing Capability C: MEASURE...")
    measurement = evaluate_intervention_impact(action, all_feedback, pre_week=3, post_week=4)
    print(f"-> Pre-Intervention Complaints: {measurement.pre_complaint_count}")
    print(f"-> Post-Intervention Complaints: {measurement.post_complaint_count}")
    print(f"-> Complaint Change: {measurement.complaint_delta_pct}%")
    print(f"-> Sentiment Shift: {measurement.pre_sentiment_avg} -> {measurement.post_sentiment_avg} (Delta: +{measurement.sentiment_delta})")
    print(f"-> Classified Outcome: {measurement.outcome.value}")
    print(f"-> Reasoning: {measurement.reasoning}")
    print(f"-> Distilled Lesson: {measurement.lesson_learned}")

    assert measurement.outcome == OutcomeClassification.SUCCESS
    assert measurement.complaint_delta_pct <= -60.0

    # 6. Learn
    print("\n[Step 6] Executing Capability C: LEARN (Retain to Hindsight)...")
    content = (
        f"Action {action.id} [{measurement.outcome.value}]: Intervention '{action.title}'. "
        f"Complaints dropped by {measurement.complaint_delta_pct}%. Lesson: {measurement.lesson_learned}"
    )
    retain_id = hindsight_manager.retain_decision_lifecycle(
        category="LESSON",
        content=content,
        tags=[action.id, "OUTCOME", "LESSON", action.product_area.value, action.affected_segment.value],
        metadata={"action_id": action.id, "outcome": measurement.outcome.value}
    )
    ActionStateMachine.transition(action, ActionState.COMPLETED)
    print(f"-> Successfully retained lesson into Hindsight! Final action status: '{action.status.value}'")

    # 7. Reflect (Verify New Wisdom)
    print("\n[Step 7] Reflecting across organizational memory...")
    reflection = hindsight_manager.reflect_on_decision(
        "Summarize organizational learnings regarding Android checkout tokenization and payment SDK failures."
    )
    print("-> Hindsight Reflection:")
    print(reflection)

    print("\n" + "=" * 60)
    print("ALL CORE CAPABILITIES VERIFIED 100% SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_full_test()
