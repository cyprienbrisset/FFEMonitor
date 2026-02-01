"""
Modèles Pydantic pour l'API EngageWatch.
Définition des schémas de requête et réponse.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class StatutConcours(str, Enum):
    """Statuts possibles d'un concours."""

    PREVISIONNEL = "previsionnel"  # Concours prévu mais pas encore ouvert
    ENGAGEMENT = "engagement"  # Ouvert aux engagements
    DEMANDE = "demande"  # Demande de participation (international)
    CLOTURE = "cloture"  # Engagements clôturés
    EN_COURS = "en_cours"  # Concours en cours
    TERMINE = "termine"  # Concours terminé
    ANNULE = "annule"  # Concours annulé
    FERME = "ferme"  # État inconnu/par défaut


class ConcoursCreate(BaseModel):
    """Schéma pour créer un concours à surveiller."""

    numero: int = Field(..., gt=0, description="Numéro du concours FFE")

    model_config = {
        "json_schema_extra": {
            "examples": [{"numero": 123456}]
        }
    }


class ConcoursResponse(BaseModel):
    """Schéma de réponse pour un concours."""

    id: int
    numero: int
    nom: str | None = None
    statut: StatutConcours
    notifie: bool
    last_check: datetime | None
    created_at: datetime
    date_debut: str | None = None
    date_fin: str | None = None
    lieu: str | None = None

    model_config = {
        "from_attributes": True
    }


class ConcoursListResponse(BaseModel):
    """Schéma de réponse pour la liste des concours."""

    concours: list[ConcoursResponse]
    total: int


class HealthResponse(BaseModel):
    """Schéma de réponse pour le health check."""

    status: str = "ok"
    ffe_connected: bool = False
    surveillance_active: bool = False
    concours_count: int = 0


class StatusResponse(BaseModel):
    """Schéma de réponse pour le statut global."""

    ffe_connected: bool
    surveillance_active: bool
    last_check: datetime | None
    concours_surveilles: int
    concours_ouverts: int


class MessageResponse(BaseModel):
    """Schéma de réponse générique avec message."""

    message: str
    success: bool = True


# ============================================================================
# Statistics Models
# ============================================================================


class CheckHistoryEntry(BaseModel):
    """Schéma pour une entrée d'historique de vérification."""

    id: int
    concours_numero: int
    checked_at: datetime
    statut_before: str | None
    statut_after: str | None
    response_time_ms: int
    success: bool


class OpeningEvent(BaseModel):
    """Schéma pour un événement d'ouverture."""

    id: int
    concours_numero: int
    opened_at: datetime
    statut: str
    notification_sent_at: datetime | None


class ConcoursStatsResponse(BaseModel):
    """Schéma de réponse pour les statistiques d'un concours."""

    numero: int
    total_checks: int
    successful_checks: int
    success_rate: float
    avg_response_time_ms: float
    opening_events: list[dict]


class GlobalStatsResponse(BaseModel):
    """Schéma de réponse pour les statistiques globales."""

    total_concours: int
    concours_ouverts: int
    total_checks: int
    checks_today: int
    total_openings: int
    avg_response_time_ms: float
    success_rate: float


class ActivityDataResponse(BaseModel):
    """Schéma de réponse pour les données d'activité (graphique)."""

    labels: list[str]
    checks: list[int]
    openings: list[int]
    period: str


# ============================================================================
# Calendar Models
# ============================================================================


class CalendarEvent(BaseModel):
    """Schéma pour un événement du calendrier."""

    numero: int
    nom: str | None = None
    date_debut: str | None
    date_fin: str | None
    lieu: str | None
    statut: StatutConcours
    notifie: bool


class CalendarEventsResponse(BaseModel):
    """Schéma de réponse pour les événements du calendrier."""

    events: list[CalendarEvent]
    month: int
    year: int
