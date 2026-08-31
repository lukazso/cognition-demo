"""Wires the feature flag tool into the platform HTTP layer."""

from platform_core.http import ToolConfig

from flags_app.connector import FlagConnector
from flags_app.policies import ACTIONS, READ_ROLES


def make_tool() -> ToolConfig:
    """Fresh ToolConfig with its own fake flag store (used by tests)."""
    return ToolConfig(
        tool_id="flags",
        connector=FlagConnector(),
        actions=ACTIONS,
        read_roles=READ_ROLES,
    )


TOOL = make_tool()
