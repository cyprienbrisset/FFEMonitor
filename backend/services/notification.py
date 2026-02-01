"""
Service de notification pour EngageWatch.
Supporte Telegram et Email (via Resend) pour envoyer des alertes lors de l'ouverture des concours.
"""

from typing import Optional, Protocol

import httpx

from backend.config import settings
from backend.models import StatutConcours
from backend.utils.logger import get_logger

logger = get_logger("notification")


class Notifier(Protocol):
    """Interface commune pour tous les notifiers."""

    async def send_notification(self, numero: int, statut: StatutConcours) -> bool:
        """Envoie une notification d'ouverture de concours."""
        ...

    async def send_startup_message(self) -> bool:
        """Envoie un message de démarrage."""
        ...

    async def send_error_message(self, error: str) -> bool:
        """Envoie un message d'erreur."""
        ...

    async def close(self) -> None:
        """Ferme les ressources."""
        ...


class TelegramNotifier:
    """
    Gestionnaire de notifications Telegram.

    Envoie des messages formatés via l'API Telegram Bot.
    """

    TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialise le notifier Telegram.

        Args:
            bot_token: Token du bot Telegram
            chat_id: ID du chat/utilisateur à notifier
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Retourne le client HTTP, le crée si nécessaire."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def send_notification(
        self,
        numero: int,
        statut: StatutConcours,
    ) -> bool:
        """
        Envoie une notification d'ouverture de concours.

        Args:
            numero: Numéro du concours
            statut: Type d'ouverture (engagement ou demande)

        Returns:
            True si envoi réussi, False sinon
        """
        message = self._format_message(numero, statut)

        try:
            client = await self._get_client()
            url = self.TELEGRAM_API_URL.format(token=self.bot_token)

            response = await client.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
            )

            if response.status_code == 200:
                logger.info(f"Notification Telegram envoyée pour concours {numero}")
                return True
            else:
                logger.error(
                    f"Erreur Telegram ({response.status_code}): {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Erreur envoi notification Telegram: {e}")
            return False

    def _format_message(self, numero: int, statut: StatutConcours) -> str:
        """
        Formate le message de notification.

        Args:
            numero: Numéro du concours
            statut: Type d'ouverture

        Returns:
            Message formaté en HTML
        """
        # Déterminer l'emoji et le type
        if statut == StatutConcours.ENGAGEMENT:
            emoji = "🟢"
            type_ouverture = "ENGAGEMENT"
            action = "Engager"
        else:  # DEMANDE
            emoji = "🔵"
            type_ouverture = "DEMANDE DE PARTICIPATION"
            action = "Demande de participation"

        url = f"{settings.ffe_concours_url}/{numero}"

        message = f"""
{emoji} <b>CONCOURS OUVERT !</b> {emoji}

━━━━━━━━━━━━━━━━━━━━

📋 <b>Concours n°{numero}</b>

🎯 <b>Type :</b> {type_ouverture}

🔘 <b>Action :</b> Bouton "{action}" disponible

━━━━━━━━━━━━━━━━━━━━

👉 <a href="{url}">Accéder au concours</a>

⚡️ <i>Notification EngageWatch</i>
"""
        return message.strip()

    async def send_startup_message(self) -> bool:
        """
        Envoie un message de démarrage.

        Returns:
            True si envoi réussi, False sinon
        """
        message = """
🚀 <b>EngageWatch démarré</b>

La surveillance des concours FFE est active.

Vous recevrez une notification dès qu'un concours surveillé s'ouvrira aux engagements.

<i>Interface : http://localhost:8000</i>
"""

        try:
            client = await self._get_client()
            url = self.TELEGRAM_API_URL.format(token=self.bot_token)

            response = await client.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": message.strip(),
                    "parse_mode": "HTML",
                },
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Erreur envoi message démarrage Telegram: {e}")
            return False

    async def send_error_message(self, error: str) -> bool:
        """
        Envoie un message d'erreur.

        Args:
            error: Description de l'erreur

        Returns:
            True si envoi réussi, False sinon
        """
        message = f"""
⚠️ <b>Erreur EngageWatch</b>

{error}

<i>Vérifiez l'application.</i>
"""

        try:
            client = await self._get_client()
            url = self.TELEGRAM_API_URL.format(token=self.bot_token)

            response = await client.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": message.strip(),
                    "parse_mode": "HTML",
                },
            )

            return response.status_code == 200

        except Exception:
            return False

    async def send_test(self) -> bool:
        """
        Envoie un message de test.

        Returns:
            True si envoi réussi, False sinon
        """
        message = """
🧪 <b>Test Notification</b>

Ceci est un message de test EngageWatch.

Si vous recevez ce message, les notifications Telegram fonctionnent correctement !
"""

        try:
            client = await self._get_client()
            url = self.TELEGRAM_API_URL.format(token=self.bot_token)

            response = await client.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": message.strip(),
                    "parse_mode": "HTML",
                },
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Erreur envoi test Telegram: {e}")
            return False

    async def close(self) -> None:
        """Ferme le client HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None


class ResendNotifier:
    """
    Gestionnaire de notifications par email via Resend.

    Envoie des emails formatés via l'API Resend.
    """

    RESEND_API_URL = "https://api.resend.com/emails"

    def __init__(
        self,
        api_key: str,
        from_email: str,
        to_email: str,
    ):
        """
        Initialise le notifier Resend.

        Args:
            api_key: Clé API Resend
            from_email: Adresse email expéditeur
            to_email: Adresse email destinataire
        """
        self.api_key = api_key
        self.from_email = from_email
        self.to_email = to_email
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Retourne le client HTTP, le crée si nécessaire."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def _send_email(self, subject: str, html_body: str) -> bool:
        """
        Envoie un email via l'API Resend.

        Args:
            subject: Sujet de l'email
            html_body: Corps de l'email en HTML

        Returns:
            True si envoi réussi, False sinon
        """
        try:
            client = await self._get_client()

            response = await client.post(
                self.RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": self.from_email,
                    "to": [self.to_email],
                    "subject": subject,
                    "html": html_body,
                },
            )

            if response.status_code == 200:
                logger.info(f"Email Resend envoyé avec succès à {self.to_email}")
                return True
            else:
                logger.error(
                    f"Erreur Resend ({response.status_code}): {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Erreur envoi email Resend: {e}")
            return False

    async def send_notification(
        self,
        numero: int,
        statut: StatutConcours,
    ) -> bool:
        """
        Envoie une notification d'ouverture de concours par email.

        Args:
            numero: Numéro du concours
            statut: Type d'ouverture (engagement ou demande)

        Returns:
            True si envoi réussi, False sinon
        """
        subject, html_body = self._format_notification(numero, statut)

        result = await self._send_email(subject, html_body)
        if result:
            logger.info(f"Notification email Resend envoyée pour concours {numero}")
        return result

    def _format_notification(
        self, numero: int, statut: StatutConcours
    ) -> tuple[str, str]:
        """
        Formate la notification pour l'email.

        Args:
            numero: Numéro du concours
            statut: Type d'ouverture

        Returns:
            Tuple (sujet, html)
        """
        if statut == StatutConcours.ENGAGEMENT:
            type_ouverture = "Engagement"
            emoji_code = "🟢"
            color = "#4A7C59"
        else:
            type_ouverture = "Demande de participation"
            emoji_code = "🔵"
            color = "#3D6B99"

        url = f"{settings.ffe_concours_url}/{numero}"

        subject = f"{emoji_code} Concours {numero} ouvert - {type_ouverture}"

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #1A1A1A;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
        <tr>
            <td>
                <!-- Header -->
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: linear-gradient(135deg, #722F37, #5A252C); border-radius: 16px 16px 0 0; padding: 30px;">
                    <tr>
                        <td align="center">
                            <h1 style="color: #F5F0E8; margin: 0; font-size: 28px; font-weight: 600;">
                                {emoji_code} Concours Ouvert !
                            </h1>
                        </td>
                    </tr>
                </table>

                <!-- Content -->
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #2D2D2D; padding: 30px;">
                    <tr>
                        <td>
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: rgba(0,0,0,0.2); border-radius: 12px; padding: 24px; border-left: 4px solid {color};">
                                <tr>
                                    <td>
                                        <p style="color: rgba(245,240,232,0.6); font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 8px 0;">
                                            Numéro du concours
                                        </p>
                                        <p style="color: #F5F0E8; font-size: 32px; font-weight: 700; margin: 0;">
                                            #{numero}
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top: 20px;">
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid rgba(245,240,232,0.1);">
                                        <span style="color: rgba(245,240,232,0.6); font-size: 14px;">Type d'ouverture</span>
                                        <span style="color: {color}; font-size: 14px; font-weight: 600; float: right;">{type_ouverture}</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0;">
                                        <span style="color: rgba(245,240,232,0.6); font-size: 14px;">Action disponible</span>
                                        <span style="color: #F5F0E8; font-size: 14px; float: right;">Bouton "{type_ouverture}" visible</span>
                                    </td>
                                </tr>
                            </table>

                            <!-- CTA Button -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top: 30px;">
                                <tr>
                                    <td align="center">
                                        <a href="{url}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #E5C76B, #C9A227); color: #1A1A1A; text-decoration: none; font-weight: 600; font-size: 16px; border-radius: 8px;">
                                            Accéder au concours →
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>

                <!-- Footer -->
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #1A1A1A; border-radius: 0 0 16px 16px; padding: 20px;">
                    <tr>
                        <td align="center">
                            <p style="color: rgba(245,240,232,0.4); font-size: 12px; margin: 0;">
                                EngageWatch — Surveillance Premium des Concours FFE
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        return subject, html_body

    async def send_startup_message(self) -> bool:
        """
        Envoie un message de démarrage par email.

        Returns:
            True si envoi réussi, False sinon
        """
        subject = "🚀 EngageWatch démarré"

        html_body = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #1A1A1A;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
        <tr>
            <td>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: linear-gradient(135deg, #2D4A3E, #3D5F50); border-radius: 16px; padding: 40px;">
                    <tr>
                        <td align="center">
                            <h1 style="color: #F5F0E8; margin: 0 0 20px 0; font-size: 24px;">
                                🚀 EngageWatch démarré
                            </h1>
                            <p style="color: rgba(245,240,232,0.8); font-size: 16px; line-height: 1.6; margin: 0;">
                                La surveillance des concours FFE est maintenant active.<br><br>
                                Vous recevrez une notification dès qu'un concours surveillé s'ouvrira aux engagements.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        return await self._send_email(subject, html_body)

    async def send_error_message(self, error: str) -> bool:
        """
        Envoie un message d'erreur par email.

        Args:
            error: Description de l'erreur

        Returns:
            True si envoi réussi, False sinon
        """
        subject = "⚠️ Erreur EngageWatch"

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #1A1A1A;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
        <tr>
            <td>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: linear-gradient(135deg, #A63D40, #8B3A44); border-radius: 16px; padding: 40px;">
                    <tr>
                        <td align="center">
                            <h1 style="color: #F5F0E8; margin: 0 0 20px 0; font-size: 24px;">
                                ⚠️ Erreur EngageWatch
                            </h1>
                            <p style="color: rgba(245,240,232,0.9); font-size: 16px; line-height: 1.6; margin: 0; background: rgba(0,0,0,0.2); padding: 20px; border-radius: 8px;">
                                {error}
                            </p>
                            <p style="color: rgba(245,240,232,0.5); font-size: 14px; margin-top: 20px;">
                                Vérifiez l'application.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        return await self._send_email(subject, html_body)

    async def send_test(self) -> bool:
        """
        Envoie un email de test.

        Returns:
            True si envoi réussi, False sinon
        """
        subject = "🧪 Test EngageWatch"

        html_body = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #1A1A1A;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
        <tr>
            <td>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: linear-gradient(135deg, #C9A227, #B8922A); border-radius: 16px; padding: 40px;">
                    <tr>
                        <td align="center">
                            <h1 style="color: #1A1A1A; margin: 0 0 20px 0; font-size: 24px;">
                                🧪 Test Notification
                            </h1>
                            <p style="color: rgba(26,26,26,0.8); font-size: 16px; line-height: 1.6; margin: 0;">
                                Ceci est un email de test EngageWatch.<br><br>
                                Si vous recevez cet email, les notifications par email fonctionnent correctement !
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        return await self._send_email(subject, html_body)

    async def close(self) -> None:
        """Ferme le client HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None


class MultiNotifier:
    """
    Gestionnaire multi-canal de notifications.

    Envoie les notifications via tous les canaux configurés (Telegram, Email).
    """

    def __init__(self):
        """Initialise le notifier multi-canal."""
        self.notifiers: list[Notifier] = []

        # Ajouter Telegram (toujours actif)
        self.telegram = TelegramNotifier(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
        )
        self.notifiers.append(self.telegram)
        logger.info("Notifier Telegram initialisé")

        # Ajouter Email via Resend si configuré
        self.email: Optional[ResendNotifier] = None
        if settings.email_configured:
            self.email = ResendNotifier(
                api_key=settings.resend_api_key,
                from_email=settings.email_from,
                to_email=settings.email_to,
            )
            self.notifiers.append(self.email)
            logger.info("Notifier Email (Resend) initialisé")
        else:
            logger.info("Notifier Email désactivé (non configuré)")

    async def send_notification(
        self,
        numero: int,
        statut: StatutConcours,
    ) -> bool:
        """
        Envoie une notification via tous les canaux.

        Args:
            numero: Numéro du concours
            statut: Type d'ouverture

        Returns:
            True si au moins un canal a réussi, False sinon
        """
        results = []
        for notifier in self.notifiers:
            try:
                result = await notifier.send_notification(numero, statut)
                results.append(result)
            except Exception as e:
                logger.error(f"Erreur notifier {type(notifier).__name__}: {e}")
                results.append(False)

        return any(results)

    async def send_startup_message(self) -> bool:
        """
        Envoie un message de démarrage via tous les canaux.

        Returns:
            True si au moins un canal a réussi, False sinon
        """
        results = []
        for notifier in self.notifiers:
            try:
                result = await notifier.send_startup_message()
                results.append(result)
            except Exception as e:
                logger.error(f"Erreur démarrage {type(notifier).__name__}: {e}")
                results.append(False)

        return any(results)

    async def send_error_message(self, error: str) -> bool:
        """
        Envoie un message d'erreur via tous les canaux.

        Args:
            error: Description de l'erreur

        Returns:
            True si au moins un canal a réussi, False sinon
        """
        results = []
        for notifier in self.notifiers:
            try:
                result = await notifier.send_error_message(error)
                results.append(result)
            except Exception as e:
                logger.error(f"Erreur message erreur {type(notifier).__name__}: {e}")
                results.append(False)

        return any(results)

    async def close(self) -> None:
        """Ferme tous les notifiers."""
        for notifier in self.notifiers:
            try:
                await notifier.close()
            except Exception as e:
                logger.error(f"Erreur fermeture {type(notifier).__name__}: {e}")
