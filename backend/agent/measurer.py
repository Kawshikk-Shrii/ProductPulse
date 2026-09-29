"""
Deterministic Measurement and Learning Engine for ProductPulse.
Compares pre-intervention vs post-intervention customer feedback metrics,
determines the objective outcome, and distills organizational lessons.
"""

from typing import List, Dict, Optional
from datetime import datetime
from ..data.schema import (
    FeedbackItem, ProductAction, MeasurementResult, OutcomeClassification,
    ProductArea, CustomerSegment
)


def evaluate_intervention_impact(
    action: ProductAction,
    feedback_items: List[FeedbackItem],
    pre_week: int = 3,
    post_week: int = 4
) -> MeasurementResult:
    """
    Deterministically computes complaint frequency and sentiment shifts before vs after an action.
    Classifies outcome as SUCCESS, PARTIAL_SUCCESS, NO_CLEAR_IMPACT, REGRESSION, or INSUFFICIENT_EVIDENCE.
    """
    pre_items = [
        f for f in feedback_items
        if f.week == pre_week and f.product_area == action.product_area and f.is_complaint
    ]
    post_items = [
        f for f in feedback_items
        if f.week == post_week and f.product_area == action.product_area and f.is_complaint
    ]

    # Filter to specific affected segment
    seg_pre_items = [f for f in pre_items if f.segment == action.affected_segment]
    seg_post_items = [f for f in post_items if f.segment == action.affected_segment]

    pre_count = len(seg_pre_items)
    post_count = len(seg_post_items)

    # Percentage change
    if pre_count == 0:
        complaint_delta_pct = 0.0 if post_count == 0 else 100.0
    else:
        complaint_delta_pct = ((post_count - pre_count) / pre_count) * 100.0

    # Sentiment calculation for all segment feedback in pre vs post
    all_seg_pre = [
        f for f in feedback_items
        if f.week == pre_week and f.product_area == action.product_area and f.segment == action.affected_segment
    ]
    all_seg_post = [
        f for f in feedback_items
        if f.week == post_week and f.product_area == action.product_area and f.segment == action.affected_segment
    ]

    pre_sentiment = sum(f.sentiment_score for f in all_seg_pre) / len(all_seg_pre) if all_seg_pre else 0.0
    post_sentiment = sum(f.sentiment_score for f in all_seg_post) / len(all_seg_post) if all_seg_post else 0.0
    sentiment_delta = post_sentiment - pre_sentiment

    area_label = action.product_area.value.replace("_", " ").title()
    seg_label = action.affected_segment.value.replace("_", " ").title()

    # Trustworthy outcome classification logic (deterministic, never forces artificial positive)
    if pre_count < 3 and post_count < 3:
        outcome = OutcomeClassification.INSUFFICIENT_EVIDENCE
        reasoning = (
            f"Pre-intervention volume ({pre_count}) and post-intervention volume ({post_count}) "
            f"for {area_label} ({seg_label}) are too sparse to establish statistical confidence."
        )
        lesson = f"Insufficient sample volume for {area_label} ({seg_label}) to draw firm conclusions. Collect further longitudinal feedback."
    elif complaint_delta_pct <= -60.0 and post_sentiment >= 0.50:
        outcome = OutcomeClassification.SUCCESS
        reasoning = (
            f"Complaints dropped significantly from {pre_count} to {post_count} ({complaint_delta_pct:.1f}%), "
            f"and user sentiment rebounded from {pre_sentiment:.2f} to {post_sentiment:.2f} (+{sentiment_delta:.2f}). "
            f"The intervention achieved its expected outcome."
        )
        lesson = (
            f"Intervention '{action.title}' for {area_label} ({seg_label}) successfully resolved the complaint surge "
            f"(from {pre_count} down to {post_count}, {complaint_delta_pct:.1f}%), validating the targeted resolution strategy."
        )
    elif complaint_delta_pct <= -25.0:
        outcome = OutcomeClassification.PARTIAL_SUCCESS
        reasoning = (
            f"Complaints decreased from {pre_count} to {post_count} ({complaint_delta_pct:.1f}%), "
            f"showing positive trajectory but residual failure reports remain."
        )
        lesson = f"Intervention '{action.title}' reduced complaints by {abs(complaint_delta_pct):.1f}% for {area_label} ({seg_label}), but residual issues require secondary investigation."
    elif complaint_delta_pct >= 25.0 or sentiment_delta <= -0.30:
        outcome = OutcomeClassification.REGRESSION
        reasoning = (
            f"Complaints increased from {pre_count} to {post_count} (+{complaint_delta_pct:.1f}%) "
            f"with worsening sentiment. The intervention appears to have exacerbated the problem."
        )
        lesson = f"Intervention '{action.title}' for {area_label} ({seg_label}) correlated with increased complaints (+{complaint_delta_pct:.1f}%). Recommend immediate rollback."
    else:
        outcome = OutcomeClassification.NO_CLEAR_IMPACT
        reasoning = (
            f"Complaints changed from {pre_count} to {post_count} ({complaint_delta_pct:.1f}%), "
            f"which falls within normal noise thresholds."
        )
        lesson = f"Intervention '{action.title}' for {area_label} ({seg_label}) produced no significant metric shift ({complaint_delta_pct:.1f}%). Re-evaluate underlying root causes."

    return MeasurementResult(
        action_id=action.id,
        pre_complaint_count=pre_count,
        post_complaint_count=post_count,
        complaint_delta_pct=round(complaint_delta_pct, 1),
        pre_sentiment_avg=round(pre_sentiment, 2),
        post_sentiment_avg=round(post_sentiment, 2),
        sentiment_delta=round(sentiment_delta, 2),
        segment_pre_count=pre_count,
        segment_post_count=post_count,
        segment_delta_pct=round(complaint_delta_pct, 1),
        outcome=outcome,
        reasoning=reasoning,
        lesson_learned=lesson,
        measured_at=datetime.utcnow()
    )
