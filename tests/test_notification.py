"""
Tests unitaires pour le service de notification Telegram.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from backend.services.notification import TelegramNotifier
from backend.models import StatutConcours


class TestTelegramNotifierInit:
    """Tests d'initialisation du notifier."""

    def test_init(self):
        """Initialisation correcte du notifier."""
        notifier = TelegramNotifier(
            bot_token="123:ABC",
            chat_id="456",
        )

        assert notifier.bot_token == "123:ABC"
        assert notifier.chat_id == "456"
        assert notifier._client is None


class TestMessageFormatting:
    """Tests de formatage des messages."""

    def test_format_message_engagement(self):
        """Formatage correct pour un concours engagement."""
        notifier = TelegramNotifier(
            bot_token="123:ABC",
            chat_id="456",
        )

        message = notifier._format_message(123456, StatutConcours.ENGAGEMENT)

        assert "123456" in message
        assert "ENGAGEMENT" in message
        assert "Engager" in message
        assert "ffecompet.ffe.com/concours/123456" in message
        assert "🟢" in message

    def test_format_message_demande(self):
        """Formatage correct pour un concours demande."""
        notifier = TelegramNotifier(
            bot_token="123:ABC",
            chat_id="456",
        )

        message = notifier._format_message(123456, StatutConcours.DEMANDE)

        assert "123456" in message
        assert "DEMANDE" in message
        assert "Demande de participation" in message
        assert "🔵" in message


class TestSendNotification:
    """Tests d'envoi de notifications."""

    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """Envoi de notification réussi."""
        notifier = TelegramNotifier(
            bot_token="123:ABC",
            chat_id="456",
        )

        # Mock du client HTTP
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(notifier, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await notifier.send_notification(
                123456, StatutConcours.ENGAGEMENT
            )

        assert result is True
        mock_client.post.assert_called_once()

        # Vérifier les arguments de l'appel
        call_args = mock_client.post.call_args
        assert "123:ABC" in call_args[0][0]  # URL contient le token
        assert call_args[1]["json"]["chat_id"] == "456"
        assert call_args[1]["json"]["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_send_notification_api_error(self):
        """Gestion d'une erreur API Telegram."""
        notifier = TelegramNotifier(
            bot_token="123:ABC",
            chat_id="456",
        )

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch.object(notifier, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await notifier.send_notification(
                123456, StatutConcours.ENGAGEMENT
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_notification_network_error(self):
        """Gestion d'une erreur réseau."""
        notifier = TelegramNotifier(
            bot_token="123:ABC",
            chat_id="456",
        )

        with patch.object(notifier, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.NetworkError("Connection failed"))
            mock_get_client.return_value = mock_client

            result = await notifier.send_notification(
                123456, StatutConcours.ENGAGEMENT
            )

        assert result is False


class TestStartupMessage:
    """Tests du message de démarrage."""

    @pytest.mark.asyncio
    async def test_send_startup_message_success(self):
        """Envoi du message de démarrage."""
        notifier = TelegramNotifier(
            bot_token="123:ABC",
            chat_id="456",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(notifier, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await notifier.send_startup_message()

        assert result is True

        # Vérifier le contenu du message
        call_args = mock_client.post.call_args
        message = call_args[1]["json"]["text"]
        assert "démarré" in message.lower() or "EngageWatch" in message


class TestErrorMessage:
    """Tests du message d'erreur."""

    @pytest.mark.asyncio
    async def test_send_error_message_success(self):
        """Envoi du message d'erreur."""
        notifier = TelegramNotifier(
            bot_token="123:ABC",
            chat_id="456",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(notifier, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await notifier.send_error_message("Test error")

        assert result is True

        call_args = mock_client.post.call_args
        message = call_args[1]["json"]["text"]
        assert "Test error" in message
        assert "Erreur" in message

    @pytest.mark.asyncio
    async def test_send_error_message_silently_fails(self):
        """Le message d'erreur ne propage pas les exceptions."""
        notifier = TelegramNotifier(
            bot_token="123:ABC",
            chat_id="456",
        )

        with patch.object(notifier, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("Network error"))
            mock_get_client.return_value = mock_client

            # Ne doit pas lever d'exception
            result = await notifier.send_error_message("Test error")

        assert result is False


class TestClientManagement:
    """Tests de gestion du client HTTP."""

    @pytest.mark.asyncio
    async def test_get_client_creates_once(self):
        """Le client est créé une seule fois."""
        notifier = TelegramNotifier(
            bot_token="123:ABC",
            chat_id="456",
        )

        client1 = await notifier._get_client()
        client2 = await notifier._get_client()

        assert client1 is client2
        assert notifier._client is not None

        # Cleanup
        await notifier.close()

    @pytest.mark.asyncio
    async def test_close_client(self):
        """La fermeture du client fonctionne."""
        notifier = TelegramNotifier(
            bot_token="123:ABC",
            chat_id="456",
        )

        # Créer le client
        await notifier._get_client()
        assert notifier._client is not None

        # Fermer
        await notifier.close()
        assert notifier._client is None

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """La fermeture sans client ne crash pas."""
        notifier = TelegramNotifier(
            bot_token="123:ABC",
            chat_id="456",
        )

        # Ne doit pas lever d'exception
        await notifier.close()
