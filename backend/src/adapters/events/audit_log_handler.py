from datetime import UTC

from domain.events.events import (
    BookingCancelled,
    BookingConfirmed,
    BookingCreated,
    BookingExpired,
    DomainEvent,
    QuotaConsumed,
)
from domain.repositories.audit_log_repository import AuditLogRepository


class AuditLogHandler:
    """Consumes domain events and records audit log entries."""

    def __init__(self, audit_log_repo: AuditLogRepository):
        self.audit_log_repo = audit_log_repo

    async def handle(self, event: DomainEvent) -> None:
        now = event.occurred_at.astimezone(UTC).replace(tzinfo=None)
        if isinstance(event, BookingCreated):
            await self.audit_log_repo.create(
                actor_id=event.employee_id,
                action="created",
                entity_type="booking",
                entity_id=str(event.booking_id),
                timestamp=now,
                reason="booking created",
            )
        elif isinstance(event, BookingConfirmed):
            await self.audit_log_repo.create(
                actor_id=event.employee_id,
                action="checked_in",
                entity_type="booking",
                entity_id=str(event.booking_id),
                timestamp=now,
                reason="QR check-in",
            )
        elif isinstance(event, BookingCancelled):
            await self.audit_log_repo.create(
                actor_id=event.employee_id,
                action="cancelled",
                entity_type="booking",
                entity_id=str(event.booking_id),
                timestamp=now,
                reason="booking cancelled",
            )
        elif isinstance(event, BookingExpired):
            await self.audit_log_repo.create(
                actor_id=event.employee_id,
                action="expired",
                entity_type="booking",
                entity_id=str(event.booking_id),
                timestamp=now,
                reason="no-show expired",
            )
        elif isinstance(event, QuotaConsumed):
            await self.audit_log_repo.create(
                actor_id=None,
                action="quota_consumed",
                entity_type="quota_period",
                entity_id=str(event.cost_center_id),
                timestamp=now,
                reason=f"consumed {event.delta_hours}h, total {event.consumed_hours}/{event.total_hours}",
            )