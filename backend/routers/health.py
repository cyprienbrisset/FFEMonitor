"""
Router pour les endpoints de santé de l'application.
"""

from fastapi import APIRouter, Depends

from backend.models import HealthResponse, MessageResponse
from backend.routers.auth import require_auth

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


@router.post("/test-email", response_model=MessageResponse, dependencies=[Depends(require_auth)])
async def test_email_notification() -> MessageResponse:
    """
    Envoie un email de test via Resend.

    Returns:
        MessageResponse avec le résultat
    """
    from backend.main import app_state
    from backend.config import settings

    notifier = app_state.get("notifier")
    if not notifier:
        return MessageResponse(message="Notifier non initialisé", success=False)

    if not settings.email_configured:
        return MessageResponse(
            message="Email non configuré (RESEND_API_KEY, EMAIL_TO manquants)",
            success=False
        )

    try:
        # Envoyer un email de test
        success = await notifier.email.send_test()
        if success:
            return MessageResponse(message=f"Email de test envoyé à {settings.email_to}", success=True)
        else:
            return MessageResponse(message="Échec de l'envoi de l'email", success=False)
    except Exception as e:
        return MessageResponse(message=f"Erreur: {str(e)}", success=False)


@router.post("/test-telegram", response_model=MessageResponse, dependencies=[Depends(require_auth)])
async def test_telegram_notification() -> MessageResponse:
    """
    Envoie un message Telegram de test.

    Returns:
        MessageResponse avec le résultat
    """
    from backend.main import app_state

    notifier = app_state.get("notifier")
    if not notifier:
        return MessageResponse(message="Notifier non initialisé", success=False)

    try:
        success = await notifier.telegram.send_test()
        if success:
            return MessageResponse(message="Message Telegram de test envoyé", success=True)
        else:
            return MessageResponse(message="Échec de l'envoi Telegram", success=False)
    except Exception as e:
        return MessageResponse(message=f"Erreur: {str(e)}", success=False)
