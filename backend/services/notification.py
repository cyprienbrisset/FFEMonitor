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


class ResendEmailNotifier:
    """
    Gestionnaire d'emails via l'API Resend directement.
    """

    RESEND_API_URL = "https://api.resend.com/emails"

    def __init__(self, api_key: str, from_email: str):
        """
        Initialise le notifier Resend.

        Args:
            api_key: Clé API Resend
            from_email: Adresse email d'expédition (ex: "Hoofs <hoofs@brisset.me>")
        """
        self.api_key = api_key
        self.from_email = from_email
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
        Envoie un email via l'API Resend.

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
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }

            if text_content:
                payload["text"] = text_content

            response = await client.post(
                self.RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Email envoyé à {to_email} via Resend (id: {result.get('id')})")
                return True
            else:
                logger.error(
                    f"Erreur Resend ({response.status_code}): {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Erreur envoi email Resend: {e}")
            return False

    def _generate_concours_email(
        self,
        numero: int,
        statut: str,
        nom: str | None = None,
        lieu: str | None = None,
        date_debut: str | None = None,
        date_fin: str | None = None,
    ) -> tuple[str, str, str]:
        """Génère le contenu de l'email pour une notification de concours."""
        # Déterminer le type d'ouverture
        emoji = "🔔"
        type_ouverture = "Concours mis à jour"
        color = "#C4A35A"

        if statut == "engagement":
            emoji = "🟢"
            type_ouverture = "Engagements ouverts"
            color = "#6B9B7A"
        elif statut == "demande":
            emoji = "🔵"
            type_ouverture = "Demandes ouvertes"
            color = "#7090C0"

        titre = nom or f"Concours #{numero}"
        url = f"https://ffecompet.ffe.com/concours/{numero}"

        subject = f"{emoji} {type_ouverture} — {titre}"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #FAF7F2;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #FAF7F2; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="100%" style="max-width: 500px;" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 24px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {color}20, {color}40); padding: 32px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 8px;">{emoji}</div>
                            <h1 style="margin: 0; font-size: 24px; color: #2D2D2D; font-weight: 600;">{type_ouverture}</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px; background-color: #FFFFFF;">
                            <h2 style="margin: 0 0 16px 0; font-size: 20px; color: #2D2D2D;">{titre}</h2>
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                                <tr>
                                    <td style="padding: 8px 0; color: #8B8B8B; font-size: 14px;">Numéro</td>
                                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; text-align: right; font-weight: 500;">#{numero}</td>
                                </tr>
                                {f'<tr><td style="padding: 8px 0; color: #8B8B8B; font-size: 14px;">Lieu</td><td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; text-align: right;">{lieu}</td></tr>' if lieu else ""}
                                {f'<tr><td style="padding: 8px 0; color: #8B8B8B; font-size: 14px;">Date</td><td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; text-align: right;">{date_debut}{f" - {date_fin}" if date_fin else ""}</td></tr>' if date_debut else ""}
                            </table>
                            <a href="{url}" style="display: block; width: 100%; padding: 16px; background-color: #2D2D2D; color: #FFFFFF; text-decoration: none; border-radius: 100px; text-align: center; font-weight: 600; font-size: 16px; box-sizing: border-box;">
                                Accéder au concours →
                            </a>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 32px; background-color: #FAF7F2; text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #8B8B8B;">
                                🐴 Hoofs — Surveillance des concours FFE
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

        text = f"""
{type_ouverture} — {titre}

Numéro: #{numero}
{f"Lieu: {lieu}" if lieu else ""}
{f"Date: {date_debut}{f' - {date_fin}' if date_fin else ''}" if date_debut else ""}

Accéder au concours: {url}

---
🐴 Hoofs — Surveillance des concours FFE
"""

        return subject, html, text

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
        subject, html, text = self._generate_concours_email(
            numero=numero,
            statut=statut,
            nom=nom,
            lieu=lieu,
            date_debut=date_debut,
            date_fin=date_fin,
        )

        success = await self.send_email(to_email, subject, html, text)
        if success:
            logger.info(f"Email concours {numero} envoyé à {to_email}")
        return success

    async def send_test_notification(self, to_email: str) -> tuple[bool, str]:
        """Envoie un email de test."""
        subject = "🐴 Hoofs — Test des notifications email"

        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #FAF7F2;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #FAF7F2; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="100%" style="max-width: 500px;" cellpadding="0" cellspacing="0">
                    <tr>
                        <td style="background: linear-gradient(135deg, #D4E4D120, #D4E4D140); padding: 32px; text-align: center; border-radius: 24px 24px 0 0; background-color: #FFFFFF;">
                            <div style="font-size: 48px; margin-bottom: 8px;">🐴</div>
                            <h1 style="margin: 0; font-size: 24px; color: #2D2D2D; font-weight: 600;">Test réussi !</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 32px; text-align: center; background-color: #FFFFFF;">
                            <p style="margin: 0 0 24px 0; font-size: 16px; color: #4A4A4A; line-height: 1.6;">
                                Les notifications email fonctionnent correctement.<br>
                                Vous recevrez un email à chaque ouverture de concours surveillé.
                            </p>
                            <div style="display: inline-block; padding: 12px 24px; background-color: #D4E4D1; color: #6B9B7A; border-radius: 100px; font-weight: 600; font-size: 14px;">
                                ✓ Configuration validée
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 24px 32px; background-color: #FAF7F2; text-align: center; border-radius: 0 0 24px 24px;">
                            <p style="margin: 0; font-size: 12px; color: #8B8B8B;">
                                🐴 Hoofs — Surveillance des concours FFE
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

        text = "Test réussi ! Les notifications email fonctionnent correctement."

        try:
            logger.info(f"Envoi email test à {to_email} via Resend")
            success = await self.send_email(to_email, subject, html, text)
            if success:
                return True, f"Email envoyé à {to_email}"
            else:
                return False, "Échec de l'envoi via Resend"
        except Exception as e:
            logger.error(f"Erreur envoi email test: {e}")
            return False, str(e)

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

    ONESIGNAL_API_URL = "https://api.onesignal.com/notifications"

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
    ) -> tuple[bool, str]:
        """
        Envoie une notification push à un player_id spécifique.

        Args:
            player_id: ID du player OneSignal
            title: Titre de la notification
            message: Corps du message
            url: URL à ouvrir au clic (optionnel)
            data: Données additionnelles (optionnel)

        Returns:
            Tuple (success, detail_message)
        """
        try:
            client = await self._get_client()

            payload = {
                "app_id": self.app_id,
                "include_subscription_ids": [player_id],
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
                    "Authorization": f"Key {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("recipients", 0) > 0:
                    logger.info(f"Push OneSignal envoyé à {player_id}")
                    return True, "Notification envoyée"
                else:
                    # OneSignal accepted the request but found no valid subscription
                    errors = result.get("errors", {})
                    invalid = errors.get("invalid_subscription_ids", [])
                    logger.warning(
                        f"Push OneSignal: aucun destinataire pour {player_id} "
                        f"(invalid_ids: {invalid}, full response: {result})"
                    )
                    if invalid:
                        return False, (
                            f"L'ID de souscription ({player_id[:12]}...) n'est plus valide sur OneSignal. "
                            "L'abonnement push a peut-être expiré ou été révoqué. "
                            "Essayez de désactiver puis réactiver les notifications."
                        )
                    return False, (
                        f"OneSignal n'a trouvé aucun destinataire pour cet ID ({player_id[:12]}...). "
                        "Essayez de recharger la page et réactiver les notifications."
                    )
            else:
                error_body = response.text
                logger.error(
                    f"Erreur OneSignal ({response.status_code}): {error_body}"
                )
                return False, f"Erreur OneSignal (HTTP {response.status_code}): {error_body[:200]}"

        except Exception as e:
            logger.error(f"Erreur envoi push OneSignal: {e}")
            return False, f"Erreur réseau: {str(e)}"

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
                    "Authorization": f"Key {self.api_key}",
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

        success, _ = await self.send_to_player(
            player_id=player_id,
            title=title,
            message=message,
            url=url,
            data={"concours_numero": numero, "statut": statut},
        )
        return success

    async def send_startup_notification(self) -> bool:
        """Envoie une notification de démarrage à tous les utilisateurs."""
        return await self.send_to_all(
            title="🐴 Hoofs",
            message="Surveillance active - Vous serez notifié à l'ouverture des concours",
            url="/app",
        )

    async def send_test_notification(self, player_id: str) -> tuple[bool, str]:
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
        self.email: Optional[ResendEmailNotifier] = None
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

        # Initialiser Resend Email si configuré
        if settings.resend_configured:
            self.email = ResendEmailNotifier(
                api_key=settings.resend_api_key,
                from_email=settings.resend_from_email,
            )
            logger.info("Resend email dispatcher initialisé")
        else:
            logger.warning("Resend non configuré (RESEND_API_KEY manquant) - email notifications désactivées")

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
