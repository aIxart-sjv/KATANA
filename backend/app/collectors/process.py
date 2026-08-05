import asyncio
import socket

import psutil

from app.collectors.base import BaseCollector
from app.core.constants import PROCESS_SCAN_INTERVAL
from app.diff.process_diff import compare_processes
from app.event_bus import event_bus
from app.state.process_snapshot import (
    ProcessInfo,
    ProcessSnapshot,
)


class ProcessCollector(BaseCollector):

    def __init__(self):
        self.snapshot = ProcessSnapshot()
        self.running = False
        self.hostname = socket.gethostname()

    def build_snapshot(self) -> dict[int, ProcessInfo]:

        processes = {}

        for proc in psutil.process_iter(
            [
                "pid",
                "ppid",
                "name",
                "username",
                "cpu_percent",
                "memory_percent",
            ]
        ):

            try:

                info = proc.info

                processes[info["pid"]] = ProcessInfo(
                    pid=info["pid"],
                    ppid=info["ppid"],
                    name=info["name"] or "",
                    username=info["username"] or "",
                    cpu_percent=info["cpu_percent"] or 0,
                    memory_percent=info["memory_percent"] or 0,
                )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                continue

        return processes

    async def collect(self):

        current = self.build_snapshot()

        events = compare_processes(
            self.snapshot.processes,
            current,
            self.hostname,
        )

        for event in events:
            await event_bus.publish(event)

        self.snapshot.update(current)

    async def start(self):

        self.running = True

        while self.running:

            await self.collect()

            await asyncio.sleep(PROCESS_SCAN_INTERVAL)

    async def stop(self):

        self.running = False