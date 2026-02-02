"""
Router pour les fonctionnalités de calendrier.
Utilise Supabase comme base de données.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query

from backend.supabase_client import supabase
from backend.models import CalendarEvent, CalendarEventsResponse
from backend.middleware.supabase_auth import get_current_user
from backend.utils.logger import get_logger

logger = get_logger("api.calendar")

router = APIRouter(
    prefix="/calendar",
    tags=["Calendar"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/events", response_model=CalendarEventsResponse)
async def get_calendar_events(
    month: int = Query(None, ge=1, le=12),
    year: int = Query(None, ge=2020, le=2100),
) -> CalendarEventsResponse:
    """
    Récupère les événements du calendrier pour un mois donné.

    Args:
        month: Mois (1-12), par défaut le mois courant
        year: Année, par défaut l'année courante

    Returns:
        Liste des concours avec leurs dates pour le mois
    """
    # Utiliser le mois/année courant si non spécifié
    now = datetime.now()
    month = month or now.month
    year = year or now.year

    # Calculer les dates de début et fin du mois
    start_date = f"{year:04d}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1:04d}-01-01"
    else:
        end_date = f"{year:04d}-{month + 1:02d}-01"

    # Récupérer les concours dans la plage
    concours_list = await supabase.get_concours_by_date_range(start_date, end_date)

    # Convertir en événements du calendrier
    events = []
    for c in concours_list:
        events.append(
            CalendarEvent(
                numero=c.get("numero"),
                nom=c.get("nom"),
                date_debut=c.get("date_debut"),
                date_fin=c.get("date_fin"),
                lieu=c.get("lieu"),
                statut=c.get("statut", "ferme"),
                notifie=c.get("is_open", False),
            )
        )

    return CalendarEventsResponse(
        events=events,
        month=month,
        year=year,
    )


@router.get("/all-events")
async def get_all_calendar_events() -> dict:
    """
    Récupère tous les événements du calendrier.

    Returns:
        Liste de tous les concours avec dates
    """
    all_concours = await supabase.get_all_concours()

    events = []
    for c in all_concours:
        if c.get("date_debut"):
            events.append({
                "numero": c.get("numero"),
                "nom": c.get("nom"),
                "date_debut": c.get("date_debut"),
                "date_fin": c.get("date_fin"),
                "lieu": c.get("lieu"),
                "statut": c.get("statut", "ferme"),
                "notifie": c.get("is_open", False),
            })

    return {"events": events, "total": len(events)}
