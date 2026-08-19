import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.health import router as health_router
from app.collectors.filesystem import FilesystemCollector
from app.collectors.process import ProcessCollector
from app.config import settings
from app.event_bus import event_bus
from app.kernel.loader.loader import KernelLoader
from app.pipeline.orchestrator import PipelineOrchestrator
from app.websocket.routes import router as websocket_router
from app.api.events import router as events_router

# ------------------------------------------------------------------
# Debug Subscriber
# ------------------------------------------------------------------


async def debug(event):

    logger.info(
        f"KATANA EVENT | "
        f"type={event.event_type.value} | "
        f"source={event.source.value} | "
        f"pid={event.pid} | "
        f"process={event.process_name}"
    )


# ------------------------------------------------------------------
# Global Components
# ------------------------------------------------------------------


process_collector = ProcessCollector()
filesystem_collector = FilesystemCollector()
kernel_loader = KernelLoader()
orchestrator = PipelineOrchestrator()


# ------------------------------------------------------------------
# Application Lifespan
# ------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):

    # --------------------------------------------------------------
    # Event Subscribers
    # --------------------------------------------------------------

    event_bus.subscribe(debug)

    # --------------------------------------------------------------
    # Background Tasks
    # --------------------------------------------------------------

    process_task = asyncio.create_task(
        process_collector.start()
    )

    filesystem_task = asyncio.create_task(
        filesystem_collector.start()
    )

    kernel_task = asyncio.create_task(
        kernel_loader.start()
    )

    orchestrator_task = asyncio.create_task(
        orchestrator.run()
    )

    logger.info(
        "KATANA background services started"
    )

    try:

        yield

    finally:

        # ----------------------------------------------------------
        # Stop Services
        # ----------------------------------------------------------

        logger.info(
            "Stopping KATANA background services..."
        )

        await process_collector.stop()
        await filesystem_collector.stop()
        await kernel_loader.stop()
        await orchestrator.stop()

        # ----------------------------------------------------------
        # Cancel Remaining Tasks
        # ----------------------------------------------------------

        tasks = [
            process_task,
            filesystem_task,
            kernel_task,
            orchestrator_task,
        ]

        for task in tasks:

            if not task.done():
                task.cancel()

        await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        logger.info(
            "KATANA background services stopped"
        )


# ------------------------------------------------------------------
# FastAPI Application
# ------------------------------------------------------------------


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


# ------------------------------------------------------------------
# CORS Middleware
# ------------------------------------------------------------------


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_ORIGIN,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------


app.include_router(
    health_router
)

app.include_router(
    events_router
)

app.include_router(
    websocket_router
)