from pydantic import BaseModel


class AIAnalysis(BaseModel):
    summary: str

    technical_analysis: str

    impact: str

    mitre_attack: list[str]

    recommendations: list[str]

    linux_commands: list[str]

    recovery_steps: list[str]