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


# ============================================================
# Native KATANA event IDs
# Defined in:
# app/kernel/headers/katana.h
# ============================================================

EVENT_EXEC = 1
EVENT_CONNECT = 2
EVENT_OPEN = 3
EVENT_UNLINK = 4
EVENT_SETUID = 5
EVENT_PTRACE = 6


class KernelLoader:

    def __init__(self):
        self.process = None
        self.reader_task = None
        self.stderr_task = None

    # ========================================================
    # Kernel event → application event mapping
    # ========================================================

    def map_event_type(
        self,
        kernel_type: int,
    ) -> EventType | None:

        mapping = {

            # execve()
            EVENT_EXEC:
                EventType.PROCESS_STARTED,

            # connect()
            EVENT_CONNECT:
                EventType.NETWORK_CONNECT,

            # openat()
            #
            # FILE_OPENED does not currently exist
            # in EventType, so use FILE_MODIFIED
            # until a dedicated FILE_OPENED type is added.
            EVENT_OPEN:
                EventType.FILE_MODIFIED,

            # unlink()
            EVENT_UNLINK:
                EventType.FILE_DELETED,

            # setuid()
            EVENT_SETUID:
                EventType.PRIVILEGE_ESCALATION,

            # ptrace()
            #
            # No PROCESS_TRACED type currently exists,
            # so map it to the existing security event.
            EVENT_PTRACE:
                EventType.PRIVILEGE_ESCALATION,
        }

        return mapping.get(kernel_type)

    # ========================================================
    # Severity mapping
    # ========================================================

    def get_severity(
        self,
        kernel_type: int,
    ) -> EventSeverity:

        if kernel_type in (
            EVENT_SETUID,
            EVENT_PTRACE,
        ):
            return EventSeverity.MEDIUM

        if kernel_type == EVENT_UNLINK:
            return EventSeverity.LOW

        return EventSeverity.INFO

    # ========================================================
    # Start native loader
    # ========================================================

    async def start(self):

        loader = (
            Path(__file__).parent
            / "native"
            / "loader"
        )

        if not loader.exists():

            raise FileNotFoundError(
                f"KATANA native loader not found: {loader}"
            )

        self.process = await asyncio.create_subprocess_exec(

            "sudo",
            str(loader),

            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # stdout → kernel events
        self.reader_task = asyncio.create_task(
            self.read_events()
        )

        # stderr → native loader diagnostics
        self.stderr_task = asyncio.create_task(
            self.read_stderr()
        )

    # ========================================================
    # Read native loader stdout
    # ========================================================

    async def read_events(self):

        if not self.process:
            return

        if not self.process.stdout:
            return

        while True:

            line = await self.process.stdout.readline()

            if not line:
                break

            text = line.decode(
                errors="replace"
            ).strip()

            # Native loader also prints startup messages.
            # Only JSON lines represent events.
            if not text.startswith("{"):
                continue

            try:

                payload = json.loads(text)

                # ------------------------------------------------
                # Kernel event type
                # ------------------------------------------------

                kernel_type = payload.get("type")

                if kernel_type is None:
                    continue

                kernel_type = int(kernel_type)

                event_type = self.map_event_type(
                    kernel_type
                )

                if event_type is None:

                    print(
                        "[KernelLoader] "
                        f"Unknown kernel event type: "
                        f"{kernel_type}"
                    )

                    continue

                # ------------------------------------------------
                # Basic event fields
                # ------------------------------------------------

                pid = payload.get("pid")
                ppid = payload.get("ppid")
                uid = payload.get("uid")

                comm = payload.get("comm") or None

                filename = (
                    payload.get("filename")
                    or None
                )

                # ------------------------------------------------
                # Network information
                # ------------------------------------------------

                ipv4 = (
                    payload.get("ipv4")
                    or None
                )

                port = payload.get("port")

                if port == 0:
                    port = None

                # ------------------------------------------------
                # Build application Event
                # ------------------------------------------------

                event = Event(

                    source=EventSource.KERNEL,

                    event_type=event_type,

                    severity=self.get_severity(
                        kernel_type
                    ),

                    host="localhost",

                    pid=pid,

                    process_name=comm,

                    parent_pid=ppid,

                    username=(
                        str(uid)
                        if uid is not None
                        else None
                    ),

                    remote_ip=ipv4,

                    remote_port=port,

                    metadata={

                        "kernel_event_type":
                            kernel_type,

                        "kernel_timestamp":
                            payload.get("timestamp"),

                        "kernel_family":
                            payload.get("family"),

                        "filename":
                            filename,
                    },
                )

                # ------------------------------------------------
                # Publish into KATANA event bus
                # ------------------------------------------------

                await event_bus.publish(event)

            except (
                json.JSONDecodeError,
                ValueError,
                TypeError,
            ) as exc:

                print(
                    "[KernelLoader] "
                    f"Invalid kernel event: {exc}"
                )

    # ========================================================
    # Read native loader stderr
    # ========================================================

    async def stop(self):
        if self.reader_task:
            self.reader_task.cancel()

            try:
                await self.reader_task
            except asyncio.CancelledError:
                pass

            self.reader_task = None

        if self.process:
            try:
                if self.process.returncode is None:
                    self.process.terminate()

                    try:
                        await asyncio.wait_for(
                            self.process.wait(),
                            timeout=2,
                        )
                    except asyncio.TimeoutError:
                        self.process.kill()
                        await self.process.wait()
                else:
                    # Process already exited; just reap it.
                    await self.process.wait()

            except ProcessLookupError:
                # Process disappeared between the check and terminate().
                pass

            finally:
                self.process = None