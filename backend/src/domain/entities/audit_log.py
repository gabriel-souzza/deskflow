from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class AuditLog:
    """Append-only audit log entity."""
    id: UUID = field(default_factory=uuid4)
    actor_id: UUID = None  # NULL for system actions (ex: cron)
    action: str = None
    entity_type: str = None  # Booking, Workspace, QuotaPeriod, etc.
    entity_id: str = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = ""

    def __post_init__(self):
        if self.action is None:
            raise ValueError("action is required")
        if self.entity_type is None:
            raise ValueError("entity_type is required")