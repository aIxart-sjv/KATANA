from pydantic import BaseModel


class BehaviorFeatures(BaseModel):
    process_creation_rate: float = 0.0
    process_termination_rate: float = 0.0

    unique_process_count: int = 0

    average_cpu: float = 0.0
    maximum_cpu: float = 0.0

    average_memory: float = 0.0
    maximum_memory: float = 0.0

    external_connections: int = 0

    failed_logins: int = 0

    privilege_escalations: int = 0

    filesystem_modifications: int = 0

    service_restarts: int = 0