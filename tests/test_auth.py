"""
Tests unitaires pour le service d'authentification FFE.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.auth import FFEAuthenticator


class TestFFEAuthenticatorInit:
    """Tests d'initialisation de l'authentificateur."""

    def test_init(self, tmp_path: Path):
        """Initialisation correcte de l'authentificateur."""
        cookies_path = tmp_path / "cookies.json"

        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=cookies_path,
        )

        assert auth.username == "test@example.com"
        assert auth.password == "testpass"
        assert auth.cookies_path == cookies_path
        assert auth.headless is True
        assert auth.is_connected is False

    def test_init_headless_false(self, tmp_path: Path):
        """Initialisation avec headless=False."""
        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=tmp_path / "cookies.json",
            headless=False,
        )

        assert auth.headless is False


class TestCookieManagement:
    """Tests de gestion des cookies."""

    @pytest.mark.asyncio
    async def test_load_cookies_file_not_exists(self, tmp_path: Path):
        """Chargement échoue si fichier n'existe pas."""
        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=tmp_path / "nonexistent.json",
        )

        # Mock du contexte
        auth._context = AsyncMock()

        result = await auth._load_cookies()

        assert result is False
        auth._context.add_cookies.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_cookies_success(self, tmp_path: Path):
        """Chargement réussi des cookies."""
        cookies_path = tmp_path / "cookies.json"
        cookies_data = [
            {"name": "session", "value": "abc123", "domain": ".ffe.com"}
        ]
        cookies_path.write_text(json.dumps(cookies_data))

        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=cookies_path,
        )

        # Mock du contexte
        auth._context = AsyncMock()

        result = await auth._load_cookies()

        assert result is True
        auth._context.add_cookies.assert_called_once_with(cookies_data)

    @pytest.mark.asyncio
    async def test_load_cookies_invalid_json(self, tmp_path: Path):
        """Chargement échoue si JSON invalide."""
        cookies_path = tmp_path / "cookies.json"
        cookies_path.write_text("not valid json")

        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=cookies_path,
        )

        auth._context = AsyncMock()

        result = await auth._load_cookies()

        assert result is False

    @pytest.mark.asyncio
    async def test_save_cookies(self, tmp_path: Path):
        """Sauvegarde des cookies."""
        cookies_path = tmp_path / "cookies.json"
        cookies_data = [
            {"name": "session", "value": "abc123", "domain": ".ffe.com"}
        ]

        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=cookies_path,
        )

        # Mock du contexte
        auth._context = AsyncMock()
        auth._context.cookies = AsyncMock(return_value=cookies_data)

        await auth._save_cookies()

        assert cookies_path.exists()
        saved_data = json.loads(cookies_path.read_text())
        assert saved_data == cookies_data


class TestSessionValidation:
    """Tests de validation de session."""

    @pytest.mark.asyncio
    async def test_is_session_valid_redirected_to_login(self, tmp_path: Path):
        """Session invalide si redirigé vers login."""
        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=tmp_path / "cookies.json",
        )

        # Mock de la page
        auth._page = AsyncMock()
        auth._page.goto = AsyncMock()
        auth._page.url = "https://ffecompet.ffe.com/login"
        auth._page.locator = MagicMock(return_value=AsyncMock(count=AsyncMock(return_value=0)))

        result = await auth._is_session_valid()

        assert result is False

    @pytest.mark.asyncio
    async def test_is_session_valid_logged_in(self, tmp_path: Path):
        """Session valide si indicateur de connexion présent."""
        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=tmp_path / "cookies.json",
        )

        # Mock de la page
        auth._page = AsyncMock()
        auth._page.goto = AsyncMock()
        auth._page.url = "https://ffecompet.ffe.com/concours"

        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=1)
        auth._page.locator = MagicMock(return_value=mock_locator)

        result = await auth._is_session_valid()

        assert result is True

    @pytest.mark.asyncio
    async def test_is_session_valid_error(self, tmp_path: Path):
        """Session invalide en cas d'erreur."""
        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=tmp_path / "cookies.json",
        )

        auth._page = AsyncMock()
        auth._page.goto = AsyncMock(side_effect=Exception("Network error"))

        result = await auth._is_session_valid()

        assert result is False


class TestLogin:
    """Tests de connexion."""

    @pytest.mark.asyncio
    async def test_perform_login_success(self, tmp_path: Path):
        """Connexion réussie."""
        cookies_path = tmp_path / "cookies.json"

        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=cookies_path,
        )

        # Mock complet
        auth._page = AsyncMock()
        auth._page.goto = AsyncMock()
        auth._page.wait_for_selector = AsyncMock()
        auth._page.fill = AsyncMock()
        auth._page.click = AsyncMock()
        auth._page.wait_for_load_state = AsyncMock()
        auth._page.url = "https://ffecompet.ffe.com/dashboard"

        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=0)
        auth._page.locator = MagicMock(return_value=mock_locator)

        auth._context = AsyncMock()
        auth._context.cookies = AsyncMock(return_value=[])

        result = await auth._perform_login()

        assert result is True
        assert auth.is_connected is True

    @pytest.mark.asyncio
    async def test_perform_login_wrong_credentials(self, tmp_path: Path):
        """Connexion échouée avec mauvais identifiants."""
        auth = FFEAuthenticator(
            username="test@example.com",
            password="wrongpass",
            cookies_path=tmp_path / "cookies.json",
        )

        auth._page = AsyncMock()
        auth._page.goto = AsyncMock()
        auth._page.wait_for_selector = AsyncMock()
        auth._page.fill = AsyncMock()
        auth._page.click = AsyncMock()
        auth._page.wait_for_load_state = AsyncMock()
        auth._page.url = "https://ffecompet.ffe.com/login"  # Toujours sur login

        # Simuler un message d'erreur
        mock_error_locator = AsyncMock()
        mock_error_locator.count = AsyncMock(return_value=1)
        mock_error_locator.first = AsyncMock()
        mock_error_locator.first.text_content = AsyncMock(return_value="Identifiants incorrects")

        auth._page.locator = MagicMock(return_value=mock_error_locator)

        result = await auth._perform_login()

        assert result is False
        assert auth.is_connected is False


class TestNavigation:
    """Tests de navigation."""

    @pytest.mark.asyncio
    async def test_navigate_to_concours_success(self, tmp_path: Path):
        """Navigation réussie vers un concours."""
        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=tmp_path / "cookies.json",
        )

        auth._connected = True
        auth._page = AsyncMock()
        auth._page.goto = AsyncMock()
        auth._page.url = "https://ffecompet.ffe.com/concours/123456"

        page = await auth.navigate_to_concours(123456)

        assert page is auth._page
        auth._page.goto.assert_called_once()

    @pytest.mark.asyncio
    async def test_navigate_to_concours_not_connected(self, tmp_path: Path):
        """Navigation échoue si non connecté."""
        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=tmp_path / "cookies.json",
        )

        auth._connected = False

        with pytest.raises(RuntimeError, match="Non connecté"):
            await auth.navigate_to_concours(123456)

    @pytest.mark.asyncio
    async def test_navigate_to_concours_session_expired_reconnect_success(
        self, tmp_path: Path
    ):
        """Reconnexion automatique si session expirée."""
        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=tmp_path / "cookies.json",
        )

        auth._connected = True
        auth._page = AsyncMock()

        # Premier goto -> redirigé vers login
        # Deuxième goto (après reconnexion) -> succès
        call_count = [0]

        async def goto_side_effect(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                auth._page.url = "https://ffecompet.ffe.com/login"
            else:
                auth._page.url = "https://ffecompet.ffe.com/concours/123456"

        auth._page.goto = AsyncMock(side_effect=goto_side_effect)

        # Mock reconnect
        auth.reconnect = AsyncMock(return_value=True)

        page = await auth.navigate_to_concours(123456)

        assert page is auth._page
        auth.reconnect.assert_called_once()


class TestClose:
    """Tests de fermeture."""

    @pytest.mark.asyncio
    async def test_close(self, tmp_path: Path):
        """Fermeture propre du navigateur."""
        auth = FFEAuthenticator(
            username="test@example.com",
            password="testpass",
            cookies_path=tmp_path / "cookies.json",
        )

        # Mock des composants - garder des références pour vérifier après close()
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright = MagicMock()
        mock_playwright.stop = AsyncMock()

        auth._page = mock_page
        auth._context = mock_context
        auth._browser = mock_browser
        auth._playwright = mock_playwright
        auth._connected = True

        await auth.close()

        # Vérifier que les méthodes close/stop ont été appelées
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()

        # Vérifier que les attributs sont mis à None
        assert auth._page is None
        assert auth._context is None
        assert auth._browser is None
        assert auth._playwright is None
        assert auth.is_connected is False
