from collections import deque
from datetime import UTC, datetime, timedelta

from app.schemas.event import Event


class EventWindow:
    def __init__(self, duration_seconds: int):
        self.duration = timedelta(seconds=duration_seconds)
        self.events: deque[Event] = deque()

    def add(self, event: Event):
        self.events.append(event)
        self.cleanup()

    def cleanup(self):
        cutoff = datetime.now(UTC) - self.duration

        while self.events and self.events[0].timestamp < cutoff:
            self.events.popleft()

    def get_events(self) -> list[Event]:
        self.cleanup()
        return list(self.events)

    def clear(self):
        self.events.clear()