"""FastAPI glue shared by all tools: app factory, error mapping, and the standard
tool router (queue / detail / action invocation) generated from a ToolConfig."""

from dataclasses import dataclass, field

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from platform_core import audit
from platform_core.actions import (
    ALL_ROLES,
    Action,
    ActionError,
    InvalidInput,
    InvalidTransition,
    PermissionDenied,
    ResourceNotFound,
    UpstreamFailure,
    actions_available,
    authorize_read,
    run_action,
)
from platform_core.auth import MOCK_USERS, Role, User, get_current_user
from platform_core.connectors import Connector, Err, ErrKind, Query
from pydantic import BaseModel

_STATUS = {
    PermissionDenied: 403,
    InvalidTransition: 409,
    InvalidInput: 422,
    ResourceNotFound: 404,
    UpstreamFailure: 502,
}


def _http_error(exc: ActionError) -> HTTPException:
    return HTTPException(
        status_code=_STATUS.get(type(exc), 500),
        detail={"outcome": exc.outcome, "message": exc.message},
    )


@dataclass(frozen=True)
class ToolConfig:
    """Everything the platform needs to expose a tool over HTTP."""

    tool_id: str  # url segment, e.g. "kyc"
    connector: Connector
    actions: list[Action]
    read_roles: frozenset[Role] = field(default_factory=lambda: ALL_ROLES)


class ActionRequest(BaseModel):
    idempotency_key: str
    input: dict = {}


def build_tool_router(config: ToolConfig) -> APIRouter:
    router = APIRouter(prefix=f"/api/{config.tool_id}")
    actions_by_name = {a.name: a for a in config.actions}

    @router.get("/resources")
    def list_resources(
        state: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
        user: User = Depends(get_current_user),
    ):
        try:
            authorize_read(user, config.read_roles)
        except ActionError as exc:
            raise _http_error(exc) from exc
        filters = {"state": state} if state else {}
        result = config.connector.list(
            Query(filters=filters, search=search, page=page, page_size=page_size)
        )
        if isinstance(result, Err):
            raise HTTPException(status_code=502, detail={"outcome": "upstream_failure",
                                                         "message": result.message})
        return {"items": result.value.items, "total": result.value.total}

    @router.get("/resources/{resource_id}")
    def get_resource(resource_id: str, user: User = Depends(get_current_user)):
        try:
            authorize_read(user, config.read_roles)
        except ActionError as exc:
            raise _http_error(exc) from exc
        result = config.connector.get(resource_id)
        if isinstance(result, Err):
            status = 404 if result.kind == ErrKind.NOT_FOUND else 502
            raise HTTPException(status_code=status, detail={"outcome": result.kind.value,
                                                            "message": result.message})
        resource = result.value
        return {
            "resource": resource,
            "available_actions": actions_available(config.actions, user, resource.get("state", "")),
            "audit": [
                r.model_dump()
                for r in audit.list_for_resource(config.connector.resource_type, resource_id)
            ],
        }

    @router.post("/resources/{resource_id}/actions/{action_name}")
    def invoke_action(
        resource_id: str,
        action_name: str,
        request: ActionRequest,
        user: User = Depends(get_current_user),
    ):
        action = actions_by_name.get(f"{config.tool_id}.{action_name}") or actions_by_name.get(
            action_name
        )
        if action is None:
            raise HTTPException(status_code=404, detail={"outcome": "unknown_action",
                                                         "message": action_name})
        try:
            result = run_action(
                action=action,
                actor=user,
                resource_id=resource_id,
                connector=config.connector,
                input_data=request.input,
                idempotency_key=request.idempotency_key,
            )
        except ActionError as exc:
            raise _http_error(exc) from exc
        return {
            "resource": result.resource,
            "new_state": result.new_state,
            "replayed": result.replayed,
        }

    return router


def create_app(tool_configs: list[ToolConfig]) -> FastAPI:
    app = FastAPI(title="Internal Tools POC")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/me")
    def me(user: User = Depends(get_current_user)):
        return user

    @app.get("/api/roles")
    def roles():
        return [u.model_dump() for u in MOCK_USERS.values()]

    for config in tool_configs:
        app.include_router(build_tool_router(config))
    return app
