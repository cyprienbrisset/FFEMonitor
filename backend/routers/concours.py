"""
Router pour les opérations CRUD sur les concours.
Toutes les routes nécessitent une authentification.
"""

from fastapi import APIRouter, HTTPException, status, Depends

from backend.database import db
from backend.models import (
    ConcoursCreate,
    ConcoursListResponse,
    ConcoursResponse,
    MessageResponse,
    StatusResponse,
)
from backend.routers.auth import require_auth
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


@router.post("", response_model=ConcoursResponse, status_code=status.HTTP_201_CREATED)
async def add_concours(data: ConcoursCreate) -> ConcoursResponse:
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
