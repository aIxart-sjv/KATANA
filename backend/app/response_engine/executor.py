import psutil

from app.response_engine.models import (
    ActionType,
    ResponseAction,
)
from app.response_engine.validators import ResponseValidator


class ResponseExecutor:

    def __init__(self):

        self.validator = ResponseValidator()

    def execute(
        self,
        action: ResponseAction,
    ):

        if not self.validator.validate(action):
            raise PermissionError()

        match action.action:

            case ActionType.TERMINATE_PROCESS:

                pid = action.parameters["pid"]

                psutil.Process(pid).terminate()

            case ActionType.BLOCK_IP:

                # TODO

                pass

            case _:

                raise NotImplementedError()