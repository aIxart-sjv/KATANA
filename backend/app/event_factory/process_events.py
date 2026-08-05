from app.schemas.enums import (
    EventSeverity,
    EventSource,
    EventType,
)
from app.schemas.event import Event
from app.state.process_snapshot import ProcessInfo


def process_started(
    process: ProcessInfo,
    host: str,
) -> Event:
    return Event(
        source=EventSource.PROCESS,
        event_type=EventType.PROCESS_STARTED,
        severity=EventSeverity.INFO,
        host=host,
        pid=process.pid,
        process_name=process.name,
        parent_pid=process.ppid,
        username=process.username,
        cpu_percent=process.cpu_percent,
        memory_percent=process.memory_percent,
    )


def process_terminated(
    process: ProcessInfo,
    host: str,
) -> Event:
    return Event(
        source=EventSource.PROCESS,
        event_type=EventType.PROCESS_TERMINATED,
        severity=EventSeverity.INFO,
        host=host,
        pid=process.pid,
        process_name=process.name,
        parent_pid=process.ppid,
        username=process.username,
        cpu_percent=process.cpu_percent,
        memory_percent=process.memory_percent,
    )