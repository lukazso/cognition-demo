"""Role -> action permissions and the state-transition table for KYC cases."""

from platform_core.actions import ALL_ROLES, Action
from platform_core.auth import Role

from kyc_app.models import ApproveInput, EscalateInput, RejectInput, StartReviewInput

OPERATORS_AND_UP = frozenset({Role.OPERATOR, Role.SUPERVISOR})
SUPERVISOR_ONLY = frozenset({Role.SUPERVISOR})
READ_ROLES = ALL_ROLES  # viewers may read, never mutate

ACTIONS: list[Action] = [
    Action(
        name="kyc.start_review",
        command="start_review",
        allowed_roles=OPERATORS_AND_UP,
        valid_from_states=frozenset({"pending"}),
        to_state="in_review",
        input_schema=StartReviewInput,
    ),
    Action(
        name="kyc.escalate",
        command="escalate",
        allowed_roles=OPERATORS_AND_UP,
        valid_from_states=frozenset({"in_review"}),
        to_state="escalated",
        input_schema=EscalateInput,
    ),
    Action(
        name="kyc.approve",
        command="approve",
        allowed_roles=SUPERVISOR_ONLY,
        valid_from_states=frozenset({"in_review", "escalated"}),
        to_state="approved",
        input_schema=ApproveInput,
    ),
    Action(
        name="kyc.reject",
        command="reject",
        allowed_roles=SUPERVISOR_ONLY,
        valid_from_states=frozenset({"in_review", "escalated"}),
        to_state="rejected",
        input_schema=RejectInput,
    ),
]
