import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.dashboard import router as dashboard_router
from app.api.events import router as events_router
from app.api.health import router as health_router

from app.collectors.filesystem import FilesystemCollector
from app.collectors.process import ProcessCollector

from app.config import settings

from app.event_bus import event_bus

from app.kernel.loader.loader import KernelLoader

from app.pipeline.orchestrator import PipelineOrchestrator

from app.services.broadcaster import broadcast_event

from app.state.dashboard import dashboard_state

from app.websocket.routes import router as websocket_router


# ------------------------------------------------------------------
# Debug Subscriber
# ------------------------------------------------------------------


async def debug(event):
    """
    Debug event subscriber.

    Prints every incoming KATANA event to the backend logs.
    """

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
    """
    Controls the lifecycle of the KATANA backend.

    Startup:
        - Subscribe event handlers.
        - Start collectors.
        - Start kernel monitoring.
        - Start the analysis pipeline.

    Shutdown:
        - Stop all KATANA services.
        - Cancel remaining background tasks.
    """

    # ==============================================================
    # EVENT SUBSCRIBERS
    # ==============================================================

    # --------------------------------------------------------------
    # Debug logging
    # --------------------------------------------------------------

    event_bus.subscribe(
        debug
    )

    # --------------------------------------------------------------
    # Event storage + WebSocket broadcasting
    # --------------------------------------------------------------

    event_bus.subscribe(
        broadcast_event
    )

    # --------------------------------------------------------------
    # Dashboard runtime state
    #
    # Every event updates:
    #
    # - Total event count
    # - Last event timestamp
    # - Event type statistics
    # - Source statistics
    # --------------------------------------------------------------

    event_bus.subscribe(
        dashboard_state.handle_event
    )

    # ==============================================================
    # DASHBOARD STATE
    # ==============================================================

    dashboard_state.set_pipeline_running(
        True
    )

    # ==============================================================
    # BACKGROUND TASKS
    # ==============================================================

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

    logger.success(
        "KATANA background services started"
    )

    logger.info(
        "Dashboard state initialized"
    )

    # ==============================================================
    # APPLICATION RUNNING
    # ==============================================================

    try:

        yield

    finally:

        # ==========================================================
        # SHUTDOWN
        # ==============================================================

        logger.warning(
            "Stopping KATANA background services..."
        )

        # ----------------------------------------------------------
        # Mark dashboard pipeline as stopped
        # ----------------------------------------------------------

        dashboard_state.set_pipeline_running(
            False
        )

        # ----------------------------------------------------------
        # Stop services gracefully
        # ----------------------------------------------------------

        await process_collector.stop()

        await filesystem_collector.stop()

        await kernel_loader.stop()

        await orchestrator.stop()

        # ----------------------------------------------------------
        # Cancel remaining tasks
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

        logger.success(
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
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],

    allow_credentials=True,

    allow_methods=[
        "*",
    ],

    allow_headers=[
        "*",
    ],
)


# ------------------------------------------------------------------
# API Routes
# ------------------------------------------------------------------


# Health endpoint
app.include_router(
    health_router
)


# ML status endpoint
app.include_router(
    events_router
)


# Dashboard state endpoint
app.include_router(
    dashboard_router
)


# Live WebSocket endpoint
app.include_router(
    websocket_router
)