from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TypeVar

from domain.events.events import DomainEvent

E = TypeVar("E", bound=DomainEvent)


class EventBus(ABC):
    """Interface for publishing and subscribing to domain events."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all registered subscribers."""

    @abstractmethod
    def subscribe(
        self,
        event_type: type[E],
        handler: Callable[[E], Awaitable[None]],
    ) -> None:
        """Register an async handler for a specific domain event type."""
