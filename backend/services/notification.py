"""
Service de notification pour EngageWatch.
Supporte Telegram et Email pour envoyer des alertes lors de l'ouverture des concours.
"""

import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Protocol

import httpx
import aiosmtplib

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

    async def close(self) -> None:
        """Ferme le client HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None


class EmailNotifier:
    """
    Gestionnaire de notifications par email.

    Envoie des emails formatés via SMTP.
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        from_email: str,
        to_email: str,
        use_tls: bool = True,
    ):
        """
        Initialise le notifier Email.

        Args:
            smtp_host: Serveur SMTP
            smtp_port: Port SMTP
            smtp_username: Nom d'utilisateur SMTP
            smtp_password: Mot de passe SMTP
            from_email: Adresse email expéditeur
            to_email: Adresse email destinataire
            use_tls: Utiliser TLS (STARTTLS)
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.to_email = to_email
        self.use_tls = use_tls

    async def _send_email(self, subject: str, html_body: str, text_body: str) -> bool:
        """
        Envoie un email via SMTP.

        Args:
            subject: Sujet de l'email
            html_body: Corps de l'email en HTML
            text_body: Corps de l'email en texte brut

        Returns:
            True si envoi réussi, False sinon
        """
        try:
            # Créer le message multipart
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = self.to_email

            # Ajouter les versions texte et HTML
            part_text = MIMEText(text_body, "plain", "utf-8")
            part_html = MIMEText(html_body, "html", "utf-8")
            message.attach(part_text)
            message.attach(part_html)

            # Configurer TLS
            tls_context = ssl.create_default_context() if self.use_tls else None

            # Envoyer l'email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=self.use_tls,
                tls_context=tls_context,
            )

            logger.info(f"Email envoyé avec succès à {self.to_email}")
            return True

        except aiosmtplib.SMTPException as e:
            logger.error(f"Erreur SMTP lors de l'envoi: {e}")
            return False
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
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
        subject, html_body, text_body = self._format_notification(numero, statut)

        result = await self._send_email(subject, html_body, text_body)
        if result:
            logger.info(f"Notification email envoyée pour concours {numero}")
        return result

    def _format_notification(
        self, numero: int, statut: StatutConcours
    ) -> tuple[str, str, str]:
        """
        Formate la notification pour l'email.

        Args:
            numero: Numéro du concours
            statut: Type d'ouverture

        Returns:
            Tuple (sujet, html, texte)
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

        text_body = f"""
CONCOURS OUVERT !

Numéro du concours : #{numero}
Type d'ouverture : {type_ouverture}
Action disponible : Bouton "{type_ouverture}" visible

Accéder au concours : {url}

---
EngageWatch - Surveillance Premium des Concours FFE
"""

        return subject, html_body, text_body

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
                            <p style="color: rgba(245,240,232,0.5); font-size: 14px; margin-top: 30px;">
                                Interface : <a href="http://localhost:8000" style="color: #C9A227;">http://localhost:8000</a>
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

        text_body = """
EngageWatch démarré

La surveillance des concours FFE est active.

Vous recevrez une notification dès qu'un concours surveillé s'ouvrira aux engagements.

Interface : http://localhost:8000
"""

        return await self._send_email(subject, html_body, text_body)

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

        text_body = f"""
Erreur EngageWatch

{error}

Vérifiez l'application.
"""

        return await self._send_email(subject, html_body, text_body)

    async def close(self) -> None:
        """Ferme les ressources (rien à faire pour l'email)."""
        pass


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

        # Ajouter Email si configuré
        self.email: Optional[EmailNotifier] = None
        if settings.email_configured:
            self.email = EmailNotifier(
                smtp_host=settings.email_smtp_host,
                smtp_port=settings.email_smtp_port,
                smtp_username=settings.email_smtp_username,
                smtp_password=settings.email_smtp_password,
                from_email=settings.email_from,
                to_email=settings.email_to,
                use_tls=settings.email_smtp_use_tls,
            )
            self.notifiers.append(self.email)
            logger.info("Notifier Email initialisé")
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
