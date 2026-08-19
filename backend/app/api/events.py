from fastapi import APIRouter

from app.ml import anomaly_engine

router = APIRouter(prefix="/api")


@router.get("/ml/status")
async def ml_status():
    return {
        "status": (
            "monitoring"
            if anomaly_engine.model.trained
            else "learning"
        ),
        "trained": anomaly_engine.model.trained,
        "baseline_samples": len(
            anomaly_engine.baseline.samples
        ),
        "baseline_required": (
            anomaly_engine.baseline.baseline_size
        ),
        "threshold": anomaly_engine.model.threshold,
    }
