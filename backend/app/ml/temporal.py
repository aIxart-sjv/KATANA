from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class TemporalResult:
    is_anomaly: bool
    severity: str
    persistence: int
    anomaly_ratio: float
    latest_score: float


class TemporalAnomalyDetector:
    """
    Converts individual ML anomaly scores into a
    temporally stable security decision.

    A single abnormal observation does not immediately
    become a high-confidence security alert.

    This reduces false alarms caused by transient activity.
    """

    def __init__(
        self,
        window_size: int = 5,
        minimum_anomalies: int = 3,
    ):
        if window_size <= 0:
            raise ValueError("window_size must be greater than zero.")

        if minimum_anomalies <= 0:
            raise ValueError(
                "minimum_anomalies must be greater than zero."
            )

        if minimum_anomalies > window_size:
            raise ValueError(
                "minimum_anomalies cannot exceed window_size."
            )

        self.window_size = window_size
        self.minimum_anomalies = minimum_anomalies

        self.history: deque[bool] = deque(
            maxlen=window_size
        )

        self.scores: deque[float] = deque(
            maxlen=window_size
        )

    def update(
        self,
        is_anomaly: bool,
        score: float,
    ) -> TemporalResult:

        self.history.append(is_anomaly)
        self.scores.append(score)

        anomaly_count = sum(self.history)

        persistence = 0

        for value in reversed(self.history):
            if value:
                persistence += 1
            else:
                break

        anomaly_ratio = (
            anomaly_count / len(self.history)
        )

        confirmed = (
            len(self.history) >= self.minimum_anomalies
            and anomaly_count >= self.minimum_anomalies
        )

        if confirmed:
            if anomaly_ratio >= 0.8:
                severity = "HIGH"
            elif anomaly_ratio >= 0.6:
                severity = "MEDIUM"
            else:
                severity = "LOW"
        else:
            severity = "NORMAL"

        return TemporalResult(
            is_anomaly=confirmed,
            severity=severity,
            persistence=persistence,
            anomaly_ratio=anomaly_ratio,
            latest_score=score,
        )

    def reset(self) -> None:
        self.history.clear()
        self.scores.clear()