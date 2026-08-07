import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.health import router as health_router
from app.collectors.ebpf.collector import EBPFCollector
from app.collectors.filesystem import FilesystemCollector
from app.collectors.process import ProcessCollector
from app.config import settings
from app.event_bus import event_bus
from app.pipeline.orchestrator import PipelineOrchestrator
from app.services.broadcaster import broadcast_event
from app.websocket.routes import router as websocket_router


# ------------------------------------------------------------------
# Temporary Debug Subscriber
# ------------------------------------------------------------------

async def debug(event):
    logger.info(event.model_dump())


# ------------------------------------------------------------------
# Global Components
# ------------------------------------------------------------------

process_collector = ProcessCollector()
filesystem_collector = FilesystemCollector()
ebpf_collector = EBPFCollector()
orchestrator = PipelineOrchestrator()


# ------------------------------------------------------------------
# Application Lifespan
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Event Subscribers
    event_bus.subscribe(broadcast_event)
    event_bus.subscribe(debug)

    # Background Tasks
    process_task = asyncio.create_task(
        process_collector.start()
    )

    filesystem_task = asyncio.create_task(
        filesystem_collector.start()
    )

    ebpf_task = asyncio.create_task(
        ebpf_collector.start()
    )

    orchestrator_task = asyncio.create_task(
        orchestrator.run()
    )

    yield

    # Graceful Shutdown
    await process_collector.stop()
    await filesystem_collector.stop()
    await ebpf_collector.stop()
    await orchestrator.stop()

    process_task.cancel()
    filesystem_task.cancel()
    ebpf_task.cancel()
    orchestrator_task.cancel()


# ------------------------------------------------------------------
# FastAPI App
# ------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


# ------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

app.include_router(health_router)
app.include_router(websocket_router)