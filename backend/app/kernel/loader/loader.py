import asyncio
import json
from pathlib import Path

from app.event_bus import event_bus
from app.schemas.enums import (
    EventSeverity,
    EventSource,
    EventType,
)
from app.schemas.event import Event


class KernelLoader:

    def __init__(self):
        self.process = None
        self.reader_task = None

    async def start(self):

        loader = (
            Path(__file__)
            .parent
            / "native"
            / "loader"
        )

        self.process = await asyncio.create_subprocess_exec(
            "sudo",
            str(loader),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self.reader_task = asyncio.create_task(
            self.read_events()
        )

    async def read_events(self):

        if not self.process or not self.process.stdout:
            return

        while True:

            line = await self.process.stdout.readline()

            if not line:
                break

            text = line.decode().strip()

            if not text.startswith("{"):
                continue

            try:
                payload = json.loads(text)

                event = Event(
                    source=EventSource.KERNEL,

                    event_type=EventType.PROCESS_STARTED,

                    severity=EventSeverity.INFO,

                    host="localhost",

                    pid=payload.get("pid"),

                    process_name=payload.get("comm"),

                    username=str(payload.get("uid")),

                    metadata={
                        "kernel_event_type": payload.get("type"),
                        "kernel_timestamp": payload.get("timestamp"),
                    },
                )

                await event_bus.publish(event)

            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                print(f"[KernelLoader] Invalid event: {exc}")

    async def stop(self):

        if self.reader_task:
            self.reader_task.cancel()

            try:
                await self.reader_task
            except asyncio.CancelledError:
                pass

            self.reader_task = None

        if self.process:

            self.process.terminate()

            try:
                await asyncio.wait_for(
                    self.process.wait(),
                    timeout=2,
                )
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()

            self.process = None