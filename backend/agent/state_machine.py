"""
Bounded Action State Machine for ProductPulse.
Manages strict lifecycle transitions for AI-proposed actions, ensuring human oversight
and preventing silent autonomous execution.
"""

from datetime import datetime
from typing import Dict, Optional
from ..data.schema import ProductAction, ActionState


class InvalidStateTransitionError(Exception):
    pass


class ActionStateMachine:
    VALID_TRANSITIONS = {
        ActionState.RECOMMENDED: {ActionState.APPROVED, ActionState.REJECTED},
        ActionState.APPROVED: {ActionState.EXECUTED, ActionState.REJECTED},
        ActionState.EXECUTED: {ActionState.MEASURING},
        ActionState.MEASURING: {ActionState.COMPLETED},
        ActionState.COMPLETED: set(),
        ActionState.REJECTED: set(),
    }

    @classmethod
    def transition(cls, action: ProductAction, target_state: ActionState) -> ProductAction:
        allowed = cls.VALID_TRANSITIONS.get(action.status, set())
        if target_state not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition action '{action.id}' from '{action.status.value}' to '{target_state.value}'. "
                f"Allowed target states: {[s.value for s in allowed]}"
            )

        now = datetime.utcnow()
        action.status = target_state

        if target_state == ActionState.APPROVED:
            action.approved_at = now
        elif target_state == ActionState.EXECUTED:
            action.executed_at = now
        elif target_state == ActionState.COMPLETED:
            action.completed_at = now

        return action
