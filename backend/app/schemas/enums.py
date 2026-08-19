from enum import Enum


class EventSource(str, Enum):
    PROCESS = "process"
    SYSTEM = "system"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    KERNEL = "kernel"
    AUTH = "auth"


class EventSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(str, Enum):
    # Process Events
    PROCESS_STARTED = "process_started"
    PROCESS_TRACED = "process_traced"
    PROCESS_TERMINATED = "process_terminated"
    CPU_SPIKE = "cpu_spike"
    MEMORY_SPIKE = "memory_spike"

    # Network Events
    CONNECTION_OPENED = "connection_opened"
    CONNECTION_CLOSED = "connection_closed"
    EXTERNAL_CONNECTION = "external_connection"
    NETWORK_CONNECT = "network_connect"
    NETWORK_ACCEPT = "network_accept"

    # Filesystem Events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_OPENED = "file_opened"

    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    PRIVILEGE_ESCALATION = "privilege_escalation"

    # System
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"

    # Kernel Events
    KERNEL_EXEC = "kernel_exec"
    KERNEL_CONNECT = "kernel_connect"
    KERNEL_OPEN = "kernel_open"
    KERNEL_UNLINK = "kernel_unlink"
    KERNEL_SETUID = "kernel_setuid"
    KERNEL_PTRACE = "kernel_ptrace"