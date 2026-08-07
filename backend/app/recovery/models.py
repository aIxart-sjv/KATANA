from pydantic import BaseModel


class RecoveryPlan(BaseModel):

    steps: list[str]

    priority: str