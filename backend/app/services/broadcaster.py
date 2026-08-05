from app.schemas.event import Event
from app.websocket.manager import manager


async def broadcast_event(event: Event):
    await manager.broadcast(event.model_dump(mode="json"))