"""
Configuration de l'application Hoofs.
Chargement des variables d'environnement via pydantic-settings.
"""

from typing import Any

from pydantic import field_validator
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
    supabase_key: str = ""  # Alias pour supabase_anon_key
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""

    # OneSignal (push notifications)
    onesignal_app_id: str = ""
    onesignal_api_key: str = ""

    # Resend (email notifications)
    resend_api_key: str = ""
    resend_from_email: str = "Hoofs <notifications@hoofs.fr>"

    # Délais par plan (secondes)
    delay_free: int = 600      # 10 minutes
    delay_premium: int = 60    # 1 minute
    delay_pro: int = 10        # 10 secondes

    @field_validator("delay_free", "delay_premium", "delay_pro", "check_interval", mode="before")
    @classmethod
    def parse_int_or_default(cls, v: Any, info) -> int:
        """Parse les entiers, retourne la valeur par défaut si vide."""
        if v is None or v == "":
            defaults = {
                "delay_free": 600,
                "delay_premium": 60,
                "delay_pro": 10,
                "check_interval": 5,
            }
            return defaults.get(info.field_name, 0)
        return int(v)

    # Application
    check_interval: int = 5  # secondes
    log_level: str = "INFO"

    # URLs FFE (pour le scraper)
    ffe_base_url: str = "https://ffecompet.ffe.com"
    ffe_concours_url: str = "https://ffecompet.ffe.com/concours"

    @property
    def supabase_anon_key_resolved(self) -> str:
        """Retourne la clé anonyme (supabase_anon_key ou supabase_key)."""
        return self.supabase_anon_key or self.supabase_key

    @property
    def supabase_configured(self) -> bool:
        """Vérifie si Supabase est configuré (URL + clé anonyme minimum)."""
        return bool(self.supabase_url and self.supabase_anon_key_resolved)

    @property
    def supabase_fully_configured(self) -> bool:
        """Vérifie si Supabase est entièrement configuré (avec service_key et jwt_secret)."""
        return bool(
            self.supabase_url
            and self.supabase_anon_key_resolved
            and self.supabase_service_key
            and self.supabase_jwt_secret
        )

    @property
    def onesignal_configured(self) -> bool:
        """Vérifie si OneSignal est correctement configuré."""
        return bool(self.onesignal_app_id and self.onesignal_api_key)

    @property
    def resend_configured(self) -> bool:
        """Vérifie si Resend (email) est correctement configuré."""
        return bool(self.resend_api_key)

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
