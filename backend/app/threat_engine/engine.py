from app.feature_engine.features import BehaviorFeatures
from app.threat_engine.models import ThreatIncident


class ThreatEngine:

    def analyze(
        self,
        features: BehaviorFeatures,
        anomaly_score: float,
    ) -> ThreatIncident:

        evidence = []

        recommendations = []

        severity = "Low"

        confidence = abs(anomaly_score)

        if features.process_creation_rate > 20:
            evidence.append(
                f"High process creation rate ({features.process_creation_rate})"
            )
            recommendations.append(
                "Inspect recently spawned processes."
            )

        if features.maximum_cpu > 90:
            evidence.append(
                f"Maximum CPU usage reached {features.maximum_cpu:.1f}%."
            )
            recommendations.append(
                "Identify CPU-intensive processes."
            )

        if features.external_connections > 5:
            evidence.append(
                f"{features.external_connections} outbound network connections detected."
            )
            recommendations.append(
                "Review active outbound connections."
            )

        if features.privilege_escalations > 0:
            evidence.append(
                f"{features.privilege_escalations} privilege escalation event(s)."
            )
            recommendations.append(
                "Review privileged operations immediately."
            )

        if anomaly_score < -0.75:
            severity = "Critical"

        elif anomaly_score < -0.55:
            severity = "High"

        elif anomaly_score < -0.35:
            severity = "Medium"

        return ThreatIncident(

            anomaly_score=anomaly_score,

            severity=severity,

            confidence=confidence,

            triggered_features=features.model_dump(),

            evidence=evidence,

            recommended_actions=recommendations,
        )