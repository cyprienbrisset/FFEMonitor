"""
Router pour les endpoints de santé de l'application.
"""

from fastapi import APIRouter, Depends

from backend.models import HealthResponse, MessageResponse
from backend.routers.auth import require_auth

router = APIRouter(tags=["Health"])


@router.api_route("/health", methods=["GET", "HEAD"], response_model=HealthResponse)
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
        surveillance_active=app_state.get("surveillance_active", False),
        concours_count=app_state.get("concours_count", 0),
    )


@router.post("/test-push", response_model=MessageResponse, dependencies=[Depends(require_auth)])
async def test_push_notification() -> MessageResponse:
    """
    Envoie une notification push de test via OneSignal.

    Returns:
        MessageResponse avec le résultat
    """
    from backend.main import app_state
    from backend.config import settings

    notifier = app_state.get("notifier")
    if not notifier:
        return MessageResponse(message="Notifier non initialisé", success=False)

    if not settings.onesignal_configured:
        return MessageResponse(
            message="OneSignal non configuré (ONESIGNAL_APP_ID, ONESIGNAL_API_KEY manquants)",
            success=False
        )

    if not notifier.onesignal:
        return MessageResponse(message="OneSignal notifier non disponible", success=False)

    try:
        # Envoyer une notification de test à tous les abonnés
        success = await notifier.onesignal.send_startup_notification()
        if success:
            return MessageResponse(message="Notification push de test envoyée", success=True)
        else:
            return MessageResponse(message="Échec de l'envoi (aucun abonné?)", success=False)
    except Exception as e:
        return MessageResponse(message=f"Erreur: {str(e)}", success=False)
