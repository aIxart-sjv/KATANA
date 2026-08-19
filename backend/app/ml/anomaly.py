from app.feature_engine.features import BehaviorFeatures
from app.ml.baseline import BaselineManager
from app.ml.features_to_vector import to_vector
from app.ml.model import BehaviorModel


class AnomalyEngine:
    """
    KATANA production anomaly detection engine.

    Runtime pipeline:

        BehaviorFeatures
            ->
        28-dimensional feature vector
            ->
        log1p transformation
            ->
        RobustScaler
            ->
        Isolation Forest
            ->
        anomaly score
            ->
        validated threshold
            ->
        anomaly / normal

    The Isolation Forest is trained exclusively on the locally
    collected benign baseline.

    The anomaly threshold is NOT learned from runtime observations.
    It is selected offline through the KATANA ML validation pipeline.
    """

    # ==============================================================
    # PRODUCTION CONFIGURATION
    # ==============================================================

    BASELINE_SIZE = 60

    # Validated production threshold.
    #
    # Calibration:
    #   Precision : 0.9206
    #   Recall    : 0.4350
    #   F1        : 0.5908
    #   FPR       : 0.0500
    #
    # Independent holdout:
    #   Precision : 0.8889
    #   Recall    : 0.5400
    #   F1        : 0.6719
    #   FPR       : 0.0450
    #
    # IsolationForest.score_samples() semantics:
    #   lower score -> more anomalous
    #
    # Decision:
    #   score <= threshold -> anomaly
    #   score > threshold  -> normal

    PRODUCTION_THRESHOLD = BehaviorModel.DEFAULT_THRESHOLD

    # ==============================================================
    # INITIALIZATION
    # ==============================================================

    def __init__(
        self,
        baseline_size: int = BASELINE_SIZE,
        threshold: float = PRODUCTION_THRESHOLD,
    ) -> None:
        """
        Initialize the KATANA anomaly detection engine.

        Parameters
        ----------
        baseline_size:
            Number of benign observations collected before the
            runtime model is trained.

        threshold:
            Validated anomaly threshold.

            The default value comes from BehaviorModel's validated
            production threshold.

            This can be overridden explicitly for experiments or
            future recalibration.
        """

        if not isinstance(baseline_size, int):
            raise TypeError(
                "baseline_size must be an integer."
            )

        if baseline_size <= 0:
            raise ValueError(
                "baseline_size must be greater than zero."
            )

        if threshold is None:
            raise ValueError(
                "threshold must be a finite numeric value."
            )

        self.baseline = BaselineManager(
            baseline_size=baseline_size
        )

        self.model = BehaviorModel()

        self.threshold = float(threshold)

    # ==============================================================
    # ANALYSIS
    # ==============================================================

    def analyze(
        self,
        features: BehaviorFeatures,
    ) -> dict:
        """
        Analyze one behavioral observation.

        The engine operates in two runtime phases.

        Phase 1:
            Collect benign baseline observations.

        Phase 2:
            Train the Isolation Forest once and continuously
            evaluate incoming behavior.

        Returns
        -------
        dict
            During baseline collection:

                {
                    "status": "learning",
                    "progress": int,
                    "required": int,
                }

            During anomaly monitoring:

                {
                    "status": "monitoring",
                    "anomaly": bool,
                    "score": float,
                    "threshold": float,
                }
        """

        # ----------------------------------------------------------
        # PHASE 1: BASELINE LEARNING
        # ----------------------------------------------------------

        if not self.baseline.ready:
            self.baseline.add_sample(features)

            return {
                "status": "learning",
                "progress": len(self.baseline.samples),
                "required": self.baseline.baseline_size,
            }

        # ----------------------------------------------------------
        # PHASE 2: MODEL TRAINING
        # ----------------------------------------------------------

        if not self.model.trained:
            self.model.train(
                self.baseline.training_data()
            )

        # ----------------------------------------------------------
        # PHASE 3: FEATURE ENGINEERING
        # ----------------------------------------------------------

        vector = to_vector(features)

        # ----------------------------------------------------------
        # PHASE 4: ANOMALY SCORING
        # ----------------------------------------------------------

        score = self.model.score(vector)

        # ----------------------------------------------------------
        # PHASE 5: THRESHOLD DECISION
        # ----------------------------------------------------------

        anomaly = score <= self.threshold

        return {
            "status": "monitoring",
            "anomaly": bool(anomaly),
            "score": float(score),
            "threshold": self.threshold,
        }

    # ==============================================================
    # STATE
    # ==============================================================

    @property
    def ready(self) -> bool:
        """
        Return True when the runtime anomaly model has been trained.
        """

        return self.model.trained

    @property
    def baseline_ready(self) -> bool:
        """
        Return True when enough baseline observations have been
        collected to train the anomaly model.
        """

        return self.baseline.ready

    # ==============================================================
    # RESET
    # ==============================================================

    def reset(self) -> None:
        """
        Reset the anomaly engine.

        This clears the runtime baseline and creates a fresh
        BehaviorModel.

        The next observation starts a new baseline-learning phase.
        """

        self.baseline.clear()
        self.model = BehaviorModel()

    # ==============================================================
    # CONFIGURATION
    # ==============================================================

    def set_threshold(
        self,
        threshold: float,
    ) -> None:
        """
        Update the anomaly threshold.

        Threshold selection should normally happen through the
        offline validation pipeline rather than runtime adaptation.
        """

        BehaviorModel._validate_threshold(threshold)

        self.threshold = float(threshold)

    # ==============================================================
    # METADATA
    # ==============================================================

    def metadata(self) -> dict:
        """
        Return the current production engine configuration and state.
        """

        return {
            "baseline_size": self.baseline.baseline_size,
            "baseline_progress": len(self.baseline.samples),
            "baseline_ready": self.baseline.ready,
            "model_trained": self.model.trained,
            "engine_ready": self.ready,
            "threshold": self.threshold,
            "score_direction": {
                "higher": "more_normal",
                "lower": "more_anomalous",
            },
            "decision_rule": (
                "score <= threshold -> anomaly; "
                "score > threshold -> normal"
            ),
            "model": self.model.summary(),
        }