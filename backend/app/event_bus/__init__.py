from app.event_bus.bus import EventBus
from app.services.broadcaster import broadcast_event

event_bus = EventBus()

event_bus.subscribe(broadcast_event)