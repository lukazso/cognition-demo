"""Connector to the feature flag configuration store (fake implementation for the POC)."""

from platform_core.connectors import Command, Err, ErrKind, FakeConnector

from flags_app.models import FeatureFlag, FlagState

# id, key, description, owner_team, state, staging, prod, rollout, created_at
_SEED = [
    ("flag-1001", "checkout.new-payment-flow", "New checkout payment flow", "payments",
     "active", True, True, 10, "2026-07-02T09:00:00Z"),
    ("flag-1002", "checkout.express-guest", "Guest express checkout", "payments",
     "active", True, False, 0, "2026-07-08T13:20:00Z"),
    ("flag-1003", "growth.referral-banner", "Referral banner on the home page", "growth",
     "active", True, True, 50, "2026-07-11T10:45:00Z"),
    ("flag-1004", "growth.onboarding-v3", "Third iteration of onboarding", "growth",
     "draft", False, False, 0, "2026-07-19T08:30:00Z"),
    ("flag-1005", "risk.device-fingerprinting", "Device fingerprinting in risk scoring", "risk",
     "active", True, True, 100, "2026-07-21T15:05:00Z"),
    ("flag-1006", "risk.manual-review-queue", "Route flagged users to manual review", "risk",
     "active", False, False, 0, "2026-07-28T11:12:00Z"),
    ("flag-1007", "platform.new-audit-viewer", "Rebuilt audit trail viewer", "platform",
     "draft", False, False, 0, "2026-08-03T09:40:00Z"),
    ("flag-1008", "platform.rate-limit-v2", "Second generation rate limiter", "platform",
     "active", True, True, 25, "2026-08-06T16:55:00Z"),
    ("flag-1009", "billing.invoice-pdf-v2", "Redesigned invoice PDFs", "billing",
     "active", True, False, 0, "2026-08-10T12:00:00Z"),
    ("flag-1010", "billing.legacy-tax-engine", "Legacy tax engine fallback", "billing",
     "archived", False, False, 0, "2026-05-14T10:10:00Z"),
    ("flag-1011", "growth.holiday-promo-2025", "Holiday promotion campaign", "growth",
     "archived", False, False, 0, "2026-04-02T07:25:00Z"),
    ("flag-1012", "payments.retry-orchestrator", "Smart payment retries", "payments",
     "active", True, True, 100, "2026-08-18T14:35:00Z"),
]


class FlagConnector(FakeConnector):
    resource_type = "feature_flag"

    def __init__(self) -> None:
        super().__init__()
        for id_, key, description, team, state, staging, prod, rollout, created in _SEED:
            flag = FeatureFlag(
                id=id_,
                key=key,
                description=description,
                owner_team=team,
                state=FlagState(state),
                staging_enabled=staging,
                prod_enabled=prod,
                prod_rollout_pct=rollout,
                created_at=created,
            )
            self.records[id_] = flag.model_dump(mode="json")

    def apply_command(self, record: dict, command: Command) -> Err | None:
        """Apply a command to the flag, rejecting domain preconditions the state machine
        cannot express (rollout needs production on, archiving needs production off)."""
        payload = command.payload
        if command.name == "activate":
            record["state"] = "active"
            note = "Activated"
        elif command.name == "set_staging":
            record["staging_enabled"] = payload["enabled"]
            note = "Staging enabled" if payload["enabled"] else "Staging disabled"
        elif command.name == "set_production":
            record["prod_enabled"] = payload["enabled"]
            if not payload["enabled"]:
                record["prod_rollout_pct"] = 0
            note = payload["reason"]
        elif command.name == "set_rollout":
            if not record["prod_enabled"]:
                return Err(
                    kind=ErrKind.CONFLICT,
                    message="Rollout can only be changed while production is enabled",
                )
            record["prod_rollout_pct"] = payload["percentage"]
            note = payload["reason"]
        elif command.name == "archive":
            if record["prod_enabled"]:
                return Err(
                    kind=ErrKind.CONFLICT,
                    message="Disable the flag in production before archiving it",
                )
            record["state"] = "archived"
            note = payload["note"]
        else:
            return Err(kind=ErrKind.INVALID_REQUEST, message=f"Unknown command {command.name}")
        record["updated_by"] = payload.get("actor_id")
        record["change_note"] = note
        return None
