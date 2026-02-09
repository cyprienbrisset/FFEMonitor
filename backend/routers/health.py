"""
Router pour les endpoints de santé de l'application.
"""

from fastapi import APIRouter, Depends

from backend.models import HealthResponse, MessageResponse
from backend.middleware.supabase_auth import get_current_user, UserContext

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


@router.get("/debug/supabase")
async def debug_supabase():
    """
    Debug endpoint pour tester la connexion Supabase.
    """
    from backend.supabase_client import supabase
    from backend.config import settings

    result = {
        "supabase_url": settings.supabase_url[:50] + "..." if settings.supabase_url else None,
        "supabase_configured": settings.supabase_configured,
        "supabase_fully_configured": settings.supabase_fully_configured,
        "has_anon_key": bool(settings.supabase_anon_key_resolved),
        "has_service_key": bool(settings.supabase_service_key),
        "client_initialized": supabase._client is not None,
        "service_client_initialized": supabase._service_client is not None,
    }

    # Tester l'accès à la table concours
    if supabase._service_client:
        try:
            response = supabase._service_client.table("concours").select("*").limit(1).execute()
            result["concours_table_access"] = "OK"
            result["concours_count"] = len(response.data) if response.data else 0
        except Exception as e:
            result["concours_table_access"] = f"ERREUR: {str(e)}"

        # Tester un insert
        try:
            test_data = {"numero": 999999, "statut": "ferme", "is_open": False}
            insert_response = supabase._service_client.table("concours").upsert(
                test_data, on_conflict="numero"
            ).execute()
            result["concours_insert_test"] = "OK"
            # Supprimer le test
            supabase._service_client.table("concours").delete().eq("numero", 999999).execute()
            result["concours_delete_test"] = "OK"
        except Exception as e:
            result["concours_insert_test"] = f"ERREUR: {str(e)}"
    else:
        result["concours_table_access"] = "service_client non disponible"

    return result


@router.get("/debug/push-subscription")
async def debug_push_subscription(
    user: UserContext = Depends(get_current_user)
):
    """Debug: vérifie le statut de la subscription OneSignal de l'utilisateur."""
    from backend.main import app_state
    from backend.config import settings

    result = {
        "user_id": user.id,
        "onesignal_player_id": user.onesignal_player_id,
        "onesignal_configured": settings.onesignal_configured,
    }

    if not user.onesignal_player_id:
        result["error"] = "Pas d'ID de subscription push enregistré"
        return result

    notifier = app_state.get("notifier")
    if notifier and notifier.onesignal:
        check = await notifier.onesignal.check_subscription(user.onesignal_player_id)
        result["onesignal_check"] = check

    return result


@router.post("/test-push", response_model=MessageResponse)
async def test_push_notification(
    user: UserContext = Depends(get_current_user)
) -> MessageResponse:
    """
    Envoie une notification push de test via OneSignal à l'utilisateur connecté.

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
        # Méthode principale : cibler par external_id (Supabase user ID)
        # Nécessite que le frontend ait fait OneSignal.login(userId)
        success, detail = await notifier.onesignal.send_to_external_id(
            external_id=user.id,
            title="🐴 Hoofs - Test",
            message="Les notifications push fonctionnent correctement !",
            url="/app",
        )

        if success:
            return MessageResponse(message="Notification push de test envoyée", success=True)

        # Fallback : essayer par subscription_id si external_id échoue
        if user.onesignal_player_id:
            success2, detail2 = await notifier.onesignal.send_test_notification(user.onesignal_player_id)
            if success2:
                return MessageResponse(message="Notification push envoyée (via subscription ID)", success=True)
            detail = f"{detail} | Fallback: {detail2}"

        return MessageResponse(message=detail, success=False)
    except Exception as e:
        return MessageResponse(message=f"Erreur: {str(e)}", success=False)


@router.post("/test-email", response_model=MessageResponse)
async def test_email_notification(
    user: UserContext = Depends(get_current_user)
) -> MessageResponse:
    """
    Envoie une notification email de test via Supabase Edge Function.

    Returns:
        MessageResponse avec le résultat
    """
    from backend.main import app_state
    from backend.config import settings

    notifier = app_state.get("notifier")
    if not notifier:
        return MessageResponse(message="Notifier non initialisé", success=False)

    if not settings.resend_configured:
        return MessageResponse(
            message="Resend non configuré (RESEND_API_KEY manquant)",
            success=False
        )

    if not notifier.email:
        return MessageResponse(message="Email notifier non disponible", success=False)

    # Vérifier si l'utilisateur a un email
    if not user.email:
        return MessageResponse(
            message="Aucune adresse email associée à votre compte",
            success=False
        )

    try:
        # Envoyer un email de test à cet utilisateur
        success, message = await notifier.email.send_test_notification(user.email)
        if success:
            return MessageResponse(
                message=message,
                success=True
            )
        else:
            return MessageResponse(
                message=f"Échec: {message}",
                success=False
            )
    except Exception as e:
        return MessageResponse(message=f"Erreur: {str(e)}", success=False)
