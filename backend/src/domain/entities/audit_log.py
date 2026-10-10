from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class AuditLog:
    """Append-only audit log entity."""

    id: UUID = field(default_factory=uuid4)
    action: str
    entity_type: str  # Booking, Workspace, QuotaPeriod, etc.
    actor_id: UUID | None = None  # NULL for system actions (ex: cron)
    entity_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    reason: str = ""

    def __post_init__(self) -> None:
        if self.action is None:
            raise ValueError("action is required")
        if self.entity_type is None:
            raise ValueError("entity_type is required")