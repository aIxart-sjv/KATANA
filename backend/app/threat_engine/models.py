from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ThreatIncident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    anomaly_score: float

    severity: str

    confidence: float

    triggered_features: dict[str, Any]

    evidence: list[str]

    recommended_actions: list[str]