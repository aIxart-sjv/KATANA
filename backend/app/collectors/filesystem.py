import asyncio
import socket

from inotify_simple import INotify, flags

from app.collectors.base import BaseCollector
from app.config import settings
from app.event_bus import event_bus
from app.schemas.enums import (
    EventSeverity,
    EventSource,
    EventType,
)
from app.schemas.event import Event

from pathlib import Path

from loguru import logger

class FilesystemCollector(BaseCollector):

    def __init__(self):
        self.hostname = socket.gethostname()
        self.running = False

        self.inotify = INotify()

        self.watch_flags = (
            flags.CREATE
            | flags.DELETE
            | flags.MODIFY
            | flags.MOVED_FROM
            | flags.MOVED_TO
        )

        self.watch_map = {}

    def initialize(self):

        for directory in settings.WATCH_DIRECTORIES:

            path = Path(directory)

            if not path.exists():

                logger.warning(
                    f"Skipping missing directory: {directory}"
                )

                continue

            try:

                wd = self.inotify.add_watch(
                    directory,
                    self.watch_flags,
                )

                self.watch_map[wd] = directory

                logger.info(
                    f"Watching {directory}"
                )

            except Exception as e:

                logger.error(
                    f"Failed to watch {directory}: {e}"
                )

    async def collect(self):

        events = self.inotify.read(timeout=100)

        for event in events:

            directory = self.watch_map.get(event.wd)

            if directory is None:
                continue

            filename = event.name

            full_path = f"{directory}/{filename}"

            mask = flags.from_mask(event.mask)

            event_type = None

            if flags.CREATE in mask:

                event_type = EventType.FILE_CREATED

            elif flags.MODIFY in mask:

                event_type = EventType.FILE_MODIFIED

            elif flags.DELETE in mask:

                event_type = EventType.FILE_DELETED

            if event_type is None:

                continue

            normalized = Event(

                source=EventSource.FILESYSTEM,

                event_type=event_type,

                severity=EventSeverity.INFO,

                host=self.hostname,

                metadata={
                    "path": full_path,
                    "flags": [m.name for m in mask],
                },
            )
            await event_bus.publish(normalized)

    async def start(self):

        self.initialize()

        self.running = True

        while self.running:

            await self.collect()

            await asyncio.sleep(0.05)

    async def stop(self):

        self.running = False