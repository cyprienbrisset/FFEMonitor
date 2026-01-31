"""
Configuration pytest et fixtures partagées pour les tests EngageWatch.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Configurer les variables d'environnement AVANT d'importer les modules
os.environ["FFE_USERNAME"] = "test@example.com"
os.environ["FFE_PASSWORD"] = "testpassword"
os.environ["TELEGRAM_BOT_TOKEN"] = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
os.environ["TELEGRAM_CHAT_ID"] = "987654321"
os.environ["CHECK_INTERVAL"] = "1"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture(scope="session")
def event_loop():
    """Crée une boucle d'événements pour toute la session de tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Crée un chemin temporaire pour la base de données de test."""
    return tmp_path / "test_engagewatch.db"


@pytest.fixture
def temp_cookies_path(tmp_path: Path) -> Path:
    """Crée un chemin temporaire pour les cookies de test."""
    return tmp_path / "test_cookies.json"


@pytest_asyncio.fixture
async def test_database(temp_db_path: Path):
    """Crée une base de données de test."""
    from backend.database import Database

    db = Database(db_path=temp_db_path)
    await db.connect()
    yield db
    await db.disconnect()


@pytest.fixture
def mock_authenticator():
    """Crée un mock de FFEAuthenticator."""
    mock = AsyncMock()
    mock.is_connected = True
    mock.login = AsyncMock(return_value=True)
    mock.close = AsyncMock()
    mock.navigate_to_concours = AsyncMock()

    # Mock de la page Playwright
    mock_page = AsyncMock()
    mock_page.url = "https://ffecompet.ffe.com/concours/123456"
    mock_page.locator = MagicMock()
    mock.navigate_to_concours.return_value = mock_page

    return mock


@pytest.fixture
def mock_notifier():
    """Crée un mock de TelegramNotifier."""
    mock = AsyncMock()
    mock.send_notification = AsyncMock(return_value=True)
    mock.send_startup_message = AsyncMock(return_value=True)
    mock.send_error_message = AsyncMock(return_value=True)
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_page_ferme():
    """Mock d'une page de concours fermé."""
    mock_page = AsyncMock()
    mock_page.url = "https://ffecompet.ffe.com/concours/123456"

    # Le locator retourne 0 pour tous les boutons
    mock_locator = AsyncMock()
    mock_locator.count = AsyncMock(return_value=0)
    mock_page.locator = MagicMock(return_value=mock_locator)

    return mock_page


@pytest.fixture
def mock_page_engagement():
    """Mock d'une page de concours avec bouton Engager."""
    mock_page = AsyncMock()
    mock_page.url = "https://ffecompet.ffe.com/concours/123456"

    def locator_side_effect(selector):
        mock_locator = AsyncMock()
        if "Engager" in selector:
            mock_locator.count = AsyncMock(return_value=1)
        else:
            mock_locator.count = AsyncMock(return_value=0)
        return mock_locator

    mock_page.locator = MagicMock(side_effect=locator_side_effect)
    return mock_page


@pytest.fixture
def mock_page_demande():
    """Mock d'une page de concours avec bouton Demande."""
    mock_page = AsyncMock()
    mock_page.url = "https://ffecompet.ffe.com/concours/123456"

    def locator_side_effect(selector):
        mock_locator = AsyncMock()
        if "Demande" in selector or "participation" in selector:
            mock_locator.count = AsyncMock(return_value=1)
        else:
            mock_locator.count = AsyncMock(return_value=0)
        return mock_locator

    mock_page.locator = MagicMock(side_effect=locator_side_effect)
    return mock_page


@pytest_asyncio.fixture
async def test_app(temp_db_path: Path, mock_authenticator, mock_notifier):
    """Crée une application FastAPI de test avec mocks."""
    from backend.main import app, app_state
    from backend.database import Database

    # Créer une nouvelle DB de test connectée
    test_db = Database(db_path=temp_db_path)
    await test_db.connect()

    # Configurer l'état de l'application
    app_state["ffe_connected"] = True
    app_state["surveillance_active"] = True
    app_state["concours_count"] = 0
    app_state["authenticator"] = mock_authenticator

    # Remplacer la base de données globale
    from backend import database
    from backend.routers import concours as concours_router
    original_db = database.db
    database.db = test_db
    concours_router.db = test_db

    yield app

    # Restaurer
    database.db = original_db
    concours_router.db = original_db
    await test_db.disconnect()


@pytest_asyncio.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Crée un client HTTP async pour tester l'API."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_client(test_app) -> Generator[TestClient, None, None]:
    """Crée un client HTTP sync pour tester l'API."""
    with TestClient(test_app) as client:
        yield client
