"""
Data schemas and models for ProductPulse.
Enforces typed entities for feedback, problems, actions, measurements, and memories.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProductArea(str, Enum):
    CHECKOUT_PAYMENTS = "checkout_payments"
    AUTH_ONBOARDING = "auth_onboarding"
    SEARCH_DISCOVERY = "search_discovery"
    NOTIFICATIONS = "notifications"


class CustomerSegment(str, Enum):
    ANDROID = "android"
    IOS = "ios"
    WEB_DESKTOP = "web_desktop"
    ENTERPRISE = "enterprise"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ActionType(str, Enum):
    CREATE_INVESTIGATION = "CREATE_INVESTIGATION"
    CREATE_EXPERIMENT = "CREATE_EXPERIMENT"
    CREATE_PRODUCT_CHANGE = "CREATE_PRODUCT_CHANGE"


class ActionState(str, Enum):
    RECOMMENDED = "RECOMMENDED"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    MEASURING = "MEASURING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class OutcomeClassification(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    NO_CLEAR_IMPACT = "NO_CLEAR_IMPACT"
    REGRESSION = "REGRESSION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class FeedbackItem(BaseModel):
    id: str
    date: str
    week: int  # 1 to 4
    product_area: ProductArea
    segment: CustomerSegment
    title: str
    body: str
    sentiment_score: float = Field(ge=-1.0, le=1.0)  # -1.0 (very negative) to +1.0 (very positive)
    is_complaint: bool = False
    app_version: Optional[str] = "4.12.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DetectedProblem(BaseModel):
    id: str
    product_area: ProductArea
    segment: CustomerSegment
    title: str
    complaint_count: int
    prior_period_count: int
    trend_pct: float
    sentiment_avg: float
    severity: Severity
    why_it_matters: str
    sample_feedback_ids: List[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class RecalledMemory(BaseModel):
    id: str
    category: str  # PROBLEM, EVIDENCE, DECISION, ACTION, OUTCOME, LESSON
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relevance_score: float = 0.0
    similarity_context: Optional[str] = None


class ProductAction(BaseModel):
    id: str
    type: ActionType
    title: str
    problem_id: str
    problem_summary: str
    evidence_summary: str
    reasoning_with_memory: str
    reasoning_without_memory: str
    memory_influence_summary: str
    recalled_memories: List[RecalledMemory] = Field(default_factory=list)
    expected_outcome: str
    affected_segment: CustomerSegment
    product_area: ProductArea
    priority: Severity
    status: ActionState = ActionState.RECOMMENDED
    relevance_assessment: Optional[str] = "HIGHLY_RELEVANT"
    memory_similarities: Optional[str] = None
    memory_differences: Optional[str] = None
    adaptation_rationale: Optional[str] = None
    historical_action_ref: Optional[str] = None
    historical_outcome_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MeasurementResult(BaseModel):
    action_id: str
    pre_complaint_count: int
    post_complaint_count: int
    complaint_delta_pct: float
    pre_sentiment_avg: float
    post_sentiment_avg: float
    sentiment_delta: float
    segment_pre_count: int
    segment_post_count: int
    segment_delta_pct: float
    outcome: OutcomeClassification
    reasoning: str
    lesson_learned: str
    hindsight_memory_id: Optional[str] = None
    measured_at: datetime = Field(default_factory=datetime.utcnow)
