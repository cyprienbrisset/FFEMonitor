"""
Tests unitaires pour le module database.
"""

import pytest
import pytest_asyncio
from datetime import datetime
from pathlib import Path

from backend.database import Database
from backend.models import StatutConcours


class TestDatabaseConnection:
    """Tests de connexion à la base de données."""

    @pytest.mark.asyncio
    async def test_connect_creates_file(self, tmp_path: Path):
        """La connexion crée le fichier de base de données."""
        db_path = tmp_path / "new_db.db"
        db = Database(db_path=db_path)

        await db.connect()

        assert db_path.exists()
        await db.disconnect()

    @pytest.mark.asyncio
    async def test_connect_creates_table(self, tmp_path: Path):
        """La connexion crée la table concours."""
        db_path = tmp_path / "test.db"
        db = Database(db_path=db_path)

        await db.connect()

        # Vérifier que la table existe
        cursor = await db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='concours'"
        )
        result = await cursor.fetchone()

        assert result is not None
        assert result[0] == "concours"

        await db.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect(self, test_database):
        """La déconnexion ferme proprement la connexion."""
        # test_database est déjà connectée via la fixture
        assert test_database._connection is not None

        await test_database.disconnect()

        assert test_database._connection is None


class TestConcoursCRUD:
    """Tests CRUD pour les concours."""

    @pytest.mark.asyncio
    async def test_add_concours_success(self, test_database):
        """Ajouter un concours fonctionne."""
        result = await test_database.add_concours(123456)

        assert result is not None
        assert result["numero"] == 123456
        assert result["statut"] == "ferme"
        assert result["notifie"] is False

    @pytest.mark.asyncio
    async def test_add_concours_duplicate(self, test_database):
        """Ajouter un concours en doublon retourne None."""
        await test_database.add_concours(123456)

        result = await test_database.add_concours(123456)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_concours_by_numero_found(self, test_database):
        """Récupérer un concours existant fonctionne."""
        await test_database.add_concours(123456)

        result = await test_database.get_concours_by_numero(123456)

        assert result is not None
        assert result["numero"] == 123456

    @pytest.mark.asyncio
    async def test_get_concours_by_numero_not_found(self, test_database):
        """Récupérer un concours inexistant retourne None."""
        result = await test_database.get_concours_by_numero(999999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_concours_empty(self, test_database):
        """Liste vide si aucun concours."""
        result = await test_database.get_all_concours()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_concours_multiple(self, test_database):
        """Liste tous les concours ajoutés."""
        await test_database.add_concours(111111)
        await test_database.add_concours(222222)
        await test_database.add_concours(333333)

        result = await test_database.get_all_concours()

        assert len(result) == 3
        numeros = [c["numero"] for c in result]
        assert 111111 in numeros
        assert 222222 in numeros
        assert 333333 in numeros

    @pytest.mark.asyncio
    async def test_get_concours_non_notifies(self, test_database):
        """Ne retourne que les concours non notifiés."""
        await test_database.add_concours(111111)
        await test_database.add_concours(222222)

        # Marquer le premier comme notifié
        await test_database.update_statut(
            111111, StatutConcours.ENGAGEMENT, notifie=True
        )

        result = await test_database.get_concours_non_notifies()

        assert len(result) == 1
        assert result[0]["numero"] == 222222

    @pytest.mark.asyncio
    async def test_update_statut_engagement(self, test_database):
        """Mise à jour du statut vers engagement."""
        await test_database.add_concours(123456)

        success = await test_database.update_statut(
            123456, StatutConcours.ENGAGEMENT, notifie=True
        )

        assert success is True

        concours = await test_database.get_concours_by_numero(123456)
        assert concours["statut"] == "engagement"
        assert concours["notifie"] is True
        assert concours["last_check"] is not None

    @pytest.mark.asyncio
    async def test_update_statut_demande(self, test_database):
        """Mise à jour du statut vers demande."""
        await test_database.add_concours(123456)

        success = await test_database.update_statut(
            123456, StatutConcours.DEMANDE, notifie=False
        )

        assert success is True

        concours = await test_database.get_concours_by_numero(123456)
        assert concours["statut"] == "demande"
        assert concours["notifie"] is False

    @pytest.mark.asyncio
    async def test_update_statut_not_found(self, test_database):
        """Mise à jour d'un concours inexistant retourne False."""
        success = await test_database.update_statut(
            999999, StatutConcours.ENGAGEMENT
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_update_last_check(self, test_database):
        """Mise à jour du timestamp de dernière vérification."""
        await test_database.add_concours(123456)

        success = await test_database.update_last_check(123456)

        assert success is True

        concours = await test_database.get_concours_by_numero(123456)
        assert concours["last_check"] is not None

    @pytest.mark.asyncio
    async def test_delete_concours_success(self, test_database):
        """Suppression d'un concours existant."""
        await test_database.add_concours(123456)

        success = await test_database.delete_concours(123456)

        assert success is True

        concours = await test_database.get_concours_by_numero(123456)
        assert concours is None

    @pytest.mark.asyncio
    async def test_delete_concours_not_found(self, test_database):
        """Suppression d'un concours inexistant retourne False."""
        success = await test_database.delete_concours(999999)

        assert success is False

    @pytest.mark.asyncio
    async def test_count_concours(self, test_database):
        """Compte le nombre de concours."""
        assert await test_database.count_concours() == 0

        await test_database.add_concours(111111)
        await test_database.add_concours(222222)

        assert await test_database.count_concours() == 2

    @pytest.mark.asyncio
    async def test_count_concours_ouverts(self, test_database):
        """Compte les concours ouverts."""
        await test_database.add_concours(111111)
        await test_database.add_concours(222222)
        await test_database.add_concours(333333)

        await test_database.update_statut(111111, StatutConcours.ENGAGEMENT)
        await test_database.update_statut(222222, StatutConcours.DEMANDE)

        count = await test_database.count_concours_ouverts()

        assert count == 2
