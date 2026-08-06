from app.event_store.store import event_store
from app.schemas.event import Event
from app.websocket.manager import manager


async def broadcast_event(event: Event):
    event_store.add(event)

    await manager.broadcast(
        event.model_dump(mode="json")
    )