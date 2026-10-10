import asyncio
import json

import pytest

from adapters.events.sse_publisher import SsePublisher


@pytest.mark.asyncio
async def test_publish_delivers_json_and_unsubscribes():
    publisher = SsePublisher()
    subscriber = publisher.subscribe()
    pending_event = asyncio.create_task(anext(subscriber))
    await asyncio.sleep(0)

    await publisher.publish({"type": "booking.created"})

    assert json.loads(await pending_event) == {"type": "booking.created"}
    await subscriber.aclose()
    assert not publisher._subscribers


@pytest.mark.asyncio
async def test_publish_drops_oldest_event_when_queue_is_full():
    publisher = SsePublisher()
    subscriber = publisher.subscribe()
    pending_event = asyncio.create_task(anext(subscriber))
    await asyncio.sleep(0)

    for sequence in range(101):
        await publisher.publish({"sequence": sequence})

    assert json.loads(await pending_event) == {"sequence": 1}
    await subscriber.aclose()


@pytest.mark.asyncio
async def test_subscriber_yields_heartbeat_on_timeout(monkeypatch):
    publisher = SsePublisher()

    async def timeout(awaitable, **_kwargs):
        awaitable.close()
        raise TimeoutError

    monkeypatch.setattr(asyncio, "wait_for", timeout)
    subscriber = publisher.subscribe()

    assert await anext(subscriber) == ""
    await subscriber.aclose()
