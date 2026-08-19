from datetime import datetime, timedelta, UTC

from app.schemas.event import Event


class EventWindow:

    def __init__(self, duration_seconds: int = 10):
        self.duration = timedelta(seconds=duration_seconds)
        self.events: list[Event] = []

    def add(self, event: Event) -> None:
        self.events.append(event)
        self._cleanup()

    def _cleanup(self) -> None:
        if not self.events:
            return

        cutoff = datetime.now(UTC) - self.duration

        self.events = [
            event
            for event in self.events
            if event.timestamp >= cutoff
        ]

    def get_events(self) -> list[Event]:
        self._cleanup()
        return list(self.events)

    def clear(self) -> None:
        self.events.clear()

    @property
    def size(self) -> int:
        self._cleanup()
        return len(self.events)