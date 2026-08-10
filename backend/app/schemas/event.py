from datetime import datetime, UTC
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.schemas.enums import (
    EventSeverity,
    EventSource,
    EventType,
)


class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    source: EventSource

    event_type: EventType

    severity: EventSeverity = EventSeverity.INFO

    host: str

    pid: int | None = None

    process_name: str | None = None

    parent_pid: int | None = None

    username: str | None = None

    cpu_percent: float | None = None

    memory_percent: float | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)

    remote_ip: str | None = None
    remote_port: int | None = None

    local_ip: str | None = None
    local_port: int | None = None