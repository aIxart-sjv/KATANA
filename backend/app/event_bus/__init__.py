from app.event_bus.bus import EventBus
from app.event_store.store import event_store
from app.services.broadcaster import broadcast_event

event_bus = EventBus()

event_bus.subscribe(event_store.add)
event_bus.subscribe(broadcast_event)