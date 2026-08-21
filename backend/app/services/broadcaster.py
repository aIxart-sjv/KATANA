from app.event_store.store import event_store
from app.schemas.event import Event
from app.state.dashboard import dashboard_state
from app.websocket.manager import manager


async def broadcast_event(event: Event):
    # Store event for pipeline analysis.
    event_store.add(event)

    # Update dashboard statistics.
    dashboard_state.record_event()

    # Broadcast raw live event to connected frontend clients.
    await manager.broadcast(
        event.model_dump(mode="json")
    )