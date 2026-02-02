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
