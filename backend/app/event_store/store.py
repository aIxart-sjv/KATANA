from app.schemas.event import Event
from app.event_store.window import EventWindow


class EventStore:
    def __init__(self):
        self.windows = {
            5: EventWindow(5),
            30: EventWindow(30),
            300: EventWindow(300),
        }

    def add(self, event: Event):
        for window in self.windows.values():
            window.add(event)

    def get_window(self, seconds: int) -> list[Event]:
        if seconds not in self.windows:
            raise ValueError(f"No window configured for {seconds} seconds")

        return self.windows[seconds].get_events()


event_store = EventStore()