"""
Router pour les statistiques et l'historique.
Utilise Supabase comme base de données.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query

from backend.supabase_client import supabase
from backend.models import (
    GlobalStatsResponse,
)
from backend.middleware.supabase_auth import get_current_user
from backend.utils.logger import get_logger

logger = get_logger("api.stats")

router = APIRouter(
    prefix="/stats",
    tags=["Statistics"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/global", response_model=GlobalStatsResponse)
async def get_global_stats() -> GlobalStatsResponse:
    """
    Récupère les statistiques globales de l'application.

    Returns:
        Statistiques globales incluant nombre de concours,
        vérifications, ouvertures, etc.
    """
    stats = await supabase.get_global_stats()

    return GlobalStatsResponse(
        total_concours=stats.get("total_concours", 0),
        concours_ouverts=stats.get("concours_ouverts", 0),
        total_checks=stats.get("total_checks", 0),
        checks_today=0,  # TODO: implement
        total_openings=stats.get("total_openings", 0),
        avg_response_time_ms=0,
        success_rate=100.0,
    )
