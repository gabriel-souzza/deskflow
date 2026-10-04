# DomainEvent -> SSE Stream adapter
import asyncio
import json


class SsePublisher:
    def __init__(self):
        self._subscribers: set[asyncio.Queue[str]] = set()

    async def publish(self, event: dict) -> None:
        message = json.dumps(event, separators=(",", ":"))
        for queue in tuple(self._subscribers):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(message)

    async def subscribe(self):
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        try:
            while True:
                try:
                    yield await asyncio.wait_for(queue.get(), timeout=20)
                except TimeoutError:
                    yield ""
        finally:
            self._subscribers.discard(queue)


sse_publisher = SsePublisher()
