"""
Routes d'authentification pour EngageWatch.
Gestion du login et des tokens JWT.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt

from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger("auth")

router = APIRouter(tags=["auth"])

# Configuration JWT
ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)


# ============================================================================
# Modèles Pydantic
# ============================================================================


class LoginRequest(BaseModel):
    """Requête de connexion."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Réponse de connexion."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # secondes


class AuthConfigResponse(BaseModel):
    """Configuration Supabase pour l'authentification."""
    supabase_url: str
    supabase_anon_key: str


class UserInfo(BaseModel):
    """Informations utilisateur."""
    username: str
    authenticated: bool = True


# ============================================================================
# Fonctions utilitaires
# ============================================================================


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT.

    Args:
        data: Données à encoder dans le token
        expires_delta: Durée de validité du token

    Returns:
        Token JWT encodé
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.auth_token_expire_hours)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.auth_secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    Vérifie un token JWT.

    Args:
        token: Token JWT à vérifier

    Returns:
        Username si valide, None sinon
    """
    try:
        payload = jwt.decode(token, settings.auth_secret_key, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """
    Dépendance pour obtenir l'utilisateur courant.

    Args:
        credentials: Credentials HTTP Bearer

    Returns:
        Username si authentifié, None sinon
    """
    if credentials is None:
        return None

    token = credentials.credentials
    username = verify_token(token)
    return username


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    Dépendance qui exige une authentification.

    Args:
        credentials: Credentials HTTP Bearer

    Returns:
        Username de l'utilisateur authentifié

    Raises:
        HTTPException: Si non authentifié
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    username = verify_token(token)

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return username


# ============================================================================
# Routes
# ============================================================================


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authentifie un utilisateur et retourne un token JWT.

    Args:
        request: Identifiants de connexion

    Returns:
        Token JWT et informations de session
    """
    # Debug logging
    logger.debug(f"Tentative de connexion - Username reçu: '{request.username}'")
    logger.debug(f"Username attendu: '{settings.auth_username}'")

    # Vérifier les identifiants
    if (
        request.username != settings.auth_username
        or request.password != settings.auth_password
    ):
        logger.warning(f"Tentative de connexion échouée pour: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
        )

    # Créer le token
    expires_delta = timedelta(hours=settings.auth_token_expire_hours)
    access_token = create_access_token(
        data={"sub": request.username},
        expires_delta=expires_delta,
    )

    logger.info(f"Connexion réussie pour: {request.username}")

    return LoginResponse(
        access_token=access_token,
        expires_in=int(expires_delta.total_seconds()),
    )


@router.get("/auth/verify", response_model=UserInfo)
async def verify_auth(username: str = Depends(require_auth)):
    """
    Vérifie si le token est valide.

    Args:
        username: Username extrait du token

    Returns:
        Informations utilisateur
    """
    return UserInfo(username=username)


@router.post("/auth/logout")
async def logout():
    """
    Déconnecte l'utilisateur.

    Note: Avec JWT, la déconnexion se fait côté client
    en supprimant le token. Cette route existe pour la cohérence.

    Returns:
        Message de confirmation
    """
    return {"message": "Déconnexion réussie"}


@router.get("/auth/config", response_model=AuthConfigResponse)
async def get_auth_config():
    """
    Retourne la configuration Supabase pour l'authentification.
    Utilisé par l'extension Chrome pour se connecter.

    Returns:
        URL et clé anonyme Supabase
    """
    return AuthConfigResponse(
        supabase_url=settings.supabase_url,
        supabase_anon_key=settings.supabase_anon_key,
    )
