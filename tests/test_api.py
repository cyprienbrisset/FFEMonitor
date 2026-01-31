"""
Tests d'intégration pour l'API FastAPI.
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests pour l'endpoint /health."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """L'endpoint /health retourne le statut."""
        response = await async_client.get("/health")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "ffe_connected" in data
        assert "surveillance_active" in data
        assert "concours_count" in data


class TestConcoursEndpoints:
    """Tests pour les endpoints /concours."""

    @pytest.mark.asyncio
    async def test_list_concours_empty(self, async_client: AsyncClient):
        """Liste vide au démarrage."""
        response = await async_client.get("/concours")

        assert response.status_code == 200

        data = response.json()
        assert data["concours"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_add_concours_success(self, async_client: AsyncClient):
        """Ajout d'un concours réussi."""
        response = await async_client.post(
            "/concours",
            json={"numero": 123456}
        )

        assert response.status_code == 201

        data = response.json()
        assert data["numero"] == 123456
        assert data["statut"] == "ferme"
        assert data["notifie"] is False

    @pytest.mark.asyncio
    async def test_add_concours_duplicate(self, async_client: AsyncClient):
        """Ajout d'un concours en doublon échoue."""
        # Premier ajout
        await async_client.post("/concours", json={"numero": 123456})

        # Deuxième ajout
        response = await async_client.post(
            "/concours",
            json={"numero": 123456}
        )

        assert response.status_code == 409
        assert "déjà surveillé" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_add_concours_invalid_numero(self, async_client: AsyncClient):
        """Ajout avec numéro invalide échoue."""
        response = await async_client.post(
            "/concours",
            json={"numero": -1}
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_add_concours_missing_numero(self, async_client: AsyncClient):
        """Ajout sans numéro échoue."""
        response = await async_client.post(
            "/concours",
            json={}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_concours_found(self, async_client: AsyncClient):
        """Récupération d'un concours existant."""
        await async_client.post("/concours", json={"numero": 123456})

        response = await async_client.get("/concours/123456")

        assert response.status_code == 200

        data = response.json()
        assert data["numero"] == 123456

    @pytest.mark.asyncio
    async def test_get_concours_not_found(self, async_client: AsyncClient):
        """Récupération d'un concours inexistant."""
        response = await async_client.get("/concours/999999")

        assert response.status_code == 404
        assert "non trouvé" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_concours_success(self, async_client: AsyncClient):
        """Suppression d'un concours réussie."""
        await async_client.post("/concours", json={"numero": 123456})

        response = await async_client.delete("/concours/123456")

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "retiré" in data["message"]

        # Vérifier que le concours est supprimé
        response = await async_client.get("/concours/123456")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_concours_not_found(self, async_client: AsyncClient):
        """Suppression d'un concours inexistant."""
        response = await async_client.delete("/concours/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_concours_multiple(self, async_client: AsyncClient):
        """Liste plusieurs concours."""
        await async_client.post("/concours", json={"numero": 111111})
        await async_client.post("/concours", json={"numero": 222222})
        await async_client.post("/concours", json={"numero": 333333})

        response = await async_client.get("/concours")

        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 3
        assert len(data["concours"]) == 3

    @pytest.mark.asyncio
    async def test_status_endpoint(self, async_client: AsyncClient):
        """L'endpoint /concours/status/global retourne l'état."""
        await async_client.post("/concours", json={"numero": 123456})

        response = await async_client.get("/concours/status/global")

        assert response.status_code == 200

        data = response.json()
        assert "ffe_connected" in data
        assert "surveillance_active" in data
        assert data["concours_surveilles"] == 1
        assert data["concours_ouverts"] == 0


class TestAPIValidation:
    """Tests de validation des entrées API."""

    @pytest.mark.asyncio
    async def test_invalid_json(self, async_client: AsyncClient):
        """JSON invalide retourne une erreur."""
        response = await async_client.post(
            "/concours",
            content="not json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_wrong_content_type(self, async_client: AsyncClient):
        """Mauvais Content-Type retourne une erreur."""
        response = await async_client.post(
            "/concours",
            content="numero=123456",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_numero_zero(self, async_client: AsyncClient):
        """Numéro zéro est invalide."""
        response = await async_client.post(
            "/concours",
            json={"numero": 0}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_numero_string(self, async_client: AsyncClient):
        """Numéro en string est converti ou rejeté."""
        response = await async_client.post(
            "/concours",
            json={"numero": "abc"}
        )

        assert response.status_code == 422
