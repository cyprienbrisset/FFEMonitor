"""
Client Supabase pour Hoofs.
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
            anon_key = settings.supabase_anon_key_resolved
            if not anon_key:
                logger.error("Aucune clé Supabase anon/key disponible!")
                return

            self._client = create_client(
                settings.supabase_url,
                anon_key
            )
            logger.info(f"Client Supabase (anon) initialisé - URL: {settings.supabase_url[:50]}...")

            # Client avec clé service (pour le backend)
            if settings.supabase_service_key:
                self._service_client = create_client(
                    settings.supabase_url,
                    settings.supabase_service_key
                )
                logger.info("Client Supabase (service) initialisé")
            else:
                logger.warning("SUPABASE_SERVICE_KEY non configurée - utilisation du client anon")
                self._service_client = self._client

        except Exception as e:
            logger.error(f"Erreur initialisation Supabase: {e}", exc_info=True)
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
        # Essayer d'abord avec le service client (plus fiable)
        client = self._service_client or self._client
        if not client:
            logger.error("Aucun client Supabase disponible")
            return None

        try:
            # Utiliser auth.get_user() avec le token d'accès
            response = client.auth.get_user(token)
            if response and response.user:
                logger.debug(f"Token validé pour user: {response.user.email}")
                return {
                    "id": str(response.user.id),
                    "email": response.user.email,
                    "created_at": str(response.user.created_at),
                }
            logger.warning("get_user() n'a pas retourné d'utilisateur")
            return None
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erreur validation token: {error_msg}")
            # Log plus de détails pour le debug
            if "invalid" in error_msg.lower() or "expired" in error_msg.lower():
                logger.debug(f"Token rejeté (premiers 50 chars): {token[:50]}...")
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
                .maybe_single()  # Utiliser maybe_single pour éviter l'erreur si 0 résultats
                .execute()
            )
            return response.data
        except Exception as e:
            logger.debug(f"Profil non trouvé pour {user_id}: {e}")
            return None

    async def create_user_profile(self, user_id: str, email: str) -> Optional[dict]:
        """Crée un nouveau profil utilisateur."""
        if not self._service_client:
            return None

        try:
            response = (
                self._service_client.table("profiles")
                .insert({
                    "id": user_id,
                    "email": email,
                    "plan": "free",
                })
                .execute()
            )
            if response.data:
                logger.info(f"Profil créé pour {email}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Erreur création profil pour {user_id}: {e}")
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
            logger.error("upsert_concours: service_client non disponible")
            return False

        try:
            logger.debug(f"upsert_concours: données = {concours_data}")
            response = self._service_client.table("concours").upsert(
                concours_data, on_conflict="numero"
            ).execute()
            logger.debug(f"upsert_concours: réponse = {response}")
            return True
        except Exception as e:
            logger.error(f"Erreur upsert concours: {e}", exc_info=True)
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

    async def update_concours(self, numero: int, data: dict) -> bool:
        """Met à jour un concours avec les données fournies."""
        if not self._service_client:
            return False

        try:
            self._service_client.table("concours").update(data).eq(
                "numero", numero
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour concours: {e}")
            return False

    async def delete_concours(self, numero: int) -> bool:
        """Supprime un concours."""
        if not self._service_client:
            return False

        try:
            self._service_client.table("concours").delete().eq(
                "numero", numero
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur suppression concours: {e}")
            return False

    async def get_concours_non_notifies(self) -> list:
        """Récupère les concours non encore notifiés (is_open = false)."""
        if not self._service_client:
            return []

        try:
            response = (
                self._service_client.table("concours")
                .select("*")
                .eq("is_open", False)
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Erreur récupération concours non notifiés: {e}")
            return []

    async def get_concours_by_date_range(self, start_date: str, end_date: str) -> list:
        """Récupère les concours dans une plage de dates."""
        if not self._service_client:
            return []

        try:
            response = (
                self._service_client.table("concours")
                .select("*")
                .gte("date_debut", start_date)
                .lte("date_debut", end_date)
                .order("date_debut")
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Erreur récupération concours par date: {e}")
            return []

    # ==================== Statistics ====================

    async def record_check(
        self,
        concours_numero: int,
        statut_before: str | None,
        statut_after: str | None,
        response_time_ms: int,
        success: bool = True,
    ) -> bool:
        """Enregistre une vérification dans l'historique."""
        if not self._service_client:
            return False

        try:
            self._service_client.table("check_history").insert({
                "concours_numero": concours_numero,
                "statut_before": statut_before,
                "statut_after": statut_after,
                "response_time_ms": response_time_ms,
                "success": success,
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur enregistrement check: {e}")
            return False

    async def record_opening(
        self,
        concours_numero: int,
        statut: str,
        notification_sent_at: str | None = None,
    ) -> bool:
        """Enregistre un événement d'ouverture."""
        if not self._service_client:
            return False

        try:
            self._service_client.table("opening_events").insert({
                "concours_numero": concours_numero,
                "statut": statut,
                "notification_sent_at": notification_sent_at,
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Erreur enregistrement ouverture: {e}")
            return False

    async def get_global_stats(self) -> dict:
        """Récupère les statistiques globales."""
        if not self._service_client:
            return {}

        try:
            # Total concours
            concours = await self.get_all_concours()
            total_concours = len(concours)
            concours_ouverts = sum(1 for c in concours if c.get("statut") != "ferme")

            # Total checks
            check_response = self._service_client.table("check_history").select("id", count="exact").execute()
            total_checks = check_response.count or 0

            # Total openings
            opening_response = self._service_client.table("opening_events").select("id", count="exact").execute()
            total_openings = opening_response.count or 0

            return {
                "total_concours": total_concours,
                "concours_ouverts": concours_ouverts,
                "total_checks": total_checks,
                "total_openings": total_openings,
            }
        except Exception as e:
            logger.error(f"Erreur récupération stats: {e}")
            return {}

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
