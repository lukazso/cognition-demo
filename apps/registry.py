"""Registry of installed tools. A new tool adds exactly one line here."""

from platform_core.http import ToolConfig

from apps.kyc.backend.config import TOOL as KYC_TOOL

TOOLS: list[ToolConfig] = [
    KYC_TOOL,
]
