"""
ProductPulse FastAPI Application Server.
Exposes clean REST APIs for the entire Agent Decision Lifecycle:
DETECT -> REMEMBER -> REASON -> DECIDE -> ACT -> MEASURE -> LEARN.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import settings
from .data.schema import (
    FeedbackItem, DetectedProblem, ProductAction, ActionState,
    MeasurementResult, RecalledMemory, OutcomeClassification,
    ProductArea, CustomerSegment, Severity
)
from .data.feedback_dataset import get_all_feedback
from .agent.detector import compute_feedback_metrics, build_detected_problems
from .agent.decider import generate_product_action
from .agent.measurer import evaluate_intervention_impact
from .agent.state_machine import ActionStateMachine, InvalidStateTransitionError
from .memory.hindsight_manager import hindsight_manager

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Product Operations Agent with Organizational Memory (Microsoft Hackathon)"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for active session state
all_feedback = get_all_feedback()
feedback_dict = {f.id: f for f in all_feedback}
active_problems: Dict[str, DetectedProblem] = {}
active_actions: Dict[str, ProductAction] = {}
active_measurements: Dict[str, MeasurementResult] = {}


@app.on_event("startup")
async def startup_event():
    """Seed foundational organizational memories on startup if needed."""
    try:
        hindsight_manager.ensure_bank()
        print(f"Connected to Hindsight server at {settings.HINDSIGHT_API_URL}")
    except Exception as e:
        print(f"Warning: Could not connect to Hindsight on startup: {e}")


# =========================================================================
# SYSTEM & HEALTH ENDPOINTS
# =========================================================================

@app.get("/api/status")
def get_system_status():
    hindsight_ok = False
    try:
        resp = hindsight_manager.client.get_version()
        hindsight_ok = True
    except Exception:
        pass

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "hindsight_connected": hindsight_ok,
        "hindsight_url": settings.HINDSIGHT_API_URL,
        "bank_id": settings.HINDSIGHT_BANK_ID,
        "actions_in_session": len(active_actions),
        "total_feedback_items": len(all_feedback)
    }


# =========================================================================
# HINDSIGHT MEMORY ENDPOINTS
# =========================================================================

@app.post("/api/memory/seed")
def seed_historical_memories():
    """Seed Incident INC-104 and EXP-042 into the real Hindsight memory bank."""
    count = hindsight_manager.seed_initial_knowledge()
    return {
        "status": "success",
        "message": f"Successfully seeded {count} foundational organizational memories into Hindsight.",
        "bank_id": settings.HINDSIGHT_BANK_ID
    }


@app.get("/api/memory/inspect")
def inspect_memories(query: str = "Android checkout tokenization failure"):
    """Search and inspect memories in Hindsight using TEMPR recall."""
    memories = hindsight_manager.recall_relevant_experience(query=query)
    return {
        "query": query,
        "count": len(memories),
        "results": [m.dict() for m in memories]
    }


# =========================================================================
# FEEDBACK ENDPOINTS
# =========================================================================

@app.get("/api/feedback")
def list_feedback(week: Optional[int] = None, product_area: Optional[str] = None):
    items = all_feedback
    if week is not None:
        items = [f for f in items if f.week == week]
    if product_area:
        items = [f for f in items if f.product_area.value == product_area]
    return [f.dict() for f in items]


# =========================================================================
# CAPABILITY A: DETECT
# =========================================================================

@app.post("/api/agent/detect")
def detect_problems(current_week: int = 3, prior_week: int = 2):
    """
    Executes Capability A: DETECT.
    Deterministically computes complaint frequencies, growth trends, segment concentrations,
    and classifies severity.
    """
    metrics = compute_feedback_metrics(all_feedback, current_week=current_week, prior_week=prior_week)
    problems = build_detected_problems(metrics, feedback_dict)

    global active_problems
    active_problems = {p.id: p for p in problems}

    return {
        "current_week": current_week,
        "prior_week": prior_week,
        "problems_count": len(problems),
        "problems": [p.dict() for p in problems]
    }


# =========================================================================
# CAPABILITY B: DECIDE AND ACT
# =========================================================================

class DecideRequest(BaseModel):
    problem_id: str


@app.post("/api/agent/decide")
def decide_action(req: DecideRequest):
    """
    Executes Capability B: DECIDE.
    Recalls organizational memories from Hindsight, synthesizes reasoning,
    contrasts with vs without memory, and creates a bounded ProductAction.
    """
    problem = active_problems.get(req.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{req.problem_id}' not found. Run /api/agent/detect first.")

    # RECALL from Hindsight
    query = f"{problem.product_area.value} {problem.segment.value} {problem.title}"
    recalled_memories = hindsight_manager.recall_relevant_experience(query=query)

    # Generate bounded action
    action = generate_product_action(
        problem=problem,
        recalled_memories=recalled_memories,
        action_id=f"ACT-2026-{len(active_actions)+1:03d}"
    )

    active_actions[action.id] = action

    return {
        "action": action.dict(),
        "recalled_memories_count": len(recalled_memories),
        "recalled_memories": [m.dict() for m in recalled_memories]
    }


class TransitionRequest(BaseModel):
    action_id: str
    target_state: ActionState


@app.post("/api/agent/action/transition")
def transition_action_state(req: TransitionRequest):
    """
    Human-in-the-Loop approval gate for bounded product actions.
    Enforces ActionStateMachine transitions.
    """
    action = active_actions.get(req.action_id)
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{req.action_id}' not found.")

    try:
        previous_state = action.status.value
        updated_action = ActionStateMachine.transition(action, req.target_state)
        active_actions[action.id] = updated_action
        return {
            "status": "success",
            "action_id": updated_action.id,
            "previous_state": previous_state,
            "new_state": updated_action.status.value,
            "action": updated_action.dict()
        }
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# CAPABILITY C: MEASURE AND LEARN
# =========================================================================

class MeasureRequest(BaseModel):
    action_id: str
    pre_week: int = 3
    post_week: int = 4


@app.post("/api/agent/measure")
def measure_action_outcome(req: MeasureRequest):
    """
    Executes Capability C: MEASURE.
    Deterministically computes pre vs post intervention complaint volume and sentiment shift.
    Classifies outcome (SUCCESS / PARTIAL_SUCCESS / NO_CLEAR_IMPACT / REGRESSION).
    """
    action = active_actions.get(req.action_id)
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{req.action_id}' not found.")

    # Advance state to MEASURING
    if action.status == ActionState.APPROVED:
        ActionStateMachine.transition(action, ActionState.EXECUTED)
    if action.status == ActionState.EXECUTED:
        ActionStateMachine.transition(action, ActionState.MEASURING)

    measurement = evaluate_intervention_impact(
        action=action,
        feedback_items=all_feedback,
        pre_week=req.pre_week,
        post_week=req.post_week
    )

    active_measurements[action.id] = measurement

    return {
        "measurement": measurement.dict(),
        "action": action.dict()
    }


class LearnRequest(BaseModel):
    action_id: str


@app.post("/api/agent/learn")
def store_lesson_in_hindsight(req: LearnRequest):
    """
    Executes Capability C: LEARN (Retain back into Hindsight).
    Distills the intervention lifecycle into new organizational memory.
    """
    action = active_actions.get(req.action_id)
    measurement = active_measurements.get(req.action_id)

    if not action or not measurement:
        raise HTTPException(status_code=404, detail="Action or measurement not found. Run /api/agent/measure first.")

    # Format distilled memory
    content = (
        f"Action {action.id} [{measurement.outcome.value}]: Intervention '{action.title}' "
        f"for {action.product_area.value} ({action.affected_segment.value}). "
        f"Complaints shifted by {measurement.complaint_delta_pct}% (from {measurement.pre_complaint_count} down to {measurement.post_complaint_count}). "
        f"Sentiment shifted by +{measurement.sentiment_delta}. "
        f"Lesson: {measurement.lesson_learned}"
    )

    tags = [
        action.id,
        "OUTCOME",
        "LESSON",
        action.product_area.value,
        action.affected_segment.value,
        measurement.outcome.value
    ]

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

    # RETAIN into Hindsight
    retain_id = hindsight_manager.retain_decision_lifecycle(
        category="LESSON",
        content=content,
        tags=tags,
        metadata=metadata
    )

    # Transition action to COMPLETED if not already
    if action.status != ActionState.COMPLETED:
        ActionStateMachine.transition(action, ActionState.COMPLETED)
    measurement.hindsight_memory_id = retain_id

    return {
        "status": "success",
        "message": "Lesson successfully distilled and retained into Hindsight organizational memory!",
        "retained_content": content,
        "tags": tags,
        "action_status": action.status.value
    }


@app.post("/api/agent/challenge")
def create_challenge_incident():
    """
    Creates a realistic second incident (Android Biometric Checkout Failure & 3DS Auth Timeout)
    to demonstrate the Continuous Learning Loop and verify that Hindsight memory
    adapts future reasoning on a related but non-identical problem.
    """
    challenge_problem = DetectedProblem(
        id="prob-challenge-002",
        product_area=ProductArea.CHECKOUT_PAYMENTS,
        segment=CustomerSegment.ANDROID,
        title="Android Biometric Checkout Failure & 3DS Auth Timeout",
        complaint_count=18,
        prior_period_count=2,
        trend_pct=800.0,
        sentiment_avg=-0.84,
        severity=Severity.CRITICAL,
        why_it_matters=(
            "Following app release v4.13.0, Android users report BiometricPrompt freezing and 3DS auth timeouts "
            "during GooglePay checkout confirmation. Checkout conversion has dropped 14% on Android 14/15."
        ),
        sample_feedback_ids=["fb-bio-101", "fb-bio-102", "fb-bio-103"],
        detected_at=datetime.utcnow()
    )
    active_problems[challenge_problem.id] = challenge_problem
    return {
        "status": "success",
        "message": "Challenge incident loaded into ProductPulse detection engine.",
        "problem": challenge_problem.dict() if hasattr(challenge_problem, "dict") else challenge_problem.model_dump()
    }


@app.post("/api/agent/reflect")
def reflect_on_product_knowledge(query: str = Body(..., embed=True)):
    """
    Queries Hindsight REFLECT to demonstrate synthesis across both historical
    incident INC-104 and the newly learned action ACT-2026-081!
    """
    reflection = hindsight_manager.reflect_on_decision(query)
    return {
        "query": query,
        "reflection": reflection
    }


# =========================================================================
# STATIC FILES & SPA SERVING
# =========================================================================

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
