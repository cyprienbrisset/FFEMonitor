"""
Client Supabase pour FFE Monitor.
Gère la connexion à Supabase pour l'authentification et la base de données.
"""

from typing import Optional
from supabase import create_client, Client
from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SupabaseClient:
    """Client singleton pour Supabase."""

    _instance: Optional["SupabaseClient"] = None
    _client: Optional[Client] = None
    _service_client: Optional[Client] = None

    def __new__(cls) -> "SupabaseClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None and settings.supabase_configured:
            self._initialize_clients()

    def _initialize_clients(self):
        """Initialise les clients Supabase."""
        try:
            # Client avec clé anonyme (pour les utilisateurs authentifiés)
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_anon_key
            )
            logger.info("Client Supabase (anon) initialisé")

            # Client avec clé service (pour le backend)
            self._service_client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
            logger.info("Client Supabase (service) initialisé")

        except Exception as e:
            logger.error(f"Erreur initialisation Supabase: {e}")
            raise

    @property
    def client(self) -> Optional[Client]:
        """Retourne le client Supabase avec clé anonyme."""
        return self._client

    @property
    def service_client(self) -> Optional[Client]:
        """Retourne le client Supabase avec clé service (backend only)."""
        return self._service_client

    async def get_user_from_token(self, token: str) -> Optional[dict]:
        """Récupère l'utilisateur à partir d'un JWT token."""
        if not self._client:
            return None

        try:
            response = self._client.auth.get_user(token)
            if response and response.user:
                return {
                    "id": str(response.user.id),
                    "email": response.user.email,
                    "created_at": str(response.user.created_at),
                }
            return None
        except Exception as e:
            logger.error(f"Erreur récupération utilisateur: {e}")
            return None

    async def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Récupère le profil utilisateur avec son plan."""
        if not self._service_client:
            return None

        try:
            response = (
                self._service_client.table("profiles")
                .select("*")
                .eq("id", user_id)
                .single()
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Erreur récupération profil: {e}")
            return None

    async def update_user_profile(self, user_id: str, data: dict) -> bool:
        """Met à jour le profil utilisateur."""
        if not self._service_client:
            return False

        try:
            self._service_client.table("profiles").update(data).eq(
                "id", user_id
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour profil: {e}")
            return False

    # ==================== Concours ====================

    async def get_concours(self, numero: int) -> Optional[dict]:
        """Récupère un concours par son numéro."""
        if not self._service_client:
            return None

        try:
            response = (
                self._service_client.table("concours")
                .select("*")
                .eq("numero", numero)
                .single()
                .execute()
            )
            return response.data
        except Exception:
            return None

    async def upsert_concours(self, concours_data: dict) -> bool:
        """Insère ou met à jour un concours."""
        if not self._service_client:
            return False

        try:
            self._service_client.table("concours").upsert(
                concours_data, on_conflict="numero"
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur upsert concours: {e}")
            return False

    async def get_all_concours(self) -> list:
        """Récupère tous les concours."""
        if not self._service_client:
            return []

        try:
            response = (
                self._service_client.table("concours").select("*").execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Erreur récupération concours: {e}")
            return []

    async def update_concours_status(
        self, numero: int, is_open: bool, statut: str
    ) -> bool:
        """Met à jour le statut d'un concours."""
        if not self._service_client:
            return False

        try:
            data = {"is_open": is_open, "statut": statut}
            if is_open:
                data["opened_at"] = "now()"

            self._service_client.table("concours").update(data).eq(
                "numero", numero
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour statut concours: {e}")
            return False

    # ==================== Subscriptions ====================

    async def get_user_subscriptions(self, user_id: str) -> list:
        """Récupère les abonnements d'un utilisateur."""
        if not self._service_client:
            return []

        try:
            response = (
                self._service_client.table("subscriptions")
                .select("*, concours(*)")
                .eq("user_id", user_id)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Erreur récupération abonnements: {e}")
            return []

    async def subscribe_to_concours(
        self, user_id: str, concours_numero: int
    ) -> bool:
        """Abonne un utilisateur à un concours."""
        if not self._service_client:
            return False

        try:
            self._service_client.table("subscriptions").insert(
                {"user_id": user_id, "concours_numero": concours_numero}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur abonnement: {e}")
            return False

    async def unsubscribe_from_concours(
        self, user_id: str, concours_numero: int
    ) -> bool:
        """Désabonne un utilisateur d'un concours."""
        if not self._service_client:
            return False

        try:
            self._service_client.table("subscriptions").delete().eq(
                "user_id", user_id
            ).eq("concours_numero", concours_numero).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur désabonnement: {e}")
            return False

    async def get_subscribers_for_concours(self, concours_numero: int) -> list:
        """Récupère tous les abonnés d'un concours avec leurs profils."""
        if not self._service_client:
            return []

        try:
            response = (
                self._service_client.table("subscriptions")
                .select("*, profiles(*)")
                .eq("concours_numero", concours_numero)
                .eq("notified", False)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Erreur récupération abonnés: {e}")
            return []

    # ==================== Notification Queue ====================

    async def queue_notification(
        self,
        user_id: str,
        concours_numero: int,
        plan: str,
        send_at: str,
    ) -> bool:
        """Ajoute une notification à la file d'attente."""
        if not self._service_client:
            return False

        try:
            self._service_client.table("notification_queue").insert(
                {
                    "user_id": user_id,
                    "concours_numero": concours_numero,
                    "plan": plan,
                    "send_at": send_at,
                }
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur queue notification: {e}")
            return False

    async def get_pending_notifications(self) -> list:
        """Récupère les notifications à envoyer."""
        if not self._service_client:
            return []

        try:
            response = (
                self._service_client.table("notification_queue")
                .select("*, profiles(*), concours(*)")
                .eq("sent", False)
                .lte("send_at", "now()")
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Erreur récupération notifications: {e}")
            return []

    async def mark_notification_sent(self, notification_id: str) -> bool:
        """Marque une notification comme envoyée."""
        if not self._service_client:
            return False

        try:
            self._service_client.table("notification_queue").update(
                {"sent": True, "sent_at": "now()"}
            ).eq("id", notification_id).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur marquage notification: {e}")
            return False

    async def log_notification(
        self,
        user_id: str,
        concours_numero: int,
        channel: str,
        plan: str,
        delay_seconds: int,
    ) -> bool:
        """Enregistre une notification dans l'historique."""
        if not self._service_client:
            return False

        try:
            self._service_client.table("notification_log").insert(
                {
                    "user_id": user_id,
                    "concours_numero": concours_numero,
                    "channel": channel,
                    "plan": plan,
                    "delay_seconds": delay_seconds,
                }
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur log notification: {e}")
            return False


# Instance globale
supabase = SupabaseClient()
