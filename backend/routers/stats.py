"""
Router pour les statistiques et l'historique.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query

from backend.database import db
from backend.models import (
    ConcoursStatsResponse,
    GlobalStatsResponse,
    ActivityDataResponse,
)
from backend.routers.auth import require_auth
from backend.utils.logger import get_logger

logger = get_logger("api.stats")

router = APIRouter(
    prefix="/stats",
    tags=["Statistics"],
    dependencies=[Depends(require_auth)],
)


@router.get("/global", response_model=GlobalStatsResponse)
async def get_global_stats() -> GlobalStatsResponse:
    """
    Récupère les statistiques globales de l'application.

    Returns:
        Statistiques globales incluant nombre de concours,
        vérifications, ouvertures, etc.
    """
    stats = await db.get_global_stats()
    return GlobalStatsResponse(**stats)


@router.get("/concours/{numero}", response_model=ConcoursStatsResponse)
async def get_concours_stats(numero: int) -> ConcoursStatsResponse:
    """
    Récupère les statistiques détaillées d'un concours.

    Args:
        numero: Numéro du concours

    Returns:
        Statistiques du concours

    Raises:
        HTTPException 404: Si le concours n'existe pas
    """
    # Vérifier que le concours existe
    concours = await db.get_concours_by_numero(numero)
    if not concours:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concours {numero} non trouvé",
        )

    stats = await db.get_concours_stats(numero)
    return ConcoursStatsResponse(**stats)


@router.get("/activity", response_model=ActivityDataResponse)
async def get_activity_data(
    period: str = Query("24h", pattern="^(24h|7d)$"),
) -> ActivityDataResponse:
    """
    Récupère les données d'activité pour le graphique.

    Args:
        period: Période - "24h" pour les dernières 24 heures,
                "7d" pour les 7 derniers jours

    Returns:
        Données formatées pour Chart.js avec labels,
        nombre de vérifications et ouvertures
    """
    data = await db.get_activity_data(period)
    return ActivityDataResponse(**data)
