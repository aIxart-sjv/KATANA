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
INCIDENT

Severity:
{incident.severity}

Anomaly Score:
{incident.anomaly_score}

Evidence:
{incident.evidence}

Triggered Features:
{incident.triggered_features}

Recommended Investigation Actions:
{incident.recommended_actions}
"""

        response = await self.llm.generate(
            system=SYSTEM_PROMPT,
            prompt=prompt,
        )

        # ----------------------------------------------------------
        # Remove accidental markdown fences from small local models
        # ----------------------------------------------------------

        response = response.strip()

        if response.startswith("```"):
            response = response.replace("```json", "", 1)
            response = response.replace("```", "")
            response = response.strip()

        # ----------------------------------------------------------
        # Parse strict JSON
        # ----------------------------------------------------------

        try:
            data = json.loads(response)

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"LLM returned invalid JSON: {exc}"
            ) from exc

        # ----------------------------------------------------------
        # Validate response schema
        # ----------------------------------------------------------

        return AIAnalysis.model_validate(data)
