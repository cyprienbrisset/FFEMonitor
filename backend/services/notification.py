"""
Service de notification pour Hoofs.
Utilise OneSignal pour les push notifications et Resend pour les emails.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import httpx

from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger("notification")


class SupabaseEmailNotifier:
    """
    Gestionnaire d'emails via Supabase Edge Function.
    Les emails sont envoyés par une fonction Supabase qui utilise Resend.
    """

    def __init__(self, supabase_url: str, service_key: str):
        """
        Initialise le notifier Supabase Email.

        Args:
            supabase_url: URL du projet Supabase
            service_key: Clé service Supabase pour authentifier les appels
        """
        self.function_url = f"{supabase_url}/functions/v1/send-email"
        self.service_key = service_key
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Retourne le client HTTP, le crée si nécessaire."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Envoie un email via Supabase Edge Function.

        Args:
            to_email: Adresse email du destinataire
            subject: Sujet de l'email
            html_content: Contenu HTML de l'email
            text_content: Contenu texte alternatif (optionnel)

        Returns:
            True si envoi réussi, False sinon
        """
        try:
            client = await self._get_client()

            payload = {
                "to": to_email,
                "subject": subject,
                "html": html_content,
            }

            if text_content:
                payload["text"] = text_content

            response = await client.post(
                self.function_url,
                headers={
                    "Authorization": f"Bearer {self.service_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"Email envoyé à {to_email} via Supabase")
                    return True
                else:
                    logger.error(f"Erreur Supabase email: {result.get('error')}")
                    return False
            else:
                logger.error(
                    f"Erreur Supabase Edge Function ({response.status_code}): {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Erreur envoi email Supabase: {e}")
            return False

    async def send_concours_notification(
        self,
        to_email: str,
        numero: int,
        statut: str,
        nom: str | None = None,
        lieu: str | None = None,
        date_debut: str | None = None,
        date_fin: str | None = None,
    ) -> bool:
        """
        Envoie une notification d'ouverture de concours par email.
        Utilise le template intégré dans la Edge Function.

        Args:
            to_email: Email du destinataire
            numero: Numéro du concours
            statut: Type d'ouverture (engagement, demande, etc.)
            nom: Nom du concours
            lieu: Lieu du concours
            date_debut: Date de début
            date_fin: Date de fin

        Returns:
            True si envoi réussi, False sinon
        """
        try:
            client = await self._get_client()

            payload = {
                "to": to_email,
                "type": "concours",
                "concours": {
                    "numero": numero,
                    "statut": statut,
                    "nom": nom,
                    "lieu": lieu,
                    "date_debut": date_debut,
                    "date_fin": date_fin,
                },
            }

            response = await client.post(
                self.function_url,
                headers={
                    "Authorization": f"Bearer {self.service_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"Email concours {numero} envoyé à {to_email}")
                    return True
                else:
                    logger.error(f"Erreur email concours: {result.get('error')}")
                    return False
            else:
                logger.error(
                    f"Erreur Supabase ({response.status_code}): {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Erreur envoi email concours: {e}")
            return False

    async def send_test_notification(self, to_email: str) -> bool:
        """Envoie un email de test via Supabase Edge Function."""
        try:
            client = await self._get_client()

            payload = {
                "to": to_email,
                "type": "test",
            }

            response = await client.post(
                self.function_url,
                headers={
                    "Authorization": f"Bearer {self.service_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"Email de test envoyé à {to_email}")
                    return True
                else:
                    logger.error(f"Erreur email test: {result.get('error')}")
                    return False
            else:
                logger.error(
                    f"Erreur Supabase ({response.status_code}): {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Erreur envoi email test: {e}")
            return False

    async def close(self) -> None:
        """Ferme le client HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None


class OneSignalNotifier:
    """
    Gestionnaire de notifications push via OneSignal.
    Envoie des push notifications aux utilisateurs de la PWA.
    """

    ONESIGNAL_API_URL = "https://onesignal.com/api/v1/notifications"

    def __init__(self, app_id: str, api_key: str):
        """
        Initialise le notifier OneSignal.

        Args:
            app_id: ID de l'application OneSignal
            api_key: Clé API REST OneSignal
        """
        self.app_id = app_id
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Retourne le client HTTP, le crée si nécessaire."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def send_to_player(
        self,
        player_id: str,
        title: str,
        message: str,
        url: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> bool:
        """
        Envoie une notification push à un player_id spécifique.

        Args:
            player_id: ID du player OneSignal
            title: Titre de la notification
            message: Corps du message
            url: URL à ouvrir au clic (optionnel)
            data: Données additionnelles (optionnel)

        Returns:
            True si envoi réussi, False sinon
        """
        try:
            client = await self._get_client()

            payload = {
                "app_id": self.app_id,
                "include_player_ids": [player_id],
                "headings": {"en": title, "fr": title},
                "contents": {"en": message, "fr": message},
            }

            if url:
                payload["url"] = url

            if data:
                payload["data"] = data

            response = await client.post(
                self.ONESIGNAL_API_URL,
                headers={
                    "Authorization": f"Basic {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("recipients", 0) > 0:
                    logger.info(f"Push OneSignal envoyé à {player_id}")
                    return True
                else:
                    logger.warning(f"Push OneSignal: aucun destinataire pour {player_id}")
                    return False
            else:
                logger.error(
                    f"Erreur OneSignal ({response.status_code}): {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Erreur envoi push OneSignal: {e}")
            return False

    async def send_to_all(
        self,
        title: str,
        message: str,
        url: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> bool:
        """
        Envoie une notification push à tous les utilisateurs.

        Args:
            title: Titre de la notification
            message: Corps du message
            url: URL à ouvrir au clic (optionnel)
            data: Données additionnelles (optionnel)

        Returns:
            True si envoi réussi, False sinon
        """
        try:
            client = await self._get_client()

            payload = {
                "app_id": self.app_id,
                "included_segments": ["All"],
                "headings": {"en": title, "fr": title},
                "contents": {"en": message, "fr": message},
            }

            if url:
                payload["url"] = url

            if data:
                payload["data"] = data

            response = await client.post(
                self.ONESIGNAL_API_URL,
                headers={
                    "Authorization": f"Basic {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                recipients = result.get("recipients", 0)
                logger.info(f"Push OneSignal envoyé à {recipients} utilisateurs")
                return recipients > 0
            else:
                logger.error(
                    f"Erreur OneSignal ({response.status_code}): {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Erreur envoi push OneSignal: {e}")
            return False

    async def send_concours_notification(
        self,
        player_id: str,
        numero: int,
        statut: str,
        nom: str | None = None,
        lieu: str | None = None,
        date_debut: str | None = None,
        date_fin: str | None = None,
    ) -> bool:
        """
        Envoie une notification d'ouverture de concours par push.

        Args:
            player_id: ID du player OneSignal
            numero: Numéro du concours
            statut: Type d'ouverture (engagement, demande, etc.)
            nom: Nom du concours
            lieu: Lieu du concours
            date_debut: Date de début
            date_fin: Date de fin

        Returns:
            True si envoi réussi, False sinon
        """
        # Déterminer le type d'ouverture
        if statut == "engagement":
            emoji = "🟢"
            type_ouverture = "Engagement ouvert"
        elif statut == "demande":
            emoji = "🔵"
            type_ouverture = "Demandes ouvertes"
        else:
            emoji = "🔔"
            type_ouverture = "Concours mis à jour"

        titre = nom if nom else f"Concours #{numero}"
        title = f"{emoji} {type_ouverture}"
        message = f"{titre}"
        if lieu:
            message += f" - {lieu}"

        url = f"{settings.ffe_concours_url}/{numero}"

        return await self.send_to_player(
            player_id=player_id,
            title=title,
            message=message,
            url=url,
            data={"concours_numero": numero, "statut": statut},
        )

    async def send_startup_notification(self) -> bool:
        """Envoie une notification de démarrage à tous les utilisateurs."""
        return await self.send_to_all(
            title="🐴 Hoofs",
            message="Surveillance active - Vous serez notifié à l'ouverture des concours",
            url="/app",
        )

    async def send_test_notification(self, player_id: str) -> bool:
        """Envoie une notification de test."""
        return await self.send_to_player(
            player_id=player_id,
            title="🐴 Hoofs - Test",
            message="Les notifications push fonctionnent correctement !",
            url="/app",
        )

    async def close(self) -> None:
        """Ferme le client HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None


class NotificationDispatcher:
    """
    Dispatcher de notifications multi-utilisateurs.
    Gère la file d'attente des notifications avec délais différenciés par plan.
    Supporte les push (OneSignal) et les emails (Resend).
    """

    def __init__(self):
        """Initialise le dispatcher."""
        self.onesignal: Optional[OneSignalNotifier] = None
        self.email: Optional[SupabaseEmailNotifier] = None
        self._running = False

        # Initialiser OneSignal si configuré
        if settings.onesignal_configured:
            self.onesignal = OneSignalNotifier(
                app_id=settings.onesignal_app_id,
                api_key=settings.onesignal_api_key,
            )
            logger.info("OneSignal dispatcher initialisé")
        else:
            logger.warning("OneSignal non configuré - push notifications désactivées")

        # Initialiser Supabase Email si configuré
        if settings.supabase_fully_configured:
            self.email = SupabaseEmailNotifier(
                supabase_url=settings.supabase_url,
                service_key=settings.supabase_service_key,
            )
            logger.info("Supabase email dispatcher initialisé")
        else:
            logger.warning("Supabase non entièrement configuré - email notifications désactivées")

    async def queue_notifications_for_concours(
        self, concours_numero: int, opened_at: datetime
    ) -> int:
        """
        Crée les notifications en file d'attente pour tous les abonnés d'un concours.

        Args:
            concours_numero: Numéro du concours
            opened_at: Timestamp d'ouverture

        Returns:
            Nombre de notifications mises en file
        """
        from backend.supabase_client import supabase

        # Récupérer tous les abonnés non notifiés
        subscribers = await supabase.get_subscribers_for_concours(concours_numero)

        if not subscribers:
            logger.info(f"Aucun abonné à notifier pour concours {concours_numero}")
            return 0

        count = 0
        for sub in subscribers:
            profile = sub.get("profiles", {})
            if not profile:
                continue

            user_id = profile.get("id")
            plan = profile.get("plan", "free")
            delay = settings.get_delay_for_plan(plan)

            # Calculer le moment d'envoi
            send_at = opened_at + timedelta(seconds=delay)

            # Ajouter à la file
            success = await supabase.queue_notification(
                user_id=user_id,
                concours_numero=concours_numero,
                plan=plan,
                send_at=send_at.isoformat(),
            )

            if success:
                count += 1
                logger.debug(
                    f"Notification planifiée pour {user_id} (plan={plan}, "
                    f"délai={delay}s, envoi={send_at})"
                )

        logger.info(
            f"{count} notifications planifiées pour concours {concours_numero}"
        )
        return count

    async def process_pending_notifications(self) -> int:
        """
        Traite les notifications en attente dont l'heure d'envoi est passée.
        Envoie via push (OneSignal) et/ou email (Resend) selon les préférences.

        Returns:
            Nombre de notifications envoyées
        """
        if not self.onesignal and not self.email:
            return 0

        from backend.supabase_client import supabase

        # Récupérer les notifications à envoyer
        pending = await supabase.get_pending_notifications()

        if not pending:
            return 0

        sent_count = 0
        for notif in pending:
            profile = notif.get("profiles", {})
            concours = notif.get("concours", {})

            if not profile or not concours:
                # Marquer comme envoyée même si invalide
                await supabase.mark_notification_sent(notif.get("id"))
                continue

            user_id = profile.get("id")
            user_email = profile.get("email")
            plan = profile.get("plan", "free")
            player_id = profile.get("onesignal_player_id")
            delay = settings.get_delay_for_plan(plan)

            notification_sent = False

            # Envoyer via OneSignal si player_id disponible et push activé
            if self.onesignal and player_id and profile.get("notification_push", True):
                success = await self.onesignal.send_concours_notification(
                    player_id=player_id,
                    numero=concours.get("numero"),
                    statut=concours.get("statut", "ferme"),
                    nom=concours.get("nom"),
                    lieu=concours.get("lieu"),
                    date_debut=concours.get("date_debut"),
                    date_fin=concours.get("date_fin"),
                )

                if success:
                    await supabase.log_notification(
                        user_id=user_id,
                        concours_numero=concours.get("numero"),
                        channel="push",
                        plan=plan,
                        delay_seconds=delay,
                    )
                    notification_sent = True

            # Envoyer via email si email activé
            if self.email and user_email and profile.get("notification_email", False):
                success = await self.email.send_concours_notification(
                    to_email=user_email,
                    numero=concours.get("numero"),
                    statut=concours.get("statut", "ferme"),
                    nom=concours.get("nom"),
                    lieu=concours.get("lieu"),
                    date_debut=concours.get("date_debut"),
                    date_fin=concours.get("date_fin"),
                )

                if success:
                    await supabase.log_notification(
                        user_id=user_id,
                        concours_numero=concours.get("numero"),
                        channel="email",
                        plan=plan,
                        delay_seconds=delay,
                    )
                    notification_sent = True

            if notification_sent:
                sent_count += 1

            # Marquer comme envoyée
            await supabase.mark_notification_sent(notif.get("id"))

        if sent_count > 0:
            logger.info(f"{sent_count} notifications envoyées")

        return sent_count

    async def start_worker(self, interval: float = 1.0):
        """
        Démarre le worker de traitement des notifications.

        Args:
            interval: Intervalle entre chaque vérification en secondes
        """
        self._running = True
        logger.info("Worker de notifications démarré")

        while self._running:
            try:
                await self.process_pending_notifications()
            except Exception as e:
                logger.error(f"Erreur worker notifications: {e}")

            await asyncio.sleep(interval)

    def stop_worker(self):
        """Arrête le worker de notifications."""
        self._running = False
        logger.info("Worker de notifications arrêté")

    async def close(self):
        """Ferme les ressources."""
        self.stop_worker()
        if self.onesignal:
            await self.onesignal.close()
        if self.email:
            await self.email.close()


# Instance globale du dispatcher
notification_dispatcher: Optional[NotificationDispatcher] = None


def get_notification_dispatcher() -> NotificationDispatcher:
    """Retourne l'instance globale du dispatcher de notifications."""
    global notification_dispatcher
    if notification_dispatcher is None:
        notification_dispatcher = NotificationDispatcher()
    return notification_dispatcher
