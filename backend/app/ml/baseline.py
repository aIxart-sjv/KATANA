from collections import deque

from app.feature_engine.features import BehaviorFeatures
from app.ml.features_to_vector import to_vector


class BaselineManager:
    """
    Collects benign behavioral observations used to initialize
    the production anomaly detector.

    The baseline contains only benign observations.

    Runtime lifecycle:

        behavioral observations
                ↓
        baseline collection
                ↓
        training dataset
                ↓
        Isolation Forest

    Threshold calibration is intentionally NOT performed here.

    The production anomaly threshold is obtained separately through
    the KATANA validation pipeline.
    """

    def __init__(
        self,
        baseline_size: int = 60,
    ):
        if baseline_size <= 0:
            raise ValueError(
                "baseline_size must be greater than zero."
            )

        self.baseline_size = baseline_size

        self.samples: deque[list[float]] = deque(
            maxlen=baseline_size
        )

    # ==================================================================
    # COLLECTION
    # ==================================================================

    def add_sample(
        self,
        features: BehaviorFeatures,
    ) -> None:
        """
        Convert one behavioral observation into the production
        28-dimensional feature vector and add it to the baseline.
        """

        vector = to_vector(
            features
        )

        self.samples.append(
            vector
        )

    # ==================================================================
    # STATE
    # ==================================================================

    @property
    def ready(self) -> bool:
        """
        Return True when enough benign observations have been
        collected to train the runtime model.
        """

        return (
            len(self.samples)
            >= self.baseline_size
        )

    # ==================================================================
    # DATA ACCESS
    # ==================================================================

    def training_data(self) -> list[list[float]]:
        """
        Return the collected benign observations as training data.
        """

        return list(
            self.samples
        )

    # ==================================================================
    # PROGRESS
    # ==================================================================

    @property
    def progress(self) -> int:
        """
        Number of baseline observations currently collected.
        """

        return len(
            self.samples
        )

    @property
    def remaining(self) -> int:
        """
        Number of observations still required before the baseline
        becomes ready.
        """

        return max(
            self.baseline_size
            - len(self.samples),
            0,
        )

    # ==================================================================
    # RESET
    # ==================================================================

    def clear(self) -> None:
        """
        Clear the collected benign baseline.
        """

        self.samples.clear()