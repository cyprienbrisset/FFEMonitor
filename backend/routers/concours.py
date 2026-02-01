"""
Router pour les opérations CRUD sur les concours.
Toutes les routes nécessitent une authentification.
"""

import asyncio
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks

from backend.database import db
from backend.models import (
    ConcoursCreate,
    ConcoursListResponse,
    ConcoursResponse,
    MessageResponse,
    StatusResponse,
)
from backend.routers.auth import require_auth
from backend.services.scraper import scraper
from backend.utils.logger import get_logger

logger = get_logger("api.concours")

router = APIRouter(
    prefix="/concours",
    tags=["Concours"],
    dependencies=[Depends(require_auth)],  # Authentification requise
)


@router.get("", response_model=ConcoursListResponse)
async def list_concours() -> ConcoursListResponse:
    """
    Liste tous les concours surveillés.

    Returns:
        Liste des concours avec leur statut actuel
    """
    concours_list = await db.get_all_concours()

    return ConcoursListResponse(
        concours=[ConcoursResponse(**c) for c in concours_list],
        total=len(concours_list),
    )


async def _scrape_and_update_concours(numero: int) -> None:
    """Scrape les infos du concours et met à jour la base."""
    from backend.models import StatutConcours

    try:
        info = await scraper.fetch_concours_info(numero)
        if info.nom or info.lieu or info.date_debut:
            await db.update_concours_info(
                numero=numero,
                nom=info.nom,
                lieu=info.lieu,
                date_debut=info.date_debut,
                date_fin=info.date_fin,
            )
            logger.info(f"Infos scrappées pour concours {numero}: {info.nom}")

        # Mettre à jour le statut si ouvert aux engagements
        if info.is_open:
            await db.update_statut(numero, StatutConcours.ENGAGEMENT, notifie=False)
            logger.info(f"Concours {numero} détecté comme ouvert")
    except Exception as e:
        logger.error(f"Erreur scraping concours {numero}: {e}")


@router.post("", response_model=ConcoursResponse, status_code=status.HTTP_201_CREATED)
async def add_concours(
    data: ConcoursCreate,
    background_tasks: BackgroundTasks,
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
    concours = await db.add_concours(data.numero)

    if concours is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Le concours {data.numero} est déjà surveillé",
        )

    # Scraper les infos du concours en arrière-plan
    background_tasks.add_task(_scrape_and_update_concours, data.numero)

    logger.info(f"Concours {data.numero} ajouté à la surveillance")
    return ConcoursResponse(**concours)


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
    concours = await db.get_concours_by_numero(numero)

    if concours is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concours {numero} non trouvé",
        )

    return ConcoursResponse(**concours)


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
    concours = await db.get_concours_by_numero(numero)
    if concours is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concours {numero} non trouvé",
        )

    from backend.models import StatutConcours

    # Scraper les infos
    info = await scraper.fetch_concours_info(numero)
    if info.nom or info.lieu or info.date_debut:
        await db.update_concours_info(
            numero=numero,
            nom=info.nom,
            lieu=info.lieu,
            date_debut=info.date_debut,
            date_fin=info.date_fin,
        )

    # Mettre à jour le statut si ouvert
    if info.is_open:
        await db.update_statut(numero, StatutConcours.ENGAGEMENT, notifie=False)

    # Récupérer le concours mis à jour
        concours = await db.get_concours_by_numero(numero)

    logger.info(f"Infos rafraîchies pour concours {numero}")
    return ConcoursResponse(**concours)


@router.delete("/{numero}", response_model=MessageResponse)
async def delete_concours(numero: int) -> MessageResponse:
    """
    Retire un concours de la surveillance.

    Args:
        numero: Numéro du concours à retirer

    Returns:
        Message de confirmation

    Raises:
        HTTPException 404: Si le concours n'est pas trouvé
    """
    deleted = await db.delete_concours(numero)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concours {numero} non trouvé",
        )

    return MessageResponse(
        message=f"Concours {numero} retiré de la surveillance",
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

    concours_list = await db.get_all_concours()
    concours_ouverts = sum(1 for c in concours_list if c["statut"] != "ferme")

    # Trouver la dernière vérification
    last_checks = [c["last_check"] for c in concours_list if c["last_check"]]
    last_check = max(last_checks) if last_checks else None

    return StatusResponse(
        ffe_connected=app_state.get("ffe_connected", False),
        surveillance_active=app_state.get("surveillance_active", False),
        last_check=last_check,
        concours_surveilles=len(concours_list),
        concours_ouverts=concours_ouverts,
    )
