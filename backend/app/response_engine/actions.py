from app.response_engine.models import (
    ActionType,
    ResponseAction,
)


def terminate_process(pid: int):

    return ResponseAction(
        action=ActionType.TERMINATE_PROCESS,
        description=f"Terminate process {pid}",
        parameters={
            "pid": pid,
        },
    )


def block_ip(ip: str):

    return ResponseAction(
        action=ActionType.BLOCK_IP,
        description=f"Block IP {ip}",
        parameters={
            "ip": ip,
        },
    )