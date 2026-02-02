"""
Configuration de l'application FFE Monitor.
Chargement des variables d'environnement via pydantic-settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration centralisée de l'application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignorer les variables non définies dans la classe
    )

    # Supabase (obligatoire)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""

    # OneSignal (obligatoire)
    onesignal_app_id: str = ""
    onesignal_api_key: str = ""

    # Délais par plan (secondes)
    delay_free: int = 600      # 10 minutes
    delay_premium: int = 60    # 1 minute
    delay_pro: int = 10        # 10 secondes

    # Application
    check_interval: int = 5  # secondes
    log_level: str = "INFO"

    # Paths
    database_path: str = "data/ffemonitor.db"
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
    def supabase_configured(self) -> bool:
        """Vérifie si Supabase est correctement configuré."""
        return bool(
            self.supabase_url
            and self.supabase_anon_key
            and self.supabase_service_key
            and self.supabase_jwt_secret
        )

    @property
    def onesignal_configured(self) -> bool:
        """Vérifie si OneSignal est correctement configuré."""
        return bool(self.onesignal_app_id and self.onesignal_api_key)

    def get_delay_for_plan(self, plan: str) -> int:
        """Retourne le délai en secondes pour un plan donné."""
        delays = {
            "free": self.delay_free,
            "premium": self.delay_premium,
            "pro": self.delay_pro,
        }
        return delays.get(plan.lower(), self.delay_free)


# Instance globale
settings = Settings()
