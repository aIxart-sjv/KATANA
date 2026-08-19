from pydantic import BaseModel


class AIAnalysis(BaseModel):
    summary: str
    analysis: str
    risk: str
    mitre_attack: list[str]
