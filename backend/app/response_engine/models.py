from enum import Enum

from pydantic import BaseModel


class ActionType(str, Enum):
    TERMINATE_PROCESS = "terminate_process"
    STOP_SERVICE = "stop_service"
    RESTART_SERVICE = "restart_service"
    BLOCK_IP = "block_ip"
    QUARANTINE_FILE = "quarantine_file"
    NOTIFY_USER = "notify_user"


class ResponseAction(BaseModel):
    action: ActionType

    description: str

    parameters: dict

    requires_confirmation: bool = True