"""
KATANA Behavioral Anomaly Detection Model.

Production pipeline:

    BehaviorFeatures
          |
          v
    28-dimensional feature vector
          |
          v
    Input validation
          |
          v
    log1p transformation
          |
          v
    RobustScaler
          |
          v
    Isolation Forest
          |
          v
    score_samples()
          |
          v
    Validated threshold
          |
          v
    NORMAL / ANOMALY

Training is performed using benign behavior only.

Score semantics:

    Higher score -> more normal
    Lower score  -> more anomalous

The anomaly threshold is selected offline using calibration data
and evaluated on an independent holdout set.

The runtime model must NOT learn or modify the threshold.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler


class BehaviorModel:
    """
    Production behavioral anomaly detector for KATANA.

    The model expects exactly 28 engineered behavioral features.

    Runtime preprocessing:

        raw features
            ->
        numeric validation
            ->
        invalid-value sanitization
            ->
        log1p selected features
            ->
        RobustScaler
            ->
        Isolation Forest
            ->
        score_samples()
            ->
        calibrated threshold

    Training uses benign behavior only.

    Production configuration validated by the KATANA threshold
    validation experiment:

        Isolation Forest
        ----------------
        estimators    = 300
        contamination = 0.05
        random_state  = 42
        threshold     = -0.501731

    Calibration performance:

        Precision : 0.9206
        Recall    : 0.4350
        F1        : 0.5908
        FPR        : 0.0500

    Independent holdout performance:

        Precision : 0.8889
        Recall    : 0.5400
        F1        : 0.6719
        FPR        : 0.0450

    The holdout set was excluded from model training and threshold
    selection.

    Decision rule:

        score <= threshold -> anomaly
        score > threshold  -> normal
    """

    # ==============================================================
    # PRODUCTION CONFIGURATION
    # ==============================================================

    FEATURE_COUNT = 28

    DEFAULT_CONTAMINATION = 0.05
    DEFAULT_ESTIMATORS = 300
    DEFAULT_RANDOM_STATE = 42

    # Validated threshold from the independent KATANA validation
    # experiment.
    #
    # IsolationForest.score_samples():
    #
    #     higher -> more normal
    #     lower  -> more anomalous
    #
    # Therefore:
    #
    #     score <= DEFAULT_THRESHOLD -> anomaly
    #     score >  DEFAULT_THRESHOLD -> normal

    DEFAULT_THRESHOLD = -0.501731

    # ==============================================================
    # FEATURE DEFINITIONS
    # ==============================================================

    FEATURE_NAMES = (
        # Base behavioral features
        "process_creation_rate",
        "process_termination_rate",
        "unique_process_count",
        "average_cpu",
        "maximum_cpu",
        "average_memory",
        "maximum_memory",
        "external_connections",
        "failed_logins",
        "privilege_escalations",
        "filesystem_modifications",
        "service_restarts",
        "kernel_exec_count",
        "kernel_connect_count",
        "kernel_open_count",
        "kernel_unlink_count",
        "kernel_setuid_count",
        "kernel_ptrace_count",

        # Engineered relationship features
        "process_activity_ratio",
        "connections_per_process",
        "failed_login_ratio",
        "filesystem_per_process",
        "exec_per_process",
        "kernel_connect_ratio",
        "kernel_open_per_process",
        "unlink_ratio",
        "privilege_kernel_interaction",
        "ptrace_exec_ratio",
    )

    # Features transformed with log1p().
    #
    # These are primarily count/rate/ratio features that can have
    # highly skewed distributions.
    #
    # log1p(x):
    #
    #     - preserves zero
    #     - reduces the influence of extreme values
    #     - is numerically stable for small x

    LOG_FEATURES = frozenset(
        {
            # Base count/rate features
            0,   # process_creation_rate
            1,   # process_termination_rate
            2,   # unique_process_count

            # Behavioral counts
            7,   # external_connections
            8,   # failed_logins
            9,   # privilege_escalations
            10,  # filesystem_modifications
            11,  # service_restarts

            # Kernel activity counts
            12,  # kernel_exec_count
            13,  # kernel_connect_count
            14,  # kernel_open_count
            15,  # kernel_unlink_count
            16,  # kernel_setuid_count
            17,  # kernel_ptrace_count

            # Engineered relationship features
            18,  # process_activity_ratio
            19,  # connections_per_process
            20,  # failed_login_ratio
            21,  # filesystem_per_process
            22,  # exec_per_process
            23,  # kernel_connect_ratio
            24,  # kernel_open_per_process
            25,  # unlink_ratio
            26,  # privilege_kernel_interaction
            27,  # ptrace_exec_ratio
        }
    )

    # ==============================================================
    # INITIALIZATION
    # ==============================================================

    def __init__(
        self,
        contamination: float = DEFAULT_CONTAMINATION,
        n_estimators: int = DEFAULT_ESTIMATORS,
        random_state: int = DEFAULT_RANDOM_STATE,
        threshold: float | None = DEFAULT_THRESHOLD,
    ) -> None:
        """
        Initialize the behavioral anomaly detector.

        Parameters
        ----------
        contamination:
            Expected proportion of anomalies used by Isolation Forest.

        n_estimators:
            Number of trees in the Isolation Forest.

        random_state:
            Random seed used for deterministic model training.

        threshold:
            Validated anomaly threshold.

            Set to None only when explicitly creating a model that
            should not perform predictions until a threshold is
            configured with set_threshold().
        """

        self._validate_contamination(contamination)
        self._validate_estimators(n_estimators)

        if threshold is not None:
            self._validate_threshold(threshold)

        self.contamination = float(contamination)
        self.n_estimators = int(n_estimators)
        self.random_state = int(random_state)

        self.threshold = (
            float(threshold)
            if threshold is not None
            else None
        )

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1,
        )

        self.scaler = RobustScaler()

        self.trained = False
        self.training_samples = 0

    # ==============================================================
    # VALIDATION
    # ==============================================================

    @staticmethod
    def _validate_contamination(
        contamination: float,
    ) -> None:
        """
        Validate Isolation Forest contamination.
        """

        try:
            value = float(contamination)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "contamination must be a numeric value."
            ) from exc

        if not np.isfinite(value):
            raise ValueError(
                "contamination must be finite."
            )

        if not 0.0 < value <= 0.5:
            raise ValueError(
                "contamination must be greater than 0 "
                "and less than or equal to 0.5."
            )

    @staticmethod
    def _validate_estimators(
        n_estimators: int,
    ) -> None:
        """
        Validate the number of Isolation Forest estimators.
        """

        if not isinstance(
            n_estimators,
            (int, np.integer),
        ):
            raise TypeError(
                "n_estimators must be an integer."
            )

        if n_estimators <= 0:
            raise ValueError(
                "n_estimators must be greater than zero."
            )

    @staticmethod
    def _validate_threshold(
        threshold: float,
    ) -> None:
        """
        Validate an anomaly threshold.
        """

        try:
            value = float(threshold)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "threshold must be a numeric value."
            ) from exc

        if not np.isfinite(value):
            raise ValueError(
                "threshold must be finite."
            )

    # ==============================================================
    # INPUT PREPARATION
    # ==============================================================

    def _prepare_input(
        self,
        samples: (
            Sequence[Sequence[float]]
            | Sequence[float]
            | np.ndarray
        ),
    ) -> np.ndarray:
        """
        Convert, validate, and sanitize model input.

        Accepted input:

            [f1, f2, ..., f28]

        or:

            [
                [f1, ..., f28],
                [f1, ..., f28],
                ...
            ]

        Returns
        -------
        numpy.ndarray
            A two-dimensional float64 array with shape:

                (samples, 28)
        """

        try:
            data = np.asarray(
                samples,
                dtype=np.float64,
            ).copy()

        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Input features must contain numeric values."
            ) from exc

        # Convert a single 28-feature vector into a matrix.
        if data.ndim == 1:
            data = data.reshape(1, -1)

        if data.ndim != 2:
            raise ValueError(
                "Input must be a 1D feature vector or "
                "a 2D feature matrix."
            )

        if data.shape[1] != self.FEATURE_COUNT:
            raise ValueError(
                "KATANA requires exactly "
                f"{self.FEATURE_COUNT} features; "
                f"received {data.shape[1]}."
            )

        if data.shape[0] == 0:
            raise ValueError(
                "Input contains zero samples."
            )

        # Telemetry should never be allowed to propagate NaN or
        # infinite values into the preprocessing/model pipeline.
        data = np.nan_to_num(
            data,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        return data

    # ==============================================================
    # FEATURE TRANSFORMATION
    # ==============================================================

    def _transform(
        self,
        samples: (
            Sequence[Sequence[float]]
            | Sequence[float]
            | np.ndarray
        ),
    ) -> np.ndarray:
        """
        Apply KATANA's deterministic feature transformation.

        Pipeline:

            input
              |
              v
            validation
              |
              v
            sanitization
              |
              v
            log1p selected features
              |
              v
            transformed features

        RobustScaler is deliberately excluded from this method.

        The scaler must be fitted exclusively on benign training data
        and then reused unchanged for runtime inference.
        """

        data = self._prepare_input(samples)

        for index in self.LOG_FEATURES:
            data[:, index] = np.log1p(
                np.maximum(
                    data[:, index],
                    0.0,
                )
            )

        return data

    # ==============================================================
    # TRAINING
    # ==============================================================

    def train(
        self,
        samples: (
            Sequence[Sequence[float]]
            | np.ndarray
        ),
    ) -> None:
        """
        Train the anomaly detector using benign behavior only.

        Training consists of:

            1. Feature transformation
            2. RobustScaler fitting
            3. Isolation Forest fitting

        The anomaly threshold is NOT selected here.

        Threshold calibration must remain an offline validation
        process using data excluded from model training.
        """

        transformed = self._transform(samples)

        if transformed.shape[0] < 2:
            raise ValueError(
                "At least two training samples are required."
            )

        # Fit the scaler exclusively on benign training data.
        scaled = self.scaler.fit_transform(
            transformed
        )

        # Train the Isolation Forest exclusively on benign data.
        self.model.fit(
            scaled
        )

        self.trained = True
        self.training_samples = transformed.shape[0]

    # ==============================================================
    # SCORING
    # ==============================================================

    def score(
        self,
        sample: Sequence[float] | np.ndarray,
    ) -> float:
        """
        Return the Isolation Forest anomaly score for one sample.

        Score semantics:

            higher score -> more normal
            lower score  -> more anomalous

        Returns
        -------
        float
            Raw Isolation Forest score.
        """

        self._require_trained()

        transformed = self._transform(sample)

        scaled = self.scaler.transform(
            transformed
        )

        scores = self.model.score_samples(
            scaled
        )

        return float(scores[0])

    def score_batch(
        self,
        samples: (
            Sequence[Sequence[float]]
            | np.ndarray
        ),
    ) -> np.ndarray:
        """
        Return Isolation Forest scores for multiple samples.

        Returns
        -------
        numpy.ndarray
            One score per input sample.
        """

        self._require_trained()

        transformed = self._transform(samples)

        scaled = self.scaler.transform(
            transformed
        )

        return self.model.score_samples(
            scaled
        )

    # ==============================================================
    # PREDICTION
    # ==============================================================

    def predict(
        self,
        sample: Sequence[float] | np.ndarray,
    ) -> tuple[bool, float]:
        """
        Classify one behavioral sample.

        Decision rule:

            score <= threshold
                -> anomaly

            score > threshold
                -> normal

        Returns
        -------
        tuple[bool, float]
            (
                is_anomaly,
                anomaly_score,
            )
        """

        self._require_ready()

        score = self.score(sample)

        anomaly = score <= self.threshold

        return (
            bool(anomaly),
            float(score),
        )

    def predict_batch(
        self,
        samples: (
            Sequence[Sequence[float]]
            | np.ndarray
        ),
    ) -> list[tuple[bool, float]]:
        """
        Classify multiple behavioral samples.

        Returns
        -------
        list[tuple[bool, float]]
            A list containing:

                (is_anomaly, score)

            for each input sample.
        """

        self._require_ready()

        scores = self.score_batch(samples)

        return [
            (
                bool(score <= self.threshold),
                float(score),
            )
            for score in scores
        ]

    # ==============================================================
    # STATE
    # ==============================================================

    @property
    def ready(self) -> bool:
        """
        Return True when the model can perform anomaly prediction.
        """

        return (
            self.trained
            and self.threshold is not None
        )

    def _require_trained(self) -> None:
        """
        Ensure that the model has been trained before scoring.
        """

        if not self.trained:
            raise RuntimeError(
                "BehaviorModel has not been trained. "
                "Call train() before scoring."
            )

    def _require_ready(self) -> None:
        """
        Ensure that the model is fully configured for prediction.
        """

        if not self.trained:
            raise RuntimeError(
                "BehaviorModel has not been trained. "
                "Call train() before prediction."
            )

        if self.threshold is None:
            raise RuntimeError(
                "Anomaly threshold has not been configured. "
                "Call set_threshold() before prediction."
            )

    # ==============================================================
    # THRESHOLD MANAGEMENT
    # ==============================================================

    def set_threshold(
        self,
        threshold: float,
    ) -> None:
        """
        Configure the anomaly threshold.

        Threshold selection belongs to the offline validation
        pipeline and should not be automatically adapted from
        runtime observations.
        """

        self._validate_threshold(threshold)

        self.threshold = float(threshold)

    def reset_threshold(self) -> None:
        """
        Remove the configured anomaly threshold.

        Prediction becomes unavailable until another threshold
        is explicitly configured.
        """

        self.threshold = None

    # ==============================================================
    # METADATA
    # ==============================================================

    def metadata(self) -> dict:
        """
        Return complete model configuration and runtime state.
        """

        return {
            "model": "IsolationForest",
            "feature_count": self.FEATURE_COUNT,
            "feature_names": list(
                self.FEATURE_NAMES
            ),
            "log_features": sorted(
                self.LOG_FEATURES
            ),
            "contamination": self.contamination,
            "n_estimators": self.n_estimators,
            "random_state": self.random_state,
            "threshold": self.threshold,
            "trained": self.trained,
            "ready": self.ready,
            "training_samples": self.training_samples,
            "score_direction": {
                "higher": "more_normal",
                "lower": "more_anomalous",
            },
            "decision_rule": (
                "score <= threshold -> anomaly; "
                "score > threshold -> normal"
            ),
        }

    # ==============================================================
    # SUMMARY
    # ==============================================================

    def summary(self) -> dict:
        """
        Return a compact production-oriented model summary.
        """

        return {
            "algorithm": "Isolation Forest",
            "features": self.FEATURE_COUNT,
            "trees": self.n_estimators,
            "contamination": self.contamination,
            "threshold": self.threshold,
            "trained": self.trained,
            "ready": self.ready,
            "training_samples": self.training_samples,
        }