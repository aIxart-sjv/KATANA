import asyncio
from collections.abc import Awaitable, Callable

from app.schemas.event import Event

Subscriber = Callable[[Event], Awaitable[None]]


class EventBus:
    def __init__(self):
        self._subscribers: list[Subscriber] = []

    def subscribe(self, subscriber: Subscriber):
        self._subscribers.append(subscriber)

    async def publish(self, event: Event):
        if not self._subscribers:
            return

        await asyncio.gather(
            *(subscriber(event) for subscriber in self._subscribers),
            return_exceptions=True,
        )