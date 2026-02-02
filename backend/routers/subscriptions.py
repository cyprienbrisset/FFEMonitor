"""
Router pour la gestion des abonnements aux concours.
Permet aux utilisateurs de s'abonner/désabonner des concours.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.middleware.supabase_auth import get_current_user, UserContext
from backend.supabase_client import supabase
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


# ==================== Modèles Pydantic ====================


class ConcoursInfo(BaseModel):
    """Informations d'un concours."""

    numero: int
    nom: Optional[str] = None
    lieu: Optional[str] = None
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None
    discipline: Optional[str] = None
    statut: str = "previsionnel"
    is_open: bool = False


class SubscriptionResponse(BaseModel):
    """Réponse pour un abonnement."""

    id: str
    concours_numero: int
    notified: bool
    created_at: str
    concours: Optional[ConcoursInfo] = None


class SubscriptionListResponse(BaseModel):
    """Liste des abonnements."""

    subscriptions: List[SubscriptionResponse]
    count: int


class ProfileResponse(BaseModel):
    """Profil utilisateur."""

    id: str
    email: str
    plan: str
    onesignal_player_id: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    notification_email: bool = True
    notification_push: bool = True


class ProfileUpdateRequest(BaseModel):
    """Requête de mise à jour du profil."""

    onesignal_player_id: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    notification_email: Optional[bool] = None
    notification_push: Optional[bool] = None


# ==================== Endpoints ====================


@router.get("", response_model=SubscriptionListResponse)
async def list_subscriptions(
    user: UserContext = Depends(get_current_user),
):
    """
    Liste tous les abonnements de l'utilisateur connecté.
    """
    subscriptions = await supabase.get_user_subscriptions(user.id)

    formatted = []
    for sub in subscriptions:
        concours_data = sub.get("concours")
        concours_info = None
        if concours_data:
            concours_info = ConcoursInfo(
                numero=concours_data.get("numero"),
                nom=concours_data.get("nom"),
                lieu=concours_data.get("lieu"),
                date_debut=concours_data.get("date_debut"),
                date_fin=concours_data.get("date_fin"),
                discipline=concours_data.get("discipline"),
                statut=concours_data.get("statut", "previsionnel"),
                is_open=concours_data.get("is_open", False),
            )

        formatted.append(
            SubscriptionResponse(
                id=sub.get("id"),
                concours_numero=sub.get("concours_numero"),
                notified=sub.get("notified", False),
                created_at=sub.get("created_at"),
                concours=concours_info,
            )
        )

    return SubscriptionListResponse(
        subscriptions=formatted,
        count=len(formatted),
    )


@router.post("/{numero}", status_code=status.HTTP_201_CREATED)
async def subscribe_to_concours(
    numero: int,
    user: UserContext = Depends(get_current_user),
):
    """
    S'abonner à un concours.
    Le concours est créé dans la table partagée s'il n'existe pas.
    """
    # Vérifier si le concours existe, sinon le créer
    existing = await supabase.get_concours(numero)
    if not existing:
        # Créer le concours avec des infos minimales
        # Le scraper remplira les détails plus tard
        await supabase.upsert_concours(
            {
                "numero": numero,
                "statut": "previsionnel",
                "is_open": False,
            }
        )
        logger.info(f"Concours {numero} créé dans la base")

    # Créer l'abonnement
    success = await supabase.subscribe_to_concours(user.id, numero)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Déjà abonné à ce concours",
        )

    logger.info(f"Utilisateur {user.email} abonné au concours {numero}")

    return {
        "message": f"Abonné au concours {numero}",
        "concours_numero": numero,
    }


@router.delete("/{numero}", status_code=status.HTTP_200_OK)
async def unsubscribe_from_concours(
    numero: int,
    user: UserContext = Depends(get_current_user),
):
    """
    Se désabonner d'un concours.
    """
    success = await supabase.unsubscribe_from_concours(user.id, numero)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Abonnement non trouvé",
        )

    logger.info(f"Utilisateur {user.email} désabonné du concours {numero}")

    return {
        "message": f"Désabonné du concours {numero}",
        "concours_numero": numero,
    }


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    user: UserContext = Depends(get_current_user),
):
    """
    Récupérer le profil de l'utilisateur connecté.
    """
    profile = await supabase.get_user_profile(user.id)

    if not profile:
        return ProfileResponse(
            id=user.id,
            email=user.email,
            plan=user.plan,
        )

    return ProfileResponse(
        id=profile.get("id"),
        email=profile.get("email"),
        plan=profile.get("plan", "free"),
        onesignal_player_id=profile.get("onesignal_player_id"),
        telegram_chat_id=profile.get("telegram_chat_id"),
        notification_email=profile.get("notification_email", True),
        notification_push=profile.get("notification_push", True),
    )


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    updates: ProfileUpdateRequest,
    user: UserContext = Depends(get_current_user),
):
    """
    Mettre à jour le profil de l'utilisateur (préférences notifications).
    """
    update_data = {}

    if updates.onesignal_player_id is not None:
        update_data["onesignal_player_id"] = updates.onesignal_player_id
    if updates.telegram_chat_id is not None:
        update_data["telegram_chat_id"] = updates.telegram_chat_id
    if updates.notification_email is not None:
        update_data["notification_email"] = updates.notification_email
    if updates.notification_push is not None:
        update_data["notification_push"] = updates.notification_push

    if update_data:
        success = await supabase.update_user_profile(user.id, update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la mise à jour du profil",
            )

    # Retourner le profil mis à jour
    return await get_profile(user)
