"""
Router pour les opérations CRUD sur les concours.
Toutes les routes nécessitent une authentification.
Utilise Supabase comme base de données.
"""

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime

from backend.supabase_client import supabase
from backend.models import (
    ConcoursCreate,
    ConcoursListResponse,
    ConcoursResponse,
    MessageResponse,
    StatusResponse,
)
from backend.middleware.supabase_auth import get_current_user
from backend.services.scraper import scraper
from backend.utils.logger import get_logger

logger = get_logger("api.concours")

router = APIRouter(
    prefix="/concours",
    tags=["Concours"],
    dependencies=[Depends(get_current_user)],  # Authentification Supabase requise
)


def _format_concours_response(c: dict) -> dict:
    """Formate un concours pour la réponse API."""
    return {
        "numero": c.get("numero"),
        "nom": c.get("nom"),
        "statut": c.get("statut", "ferme"),
        "notifie": c.get("is_open", False),
        "last_check": c.get("last_check"),
        "created_at": c.get("created_at"),
        "date_debut": c.get("date_debut"),
        "date_fin": c.get("date_fin"),
        "lieu": c.get("lieu"),
    }


@router.get("", response_model=ConcoursListResponse)
async def list_concours(
    current_user = Depends(get_current_user),
) -> ConcoursListResponse:
    """
    Liste les concours surveillés par l'utilisateur connecté.

    Returns:
        Liste des concours avec leur statut actuel
    """
    # Récupérer uniquement les concours auxquels l'utilisateur est abonné
    concours_list = await supabase.get_user_subscribed_concours(current_user.id)

    return ConcoursListResponse(
        concours=[ConcoursResponse(**_format_concours_response(c)) for c in concours_list],
        total=len(concours_list),
    )


async def _scrape_and_update_concours(numero: int) -> None:
    """Scrape les infos du concours et met à jour la base."""
    try:
        info = await scraper.fetch_concours_info(numero)

        update_data = {}
        if info.nom:
            update_data["nom"] = info.nom
        if info.lieu:
            update_data["lieu"] = info.lieu
        if info.date_debut:
            update_data["date_debut"] = info.date_debut
        if info.date_fin:
            update_data["date_fin"] = info.date_fin
        if info.statut:
            update_data["statut"] = info.statut
        # IMPORTANT: Utiliser is_open du scraper, pas calculé depuis statut
        update_data["is_open"] = info.is_open

        update_data["last_check"] = datetime.now().isoformat()

        if update_data:
            await supabase.update_concours(numero, update_data)
            logger.info(f"Infos scrappées pour concours {numero}: {info.nom}")

    except Exception as e:
        logger.error(f"Erreur scraping concours {numero}: {e}")


@router.post("", response_model=ConcoursResponse, status_code=status.HTTP_201_CREATED)
async def add_concours(
    data: ConcoursCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
) -> ConcoursResponse:
    """
    Ajoute un concours à surveiller.

    Args:
        data: Numéro du concours à ajouter

    Returns:
        Le concours créé

    Raises:
        HTTPException 409: Si le concours est déjà surveillé
    """
    logger.info(f"=== ADD CONCOURS: Reçu numéro {data.numero} ===")

    # Vérifier si le concours existe déjà
    existing = await supabase.get_concours(data.numero)
    logger.info(f"Concours existant: {existing}")

    user_id = current_user.id

    if existing:
        # Le concours existe - abonner l'utilisateur s'il ne l'est pas déjà
        if user_id:
            try:
                await supabase.subscribe_to_concours(user_id, data.numero)
                logger.info(f"Utilisateur {user_id} abonné au concours existant {data.numero}")
            except Exception as e:
                # Probablement déjà abonné (contrainte UNIQUE)
                logger.debug(f"Abonnement déjà existant ou erreur: {e}")

        return ConcoursResponse(**_format_concours_response(existing))

    # Créer le concours (colonnes minimales)
    concours_data = {
        "numero": data.numero,
        "statut": "ferme",
        "is_open": False,
    }

    try:
        logger.info(f"Appel upsert_concours avec: {concours_data}")
        success = await supabase.upsert_concours(concours_data)
        logger.info(f"Résultat upsert_concours: {success}")
        if not success:
            logger.error(f"Échec upsert_concours pour {data.numero} - retour False")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la création du concours - vérifiez que la table 'concours' existe dans Supabase",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception lors de upsert_concours pour {data.numero}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du concours: {str(e)}",
        )

    # Scraper les infos du concours en arrière-plan
    background_tasks.add_task(_scrape_and_update_concours, data.numero)

    # Abonner automatiquement l'utilisateur au concours
    if user_id:
        try:
            await supabase.subscribe_to_concours(user_id, data.numero)
            logger.info(f"Utilisateur {user_id} abonné au concours {data.numero}")
        except Exception as e:
            logger.warning(f"Impossible d'abonner l'utilisateur au concours: {e}")

    # Récupérer le concours créé
    concours = await supabase.get_concours(data.numero)

    logger.info(f"Concours {data.numero} ajouté à la surveillance")
    return ConcoursResponse(**_format_concours_response(concours))


@router.get("/{numero}", response_model=ConcoursResponse)
async def get_concours(numero: int) -> ConcoursResponse:
    """
    Récupère un concours par son numéro.

    Args:
        numero: Numéro du concours

    Returns:
        Le concours

    Raises:
        HTTPException 404: Si le concours n'est pas trouvé
    """
    concours = await supabase.get_concours(numero)

    if concours is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concours {numero} non trouvé",
        )

    return ConcoursResponse(**_format_concours_response(concours))


@router.post("/{numero}/refresh", response_model=ConcoursResponse)
async def refresh_concours(numero: int) -> ConcoursResponse:
    """
    Rafraîchit les informations scrappées d'un concours.

    Args:
        numero: Numéro du concours

    Returns:
        Le concours avec les infos mises à jour

    Raises:
        HTTPException 404: Si le concours n'est pas trouvé
    """
    concours = await supabase.get_concours(numero)
    if concours is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concours {numero} non trouvé",
        )

    # Scraper les infos
    await _scrape_and_update_concours(numero)

    # Récupérer le concours mis à jour
    concours = await supabase.get_concours(numero)

    logger.info(f"Infos rafraîchies pour concours {numero}")
    return ConcoursResponse(**_format_concours_response(concours))


@router.delete("/{numero}", response_model=MessageResponse)
async def delete_concours(
    numero: int,
    current_user = Depends(get_current_user),
) -> MessageResponse:
    """
    Retire un concours de la surveillance de l'utilisateur.

    Args:
        numero: Numéro du concours à retirer

    Returns:
        Message de confirmation

    Raises:
        HTTPException 404: Si le concours n'est pas trouvé
    """
    # Vérifier que le concours existe
    concours = await supabase.get_concours(numero)
    if concours is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concours {numero} non trouvé",
        )

    # Supprimer uniquement l'abonnement de l'utilisateur (pas le concours lui-même)
    deleted = await supabase.unsubscribe_from_concours(current_user.id, numero)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vous n'êtes pas abonné au concours {numero}",
        )

    return MessageResponse(
        message=f"Concours {numero} retiré de votre surveillance",
        success=True,
    )


@router.get("/status/global", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """
    Retourne le statut global de l'application.

    Returns:
        Statut de connexion FFE et surveillance
    """
    from backend.main import app_state

    concours_list = await supabase.get_all_concours()
    concours_ouverts = sum(1 for c in concours_list if c.get("statut") != "ferme")

    # Trouver la dernière vérification
    last_checks = [c.get("last_check") for c in concours_list if c.get("last_check")]
    last_check = max(last_checks) if last_checks else None

    return StatusResponse(
        ffe_connected=app_state.get("ffe_connected", False),
        surveillance_active=app_state.get("surveillance_active", False),
        last_check=last_check,
        concours_surveilles=len(concours_list),
        concours_ouverts=concours_ouverts,
    )
