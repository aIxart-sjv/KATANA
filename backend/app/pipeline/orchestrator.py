import asyncio

from loguru import logger

from app.event_store.store import event_store
from app.feature_engine import feature_extractor
from app.ml import anomaly_engine
from app.threat_engine import threat_engine


class PipelineOrchestrator:
    def __init__(
        self,
        interval: int = 5,
    ):
        self.interval = interval
        self.running = False

    async def process_window(self):

        events = event_store.get_window(5)

        if not events:
            return

        features = feature_extractor.extract(events)

        result = anomaly_engine.analyze(features)

        if result["status"] == "learning":

            logger.info(
                f"Learning baseline "
                f"({result['progress']}/{result['required']})"
            )

            return

        if not result["anomaly"]:

            logger.info(
                "System behavior normal."
            )

            return

        incident = threat_engine.analyze(
            features,
            result["score"],
        )

        logger.warning(
            f"Threat Detected: {incident.severity}"
        )

        logger.warning(
            incident.model_dump_json(indent=2)
        )

        #
        # Next phases
        #
        # Explainability Engine
        #
        # Recommendation Engine
        #
        # Response Engine
        #
        # Dashboard Broadcast
        #

    async def run(self):

        self.running = True

        while self.running:

            await self.process_window()

            await asyncio.sleep(self.interval)

    async def stop(self):

        self.running = False