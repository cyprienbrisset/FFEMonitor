"""
Modèles Pydantic pour l'API EngageWatch.
Définition des schémas de requête et réponse.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class StatutConcours(str, Enum):
    """Statuts possibles d'un concours."""

    FERME = "ferme"
    ENGAGEMENT = "engagement"  # Bouton "Engager" détecté
    DEMANDE = "demande"  # Bouton "Demande de participation" détecté


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
    statut: StatutConcours
    notifie: bool
    last_check: datetime | None
    created_at: datetime

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
