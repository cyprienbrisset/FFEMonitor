"""
Middleware d'authentification Supabase pour FFE Monitor.
Vérifie les JWT tokens Supabase et injecte l'utilisateur dans les requêtes.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from backend.config import settings
from backend.supabase_client import supabase
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Security scheme pour le bearer token
security = HTTPBearer(auto_error=False)


class UserContext:
    """Contexte utilisateur pour les requêtes authentifiées."""

    def __init__(
        self,
        id: str,
        email: str,
        plan: str = "free",
        onesignal_player_id: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        notification_email: bool = True,
        notification_push: bool = True,
    ):
        self.id = id
        self.email = email
        self.plan = plan
        self.onesignal_player_id = onesignal_player_id
        self.telegram_chat_id = telegram_chat_id
        self.notification_email = notification_email
        self.notification_push = notification_push


def verify_supabase_token(token: str) -> Optional[dict]:
    """
    Vérifie un token JWT Supabase.

    Args:
        token: Le JWT token à vérifier

    Returns:
        Le payload du token si valide, None sinon
    """
    if not settings.supabase_jwt_secret:
        logger.warning("SUPABASE_JWT_SECRET non configuré")
        return None

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token Supabase expiré")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token Supabase invalide: {e}")
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> UserContext:
    """
    Dépendance FastAPI pour obtenir l'utilisateur courant.
    Lève une exception si non authentifié.

    Usage:
        @app.get("/protected")
        async def protected_route(user: UserContext = Depends(get_current_user)):
            return {"email": user.email}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification requis",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_supabase_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide: user_id manquant",
        )

    # Récupérer le profil utilisateur depuis Supabase
    profile = await supabase.get_user_profile(user_id)

    if not profile:
        # Créer un contexte minimal si pas de profil
        return UserContext(
            id=user_id,
            email=payload.get("email", ""),
            plan="free",
        )

    return UserContext(
        id=user_id,
        email=profile.get("email", payload.get("email", "")),
        plan=profile.get("plan", "free"),
        onesignal_player_id=profile.get("onesignal_player_id"),
        telegram_chat_id=profile.get("telegram_chat_id"),
        notification_email=profile.get("notification_email", True),
        notification_push=profile.get("notification_push", True),
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[UserContext]:
    """
    Dépendance FastAPI pour obtenir l'utilisateur courant optionnellement.
    Retourne None si non authentifié (pas d'exception).

    Usage:
        @app.get("/public-or-private")
        async def route(user: Optional[UserContext] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user.email}"}
            return {"message": "Hello anonymous"}
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
