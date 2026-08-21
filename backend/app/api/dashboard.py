from fastapi import APIRouter

from app.state.dashboard import dashboard_state


router = APIRouter(
    prefix="/api"
)


@router.get("/dashboard")
async def get_dashboard():
    """
    Return the current KATANA dashboard state.
    """

    return dashboard_state.snapshot()