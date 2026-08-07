from collections import deque

from app.feature_engine.features import BehaviorFeatures
from app.ml.features_to_vector import to_vector


class BaselineManager:
    def __init__(self, baseline_size: int = 12):
        self.baseline_size = baseline_size
        self.samples: deque[list[float]] = deque(maxlen=baseline_size)

    def add_sample(
        self,
        features: BehaviorFeatures,
    ):
        self.samples.append(
            to_vector(features)
        )

    @property
    def ready(self) -> bool:
        return len(self.samples) >= self.baseline_size

    def training_data(self) -> list[list[float]]:
        return list(self.samples)

    def clear(self):
        self.samples.clear()