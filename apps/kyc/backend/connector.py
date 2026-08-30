"""Connector to the KYC system of record (fake implementation for the POC)."""

from platform_core.connectors import Command, Err, ErrKind, FakeConnector

from apps.kyc.backend.models import KycCase, KycState

_SEED = [
    ("kyc-1001", "Amara Okafor", "amara.okafor@example.com", "NG", 22, "pending", "2026-08-24T09:15:00Z"),
    ("kyc-1002", "Jonas Weber", "jonas.weber@example.com", "DE", 8, "pending", "2026-08-24T11:40:00Z"),
    ("kyc-1003", "Priya Sharma", "priya.sharma@example.com", "IN", 55, "in_review", "2026-08-25T08:05:00Z"),
    ("kyc-1004", "Liam O'Connor", "liam.oconnor@example.com", "IE", 31, "pending", "2026-08-25T14:22:00Z"),
    ("kyc-1005", "Sofia Rossi", "sofia.rossi@example.com", "IT", 77, "escalated", "2026-08-26T10:48:00Z"),
    ("kyc-1006", "Chen Wei", "chen.wei@example.com", "SG", 12, "in_review", "2026-08-26T16:30:00Z"),
    ("kyc-1007", "Fatima Al-Sayed", "fatima.alsayed@example.com", "AE", 64, "pending", "2026-08-27T07:55:00Z"),
    ("kyc-1008", "Lucas Silva", "lucas.silva@example.com", "BR", 41, "pending", "2026-08-27T13:10:00Z"),
    ("kyc-1009", "Emma Johansson", "emma.johansson@example.com", "SE", 5, "approved", "2026-08-27T15:33:00Z"),
    ("kyc-1010", "David Kim", "david.kim@example.com", "KR", 89, "rejected", "2026-08-28T09:02:00Z"),
    ("kyc-1011", "Nadia Petrova", "nadia.petrova@example.com", "BG", 47, "pending", "2026-08-28T12:44:00Z"),
    ("kyc-1012", "Tom Becker", "tom.becker@example.com", "DE", 18, "in_review", "2026-08-29T08:20:00Z"),
]


class KycConnector(FakeConnector):
    resource_type = "kyc_case"

    def __init__(self) -> None:
        super().__init__()
        for id_, name, email, country, risk, state, submitted in _SEED:
            case = KycCase(
                id=id_,
                applicant_name=name,
                email=email,
                country=country,
                risk_score=risk,
                documents=["passport.pdf", "proof_of_address.pdf"],
                state=KycState(state),
                submitted_at=submitted,
            )
            self.records[id_] = case.model_dump(mode="json")

    def apply_command(self, record: dict, command: Command) -> Err | None:
        actor_id = command.payload.get("actor_id")
        if command.name == "start_review":
            record["state"] = "in_review"
            record["reviewer_id"] = actor_id
        elif command.name == "escalate":
            record["state"] = "escalated"
            record["resolution_note"] = f"Escalated: {command.payload['reason']}"
        elif command.name == "approve":
            record["state"] = "approved"
            record["resolution_note"] = command.payload.get("note") or "Approved"
        elif command.name == "reject":
            record["state"] = "rejected"
            record["resolution_note"] = f"Rejected: {command.payload['reason']}"
        else:
            return Err(kind=ErrKind.INVALID_REQUEST, message=f"Unknown command {command.name}")
        return None
