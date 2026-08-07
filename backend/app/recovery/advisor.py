from app.recovery.models import RecoveryPlan
from app.threat_engine.models import ThreatIncident


class RecoveryAdvisor:

    def generate(
        self,
        incident: ThreatIncident,
    ) -> RecoveryPlan:

        return RecoveryPlan(

            priority=incident.severity,

            steps=[

                "Review running processes.",

                "Review authentication logs.",

                "Inspect modified files.",

                "Rotate credentials if required.",

                "Verify persistence mechanisms.",

            ],
        )