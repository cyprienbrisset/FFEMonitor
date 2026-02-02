"""
Configuration de l'application EngageWatch.
Chargement des variables d'environnement via pydantic-settings.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration centralisée de l'application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignorer les variables non définies dans la classe
    )

    # Application Authentication
    auth_username: str = "admin"
    auth_password: str = "changeme"
    auth_secret_key: str = "change-this-secret-key-in-production"
    auth_token_expire_hours: int = 24

    # FFE Credentials
    ffe_username: str
    ffe_password: str

    # Telegram
    telegram_bot_token: str
    telegram_chat_id: str

    # Email via Resend (optionnel)
    email_enabled: bool = False
    resend_api_key: Optional[str] = None
    email_from: str = "FFE Monitor <onboarding@resend.dev>"
    email_to: Optional[str] = None

    # WhatsApp via Whapi.cloud (optionnel)
    whatsapp_enabled: bool = False
    whapi_api_key: Optional[str] = None
    whatsapp_to: Optional[str] = None  # Numéro au format international sans + (ex: 33612345678)

    # Application
    check_interval: int = 5  # secondes
    log_level: str = "INFO"

    # Paths
    database_path: str = "data/engagewatch.db"
    cookies_path: str = "data/cookies.json"

    # URLs FFE
    ffe_base_url: str = "https://ffecompet.ffe.com"
    ffe_login_url: str = "https://ffecompet.ffe.com/login"
    ffe_concours_url: str = "https://ffecompet.ffe.com/concours"

    @property
    def database_full_path(self) -> Path:
        """Retourne le chemin complet vers la base de données."""
        return Path(self.database_path)

    @property
    def cookies_full_path(self) -> Path:
        """Retourne le chemin complet vers le fichier cookies."""
        return Path(self.cookies_path)

    @property
    def email_configured(self) -> bool:
        """Vérifie si l'email via Resend est correctement configuré."""
        return (
            self.email_enabled
            and self.resend_api_key is not None
            and self.email_to is not None
        )

    @property
    def whatsapp_configured(self) -> bool:
        """Vérifie si WhatsApp via Whapi.cloud est correctement configuré."""
        return (
            self.whatsapp_enabled
            and self.whapi_api_key is not None
            and self.whatsapp_to is not None
        )


# Instance globale
settings = Settings()
