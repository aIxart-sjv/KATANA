from app.event_factory.process_events import (
    process_started,
    process_terminated,
)
from app.schemas.event import Event
from app.state.process_snapshot import ProcessInfo


def compare_processes(
    previous: dict[int, ProcessInfo],
    current: dict[int, ProcessInfo],
    host: str,
) -> list[Event]:

    events: list[Event] = []

    new = current.keys() - previous.keys()

    dead = previous.keys() - current.keys()

    for pid in new:
        events.append(
            process_started(
                current[pid],
                host,
            )
        )

    for pid in dead:
        events.append(
            process_terminated(
                previous[pid],
                host,
            )
        )

    return events