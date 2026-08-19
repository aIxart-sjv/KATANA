from dataclasses import dataclass, field


@dataclass
class AnomalyResult:
    status: str
    severity: str
    score: float
    persistence: int
    anomaly_ratio: float
    evidence: list[str] = field(default_factory=list)