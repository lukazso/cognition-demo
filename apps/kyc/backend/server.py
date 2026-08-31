from platform_core.http import create_app

from kyc_app.config import TOOL

app = create_app([TOOL])
