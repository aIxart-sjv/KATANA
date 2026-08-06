from sklearn.ensemble import IsolationForest


class BehaviorModel:
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.02,
            random_state=42,
            n_estimators=150,
        )

        self.trained = False

    def train(
        self,
        samples: list[list[float]],
    ):
        self.model.fit(samples)
        self.trained = True

    def predict(
        self,
        sample: list[float],
    ) -> tuple[bool, float]:

        prediction = self.model.predict([sample])[0]

        score = self.model.score_samples([sample])[0]

        return prediction == -1, score