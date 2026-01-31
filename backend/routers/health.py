"""
Router pour les endpoints de santé de l'application.
"""

from fastapi import APIRouter

from backend.models import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Vérifie l'état de santé de l'application.

    Returns:
        HealthResponse avec le statut actuel
    """
    # Import différé pour éviter les imports circulaires
    from backend.main import app_state

    return HealthResponse(
        status="ok",
        ffe_connected=app_state.get("ffe_connected", False),
        surveillance_active=app_state.get("surveillance_active", False),
        concours_count=app_state.get("concours_count", 0),
    )
