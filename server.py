"""Dev server entrypoint: ``uvicorn server:app --reload``"""

from platform_core.http import create_app

from apps.registry import TOOLS

app = create_app(TOOLS)
