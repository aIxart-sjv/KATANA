from pydantic import BaseModel


class BehaviorFeatures(BaseModel):
    # Process behavior
    process_creation_rate: float = 0.0
    process_termination_rate: float = 0.0
    unique_process_count: int = 0

    # Resource behavior
    average_cpu: float = 0.0
    maximum_cpu: float = 0.0
    average_memory: float = 0.0
    maximum_memory: float = 0.0

    # Network behavior
    external_connections: int = 0

    # Authentication
    failed_logins: int = 0
    privilege_escalations: int = 0

    # Filesystem
    filesystem_modifications: int = 0

    # Services
    service_restarts: int = 0

    # Kernel behavior
    kernel_exec_count: int = 0
    kernel_connect_count: int = 0
    kernel_open_count: int = 0
    kernel_unlink_count: int = 0
    kernel_setuid_count: int = 0
    kernel_ptrace_count: int = 0