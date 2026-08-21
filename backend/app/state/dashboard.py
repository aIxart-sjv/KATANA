from datetime import datetime, timezone
from typing import Any

from app.schemas.event import Event


class DashboardState:
    """
    Central runtime state exposed to the KATANA frontend.

    This class stores dashboard-facing runtime information.
    It does not perform detection, threat classification,
    or security analysis itself.
    """

    def __init__(self):
        # ==========================================================
        # SYSTEM STATE
        # ==========================================================

        self.pipeline_running = False

        self.started_at: str | None = None

        # ==========================================================
        # ML STATE
        # ==========================================================

        self.ml_status = "learning"

        self.baseline_samples = 0

        self.baseline_required = 0

        self.latest_anomaly_score: float | None = None

        self.threshold: float | None = None

        # ==========================================================
        # EVENT STATE
        # ==========================================================

        self.total_events = 0

        self.last_event_at: str | None = None

        # ==========================================================
        # INCIDENT STATE
        # ==========================================================

        self.total_incidents = 0

        self.current_severity: str | None = None

        self.current_confidence: float | None = None

        self.recent_incidents: list[
            dict[str, Any]
        ] = []

        # ==========================================================
        # AI / EXPLAINABILITY STATE
        # ==========================================================

        self.latest_ai_analysis: (
            dict[str, Any] | None
        ) = None

        # ==========================================================
        # INVESTIGATION STATE
        # ==========================================================

        self.latest_recommendations: list[
            dict[str, Any]
        ] = []

    # ==============================================================
    # HELPERS
    # ==============================================================

    @staticmethod
    def _now() -> str:
        """
        Return the current UTC timestamp.
        """

        return datetime.now(
            timezone.utc
        ).isoformat()

    # ==============================================================
    # PIPELINE STATE
    # ==============================================================

    def set_pipeline_running(
        self,
        running: bool,
    ):
        """
        Update the pipeline runtime status.
        """

        self.pipeline_running = running

        if running and self.started_at is None:
            self.started_at = self._now()

    # ==============================================================
    # EVENT UPDATES
    # ==============================================================

    def record_event(
        self,
        event: Event | None = None,
    ):
        """
        Record that a new KATANA event was received.

        The event argument is intentionally available for future
        dashboard statistics without changing the EventBus interface.
        """

        self.total_events += 1

        self.last_event_at = self._now()

    async def handle_event(
        self,
        event: Event,
    ):
        """
        EventBus subscriber.

        This method is called whenever a collector publishes
        a new KATANA event through the EventBus.
        """

        self.record_event(event)

    # ==============================================================
    # ML UPDATES
    # ==============================================================

    def update_learning(
        self,
        progress: int,
        required: int,
    ):
        """
        Update ML baseline-learning progress.
        """

        self.ml_status = "learning"

        self.baseline_samples = progress

        self.baseline_required = required

    def update_normal(
        self,
        score: float,
        threshold: float,
    ):
        """
        Update the dashboard after normal behavior is analyzed.
        """

        self.ml_status = "monitoring"

        self.latest_anomaly_score = score

        self.threshold = threshold

    # ==============================================================
    # ANOMALY / INCIDENT UPDATES
    # ==============================================================

    def update_incident(
        self,
        output: dict[str, Any],
    ):
        """
        Update dashboard state with a confirmed anomaly incident.
        """

        self.ml_status = "monitoring"

        self.latest_anomaly_score = (
            output.get("score")
        )

        self.threshold = output.get(
            "threshold"
        )

        self.current_severity = output.get(
            "severity"
        )

        self.current_confidence = output.get(
            "confidence"
        )

        self.latest_ai_analysis = output.get(
            "ai_analysis"
        )

        self.latest_recommendations = (
            output.get(
                "investigation_commands",
                [],
            )
        )

        self.total_incidents += 1

        # ----------------------------------------------------------
        # Create dashboard incident record
        # ----------------------------------------------------------

        incident = {
            "timestamp": self._now(),

            "severity": output.get(
                "severity"
            ),

            "confidence": output.get(
                "confidence"
            ),

            "score": output.get(
                "score"
            ),

            "threshold": output.get(
                "threshold"
            ),

            "evidence": output.get(
                "evidence",
                [],
            ),

            "triggered_features": output.get(
                "triggered_features",
                [],
            ),

            "recommended_actions": output.get(
                "recommended_actions",
                [],
            ),

            "investigation_commands": output.get(
                "investigation_commands",
                [],
            ),

            "ai_analysis": output.get(
                "ai_analysis"
            ),

            "automatic_remediation": output.get(
                "automatic_remediation",
                False,
            ),
        }

        # ----------------------------------------------------------
        # Store newest incident first
        # ----------------------------------------------------------

        self.recent_incidents.insert(
            0,
            incident,
        )

        # ----------------------------------------------------------
        # Prevent unlimited memory growth
        # ----------------------------------------------------------

        self.recent_incidents = (
            self.recent_incidents[:50]
        )

    # ==============================================================
    # SNAPSHOT FOR API
    # ==============================================================

    def snapshot(self) -> dict[str, Any]:
        """
        Return the complete dashboard-facing state.

        This method is used by the REST API so the frontend can
        retrieve the current state when it first loads.
        """

        return {
            # ------------------------------------------------------
            # System
            # ------------------------------------------------------

            "system": {
                "pipeline_running": (
                    self.pipeline_running
                ),

                "started_at": (
                    self.started_at
                ),
            },

            # ------------------------------------------------------
            # Machine Learning
            # ------------------------------------------------------

            "ml": {
                "status": (
                    self.ml_status
                ),

                "baseline_samples": (
                    self.baseline_samples
                ),

                "baseline_required": (
                    self.baseline_required
                ),

                "latest_anomaly_score": (
                    self.latest_anomaly_score
                ),

                "threshold": (
                    self.threshold
                ),
            },

            # ------------------------------------------------------
            # Events
            # ------------------------------------------------------

            "events": {
                "total": (
                    self.total_events
                ),

                "last_event_at": (
                    self.last_event_at
                ),
            },

            # ------------------------------------------------------
            # Incidents
            # ------------------------------------------------------

            "incidents": {
                "total": (
                    self.total_incidents
                ),

                "current_severity": (
                    self.current_severity
                ),

                "current_confidence": (
                    self.current_confidence
                ),

                "recent": (
                    self.recent_incidents
                ),
            },

            # ------------------------------------------------------
            # Analysis
            # ------------------------------------------------------

            "analysis": {
                "latest_ai_analysis": (
                    self.latest_ai_analysis
                ),

                "latest_recommendations": (
                    self.latest_recommendations
                ),
            },
        }


# ==============================================================
# GLOBAL DASHBOARD STATE
# ==============================================================


dashboard_state = DashboardState()