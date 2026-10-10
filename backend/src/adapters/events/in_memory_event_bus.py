from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import TypeVar

from domain.events.event_bus import EventBus
from domain.events.events import DomainEvent

E = TypeVar("E", bound=DomainEvent)


class InMemoryEventBus(EventBus):
    """In-memory event bus implementation for async event dispatching."""

    def __init__(self):
        self._subscribers: dict[type[DomainEvent], list[Callable[[DomainEvent], Awaitable[None]]]] = (
            defaultdict(list)
        )

    def subscribe(
        self,
        event_type: type[E],
        handler: Callable[[E], Awaitable[None]],
    ) -> None:
        self._subscribers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        event_type = type(event)
        # Call handlers for exact type and base classes
        for registered_type, handlers in self._subscribers.items():
            if issubclass(event_type, registered_type):
                for handler in handlers:
                    await handler(event)


event_bus = InMemoryEventBus()
