from app.feature_engine.features import BehaviorFeatures
from app.ml.baseline import BaselineManager
from app.ml.features_to_vector import to_vector
from app.ml.model import BehaviorModel


class AnomalyEngine:
    def __init__(self):
        self.baseline = BaselineManager()
        self.model = BehaviorModel()

    def analyze(
        self,
        features: BehaviorFeatures,
    ):

        if not self.baseline.ready:

            self.baseline.add_sample(features)

            return {
                "status": "learning",
                "progress": len(self.baseline.samples),
                "required": self.baseline.baseline_size,
            }

        if not self.model.trained:

            self.model.train(
                self.baseline.training_data()
            )

        vector = to_vector(features)

        anomaly, score = self.model.predict(vector)

        return {
            "status": "monitoring",
            "anomaly": anomaly,
            "score": float(score),
        }