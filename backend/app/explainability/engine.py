import json

from app.explainability.models import AIAnalysis
from app.explainability.prompts import SYSTEM_PROMPT
from app.threat_engine.models import ThreatIncident


class ExplainabilityEngine:

    def __init__(self, llm_client):
        self.llm = llm_client

    async def explain(
        self,
        incident: ThreatIncident,
    ) -> AIAnalysis:

        prompt = f"""
Incident

Severity:
{incident.severity}

Anomaly Score:
{incident.anomaly_score}

Evidence:
{incident.evidence}

Triggered Features:
{incident.triggered_features}

Recommended Actions:
{incident.recommended_actions}
"""

        response = await self.llm.generate(

            system=SYSTEM_PROMPT,

            prompt=prompt,

        )

        return AIAnalysis.model_validate(
            json.loads(response)
        )