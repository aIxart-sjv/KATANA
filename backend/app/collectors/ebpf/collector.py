import asyncio
import ctypes
import socket
from pathlib import Path

from bcc import BPF

from app.event_bus import event_bus
from app.schemas.enums import (
    EventSeverity,
    EventSource,
    EventType,
)
from app.schemas.event import Event


class ExecEvent(ctypes.Structure):
    _fields_ = [
        ("pid", ctypes.c_uint),
        ("comm", ctypes.c_char * 16),
    ]


class EBPFCollector:

    def __init__(self):

        self.hostname = socket.gethostname()

        self.running = False

        self.queue = asyncio.Queue()

        program = (
            Path(__file__)
            .with_name("program.c")
            .resolve()
        )

        self.bpf = BPF(src_file=str(program))

        self.bpf.attach_kprobe(
            event="__x64_sys_execve",
            fn_name="trace_exec",
        )

    ###################################################

    def handle_event(
        self,
        cpu,
        data,
        size,
    ):

        event = ctypes.cast(
            data,
            ctypes.POINTER(ExecEvent),
        ).contents

        self.queue.put_nowait(
            {
                "pid": event.pid,
                "comm": event.comm.decode(),
            }
        )

    ###################################################

    async def process_queue(self):

        while self.running:

            item = await self.queue.get()

            event = Event(

                source=EventSource.KERNEL,

                event_type=EventType.PROCESS_STARTED,

                severity=EventSeverity.INFO,

                host=self.hostname,

                pid=item["pid"],

                process_name=item["comm"],
            )

            await event_bus.publish(event)

    ###################################################

    async def poll_perf_buffer(self):

        while self.running:

            self.bpf.perf_buffer_poll(timeout=100)

            await asyncio.sleep(0)

    ###################################################

    async def start(self):

        self.running = True

        self.bpf["events"].open_perf_buffer(
            self.handle_event
        )

        poll_task = asyncio.create_task(
            self.poll_perf_buffer()
        )

        worker_task = asyncio.create_task(
            self.process_queue()
        )

        await asyncio.gather(
            poll_task,
            worker_task,
        )

    ###################################################

    async def stop(self):

        self.running = False