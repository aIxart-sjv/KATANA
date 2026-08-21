import asyncio

from loguru import logger

from app.event_store.store import event_store
from app.explainability.engine import ExplainabilityEngine
from app.feature_engine import feature_extractor
from app.llm.ollama import OllamaClient
from app.ml import anomaly_engine
from app.recommendations import recommendation_engine
from app.state.dashboard import dashboard_state
from app.threat_engine.engine import ThreatEngine


class PipelineOrchestrator:

    def __init__(
        self,
        interval: int = 5,
    ):
        self.interval = interval
        self.running = False

        # ----------------------------------------------------------
        # Core analysis engines
        # ----------------------------------------------------------

        self.threat_engine = ThreatEngine()

        # ----------------------------------------------------------
        # Local LLM + explainability
        #
        # Ollama is only used when a High/Critical incident
        # requires deeper analysis.
        # ----------------------------------------------------------

        self.llm = OllamaClient()

        self.explainability_engine = ExplainabilityEngine(
            self.llm
        )

    # ==============================================================
    # PROCESS ONE OBSERVATION WINDOW
    # ==============================================================

    async def process_window(self):

        # ----------------------------------------------------------
        # Get events from latest 5-second window
        # ----------------------------------------------------------

        events = event_store.get_window(5)

        if not events:

            logger.debug(
                "No events in current observation window."
            )

            return None

        # ----------------------------------------------------------
        # Extract behavioral features
        # ----------------------------------------------------------

        features = feature_extractor.extract(
            events
        )

        # ----------------------------------------------------------
        # Run ML anomaly detection
        # ----------------------------------------------------------

        result = anomaly_engine.analyze(
            features
        )

        # ==========================================================
        # PHASE 1 — BASELINE LEARNING
        # ==========================================================

        if result["status"] == "learning":

            # ------------------------------------------------------
            # Update live dashboard state
            # ------------------------------------------------------

            dashboard_state.update_learning(
                progress=result["progress"],
                required=result["required"],
            )

            logger.info(
                f"Learning baseline "
                f"({result['progress']}/{result['required']})"
            )

            return {
                "status": "learning",
                "progress": result["progress"],
                "required": result["required"],
            }

        # ==========================================================
        # PHASE 2 — NORMAL BEHAVIOR
        # ==========================================================

        if not result["anomaly"]:

            # ------------------------------------------------------
            # Update live dashboard state
            # ------------------------------------------------------

            dashboard_state.update_normal(
                score=float(
                    result["score"]
                ),
                threshold=float(
                    result["threshold"]
                ),
            )

            logger.info(
                "System behavior normal."
            )

            logger.info(
                f"Anomaly score: "
                f"{result['score']:.6f}"
            )

            return {
                "status": "normal",
                "anomaly": False,
                "score": result["score"],
                "threshold": result["threshold"],
            }

        # ==========================================================
        # PHASE 3 — ANOMALY DETECTED
        # ==========================================================

        logger.warning(
            "=============================================="
        )

        logger.warning(
            "ANOMALY DETECTED"
        )

        logger.warning(
            f"Anomaly score: "
            f"{result['score']:.6f}"
        )

        logger.warning(
            f"Detection threshold: "
            f"{result['threshold']:.6f}"
        )

        # ==========================================================
        # PHASE 4 — THREAT ANALYSIS
        # ==========================================================

        incident = self.threat_engine.analyze(
            features=features,
            anomaly_score=result["score"],
        )

        logger.warning(
            f"Threat severity: "
            f"{incident.severity}"
        )

        logger.warning(
            f"Threat confidence: "
            f"{incident.confidence:.4f}"
        )

        # ----------------------------------------------------------
        # Evidence
        # ----------------------------------------------------------

        if incident.evidence:

            logger.warning(
                "Evidence:"
            )

            for evidence in incident.evidence:

                logger.warning(
                    f"  • {evidence}"
                )

        else:

            logger.warning(
                "Evidence: insufficient"
            )

        # ==========================================================
        # PHASE 5 — DETERMINISTIC INVESTIGATION
        # ==========================================================
        #
        # These commands are ALWAYS recommendations only.
        #
        # KATANA never executes them automatically.
        # ==========================================================

        recommendations = (
            recommendation_engine.generate(
                features
            )
        )

        logger.warning(
            "Recommended investigation commands:"
        )

        for recommendation in recommendations:

            logger.warning(
                f"  [{recommendation['category']}] "
                f"{recommendation['reason']}"
            )

            logger.warning(
                f"  $ {recommendation['command']}"
            )

        # ==========================================================
        # PHASE 6 — SEVERITY-BASED LLM ESCALATION
        # ==========================================================
        #
        # Medium:
        #     Deterministic recommendations only.
        #
        # High:
        #     Deterministic recommendations + LLM analysis.
        #
        # Critical:
        #     Deterministic recommendations + LLM analysis.
        #
        # The LLM does NOT decide whether the event is anomalous.
        # The ML + ThreatEngine already made that decision.
        # ==========================================================

        ai_analysis = None

        if incident.severity in {
            "High",
            "Critical",
        }:

            logger.warning(
                "=============================================="
            )

            logger.warning(
                "LLM ESCALATION"
            )

            logger.warning(
                f"Severity {incident.severity} "
                "requires deeper analysis."
            )

            logger.info(
                "Calling local Qwen3 explainability engine..."
            )

            try:

                ai_analysis = (
                    await self.explainability_engine.explain(
                        incident
                    )
                )

                logger.success(
                    "LLM analysis completed."
                )

                logger.info(
                    f"AI Risk: "
                    f"{ai_analysis.risk}"
                )

                logger.info(
                    f"AI Summary: "
                    f"{ai_analysis.summary}"
                )

                logger.info(
                    f"AI Analysis: "
                    f"{ai_analysis.analysis}"
                )

                if ai_analysis.mitre_attack:

                    logger.info(
                        "MITRE ATT&CK:"
                    )

                    for technique in (
                        ai_analysis.mitre_attack
                    ):

                        logger.info(
                            f"  • {technique}"
                        )

                else:

                    logger.info(
                        "MITRE ATT&CK: "
                        "No directly supported techniques."
                    )

            except Exception as exc:

                # --------------------------------------------------
                # LLM failure must NOT break KATANA.
                #
                # The deterministic detection and investigation
                # layers remain valid even if Ollama fails.
                # --------------------------------------------------

                logger.exception(
                    f"LLM analysis failed: {exc}"
                )

                logger.warning(
                    "Continuing with deterministic "
                    "security analysis."
                )

        else:

            logger.info(
                f"LLM not required "
                f"(severity={incident.severity})."
            )

            logger.info(
                "Using deterministic investigation "
                "recommendations only."
            )

        # ==========================================================
        # PHASE 7 — UNIFIED RESULT
        # ==========================================================

        output = {
            "status": "anomaly",

            "anomaly": True,

            "score": float(
                result["score"]
            ),

            "threshold": float(
                result["threshold"]
            ),

            "severity": incident.severity,

            "confidence": float(
                incident.confidence
            ),

            "evidence": incident.evidence,

            "triggered_features": (
                incident.triggered_features
            ),

            "recommended_actions": (
                incident.recommended_actions
            ),

            "investigation_commands": [
                {
                    "category": (
                        recommendation["category"]
                    ),

                    "reason": (
                        recommendation["reason"]
                    ),

                    "command": (
                        recommendation["command"]
                    ),
                }
                for recommendation in recommendations
            ],

            "ai_analysis": (
                ai_analysis.model_dump()
                if ai_analysis is not None
                else None
            ),

            # ------------------------------------------------------
            # Safety guarantee
            # ------------------------------------------------------

            "automatic_remediation": False,
        }

        # ==========================================================
        # UPDATE LIVE DASHBOARD STATE
        # ==========================================================

        dashboard_state.update_incident(
            output
        )

        # ==========================================================
        # FINAL LOGGING
        # ==========================================================

        logger.warning(
            "No automatic remediation was performed."
        )

        logger.warning(
            "=============================================="
        )

        return output

    # ==============================================================
    # MAIN PIPELINE LOOP
    # ==============================================================

    async def run(self):

        self.running = True

        # ----------------------------------------------------------
        # Update dashboard state
        # ----------------------------------------------------------

        dashboard_state.set_pipeline_running(
            True
        )

        logger.info(
            f"KATANA pipeline started "
            f"(interval={self.interval}s)"
        )

        while self.running:

            try:

                await self.process_window()

            except Exception as exc:

                logger.exception(
                    f"Pipeline error: {exc}"
                )

            await asyncio.sleep(
                self.interval
            )

    # ==============================================================
    # STOP
    # ==============================================================

    async def stop(self):

        self.running = False

        # ----------------------------------------------------------
        # Update dashboard state
        # ----------------------------------------------------------

        dashboard_state.set_pipeline_running(
            False
        )

        logger.info(
            "KATANA pipeline stopped."
        )