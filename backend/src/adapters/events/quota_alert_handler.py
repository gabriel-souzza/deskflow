from decimal import Decimal
from typing import Protocol

from domain.events.events import QuotaAlert, QuotaConsumed


class AlertEventPublisher(Protocol):
    async def publish(self, event: dict) -> None: ...


class QuotaAlertHandler:
    """RF15: Dispara alertas quando o centro de custo atinge 80% ou 95% da cota mensal."""

    def __init__(self, publisher: AlertEventPublisher):
        self.publisher = publisher

    async def handle_quota_consumed(self, event: QuotaConsumed) -> QuotaAlert | None:
        if event.total_hours <= Decimal(0):
            return None

        current_ratio = event.consumed_hours / event.total_hours
        prev_consumed = event.consumed_hours - event.delta_hours
        prev_ratio = prev_consumed / event.total_hours if event.total_hours > 0 else Decimal(0)

        alert_threshold = None
        if current_ratio >= Decimal("0.95") and prev_ratio < Decimal("0.95"):
            alert_threshold = 95
        elif current_ratio >= Decimal("0.80") and prev_ratio < Decimal("0.80"):
            alert_threshold = 80

        if alert_threshold is not None:
            alert = QuotaAlert(
                cost_center_id=event.cost_center_id,
                threshold_percent=alert_threshold,
                consumed_hours=event.consumed_hours,
                total_hours=event.total_hours,
            )
            await self.publisher.publish(
                {
                    "type": "quota.alert",
                    "cost_center_id": str(event.cost_center_id),
                    "threshold_percent": alert_threshold,
                    "consumed_hours": float(event.consumed_hours),
                    "total_hours": float(event.total_hours),
                    "message": f"Cost center has reached {alert_threshold}% of its monthly quota limit.",
                }
            )
            return alert
        return None