"""Wires the KYC tool into the platform HTTP layer."""

from platform_core.http import ToolConfig

from kyc_app.connector import KycConnector
from kyc_app.policies import ACTIONS, READ_ROLES


def make_tool() -> ToolConfig:
    """Fresh ToolConfig with its own fake system of record (used by tests)."""
    return ToolConfig(
        tool_id="kyc",
        connector=KycConnector(),
        actions=ACTIONS,
        read_roles=READ_ROLES,
    )


TOOL = make_tool()
