from app.response_engine.models import ResponseAction
from app.response_engine.validators import ResponseValidator


class ResponseExecutor:
    """
    Safe response layer.

    KATANA NEVER executes remediation automatically.

    This component only validates and presents the action that
    should be shown to the user for manual execution.
    """

    def __init__(self):
        self.validator = ResponseValidator()

    def execute(
        self,
        action: ResponseAction,
    ) -> dict:

        if not self.validator.validate(action):
            raise PermissionError(
                "Response action rejected by validator."
            )

        return {
            "executed": False,
            "requires_confirmation": True,
            "action": action.action.value,
            "description": action.description,
            "parameters": action.parameters,
            "message": (
                "KATANA does not execute remediation automatically. "
                "Review and perform the recommended action manually."
            ),
        }