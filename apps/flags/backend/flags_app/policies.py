"""Role -> action permissions and the state-transition table for feature flags."""

from platform_core.actions import ALL_ROLES, Action
from platform_core.auth import Role

from flags_app.models import (
    ActivateInput,
    ArchiveInput,
    CreateInput,
    SetProductionInput,
    SetRolloutInput,
    SetStagingInput,
)

OPERATORS_AND_UP = frozenset({Role.OPERATOR, Role.SUPERVISOR})
SUPERVISOR_ONLY = frozenset({Role.SUPERVISOR})
READ_ROLES = ALL_ROLES  # anyone in the team may look up a flag, only operators mutate

ACTIONS: list[Action] = [
    Action(
        name="flags.create",
        command="create",
        allowed_roles=OPERATORS_AND_UP,
        creates_resource=True,
        input_schema=CreateInput,
    ),
    Action(
        name="flags.activate",
        command="activate",
        allowed_roles=OPERATORS_AND_UP,
        valid_from_states=frozenset({"draft"}),
        to_state="active",
        input_schema=ActivateInput,
    ),
    Action(
        name="flags.set_staging",
        command="set_staging",
        allowed_roles=OPERATORS_AND_UP,
        valid_from_states=frozenset({"active"}),
        input_schema=SetStagingInput,
    ),
    Action(
        name="flags.set_production",
        command="set_production",
        allowed_roles=SUPERVISOR_ONLY,
        valid_from_states=frozenset({"active"}),
        input_schema=SetProductionInput,
    ),
    Action(
        name="flags.set_rollout",
        command="set_rollout",
        allowed_roles=SUPERVISOR_ONLY,
        valid_from_states=frozenset({"active"}),
        input_schema=SetRolloutInput,
    ),
    Action(
        name="flags.archive",
        command="archive",
        allowed_roles=SUPERVISOR_ONLY,
        valid_from_states=frozenset({"active"}),
        to_state="archived",
        input_schema=ArchiveInput,
    ),
]
