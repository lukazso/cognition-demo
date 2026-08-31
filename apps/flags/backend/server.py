from platform_core.http import create_app

from flags_app.config import TOOL

app = create_app([TOOL])
