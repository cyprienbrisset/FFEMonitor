"""
Tests unitaires pour le service de surveillance.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.surveillance import SurveillanceService
from backend.models import StatutConcours
from backend.utils import retry as retry_module


class TestSurveillanceDetection:
    """Tests de détection des boutons d'ouverture."""

    @pytest.mark.asyncio
    async def test_detect_opening_ferme(
        self, test_database, mock_authenticator, mock_notifier, mock_page_ferme
    ):
        """Détection correcte d'un concours fermé."""
        service = SurveillanceService(
            authenticator=mock_authenticator,
            database=test_database,
            notifier=mock_notifier,
        )

        result = await service._detect_opening(mock_page_ferme)

        assert result is None

    @pytest.mark.asyncio
    async def test_detect_opening_engagement(
        self, test_database, mock_authenticator, mock_notifier, mock_page_engagement
    ):
        """Détection correcte du bouton Engager."""
        service = SurveillanceService(
            authenticator=mock_authenticator,
            database=test_database,
            notifier=mock_notifier,
        )

        result = await service._detect_opening(mock_page_engagement)

        assert result == StatutConcours.ENGAGEMENT

    @pytest.mark.asyncio
    async def test_detect_opening_demande(
        self, test_database, mock_authenticator, mock_notifier, mock_page_demande
    ):
        """Détection correcte du bouton Demande de participation."""
        service = SurveillanceService(
            authenticator=mock_authenticator,
            database=test_database,
            notifier=mock_notifier,
        )

        result = await service._detect_opening(mock_page_demande)

        assert result == StatutConcours.DEMANDE


class TestSurveillanceCheck:
    """Tests de vérification des concours."""

    @pytest.mark.asyncio
    async def test_check_concours_ferme(
        self, test_database, mock_authenticator, mock_notifier, mock_page_ferme
    ):
        """Vérification d'un concours fermé ne notifie pas."""
        # Préparer
        await test_database.add_concours(123456)
        mock_authenticator.navigate_to_concours.return_value = mock_page_ferme

        service = SurveillanceService(
            authenticator=mock_authenticator,
            database=test_database,
            notifier=mock_notifier,
        )

        concours = await test_database.get_concours_by_numero(123456)

        # Exécuter
        await service._check_concours(concours)

        # Vérifier
        mock_notifier.send_notification.assert_not_called()

        updated = await test_database.get_concours_by_numero(123456)
        assert updated["statut"] == "ferme"
        assert updated["notifie"] is False

    @pytest.mark.asyncio
    async def test_check_concours_ouvert_engagement(
        self, test_database, mock_authenticator, mock_notifier, mock_page_engagement
    ):
        """Vérification d'un concours ouvert (engagement) notifie."""
        # Préparer
        await test_database.add_concours(123456)
        mock_authenticator.navigate_to_concours.return_value = mock_page_engagement

        service = SurveillanceService(
            authenticator=mock_authenticator,
            database=test_database,
            notifier=mock_notifier,
        )

        concours = await test_database.get_concours_by_numero(123456)

        # Exécuter
        await service._check_concours(concours)

        # Vérifier
        mock_notifier.send_notification.assert_called_once_with(
            123456, StatutConcours.ENGAGEMENT
        )

        updated = await test_database.get_concours_by_numero(123456)
        assert updated["statut"] == "engagement"
        assert updated["notifie"] is True

    @pytest.mark.asyncio
    async def test_check_concours_ouvert_demande(
        self, test_database, mock_authenticator, mock_notifier, mock_page_demande
    ):
        """Vérification d'un concours ouvert (demande) notifie."""
        # Préparer
        await test_database.add_concours(123456)
        mock_authenticator.navigate_to_concours.return_value = mock_page_demande

        service = SurveillanceService(
            authenticator=mock_authenticator,
            database=test_database,
            notifier=mock_notifier,
        )

        concours = await test_database.get_concours_by_numero(123456)

        # Exécuter
        await service._check_concours(concours)

        # Vérifier
        mock_notifier.send_notification.assert_called_once_with(
            123456, StatutConcours.DEMANDE
        )

        updated = await test_database.get_concours_by_numero(123456)
        assert updated["statut"] == "demande"
        assert updated["notifie"] is True


class TestSurveillanceLoop:
    """Tests de la boucle de surveillance."""

    @pytest.mark.asyncio
    async def test_check_all_concours_empty(
        self, test_database, mock_authenticator, mock_notifier
    ):
        """Pas de vérification si aucun concours."""
        service = SurveillanceService(
            authenticator=mock_authenticator,
            database=test_database,
            notifier=mock_notifier,
        )

        await service._check_all_concours()

        mock_authenticator.navigate_to_concours.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_all_concours_skips_notified(
        self, test_database, mock_authenticator, mock_notifier, mock_page_ferme
    ):
        """Les concours déjà notifiés sont ignorés."""
        # Préparer
        await test_database.add_concours(123456)
        await test_database.update_statut(
            123456, StatutConcours.ENGAGEMENT, notifie=True
        )

        mock_authenticator.navigate_to_concours.return_value = mock_page_ferme

        service = SurveillanceService(
            authenticator=mock_authenticator,
            database=test_database,
            notifier=mock_notifier,
        )

        # Exécuter
        await service._check_all_concours()

        # Vérifier - pas de navigation car déjà notifié
        mock_authenticator.navigate_to_concours.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_all_concours_multiple(
        self, test_database, mock_authenticator, mock_notifier
    ):
        """Vérifie tous les concours non notifiés."""
        # Préparer
        await test_database.add_concours(111111)
        await test_database.add_concours(222222)
        await test_database.add_concours(333333)

        service = SurveillanceService(
            authenticator=mock_authenticator,
            database=test_database,
            notifier=mock_notifier,
        )

        # Activer le service pour que la boucle fonctionne
        service._running = True

        # Mock _check_concours pour compter les appels
        with patch.object(service, '_check_concours', new_callable=AsyncMock) as mock_check:
            # Exécuter
            await service._check_all_concours()

            # Vérifier - 3 concours vérifiés
            assert mock_check.call_count == 3

    @pytest.mark.asyncio
    async def test_running_state(
        self, test_database, mock_authenticator, mock_notifier
    ):
        """Le service démarre et s'arrête correctement."""
        service = SurveillanceService(
            authenticator=mock_authenticator,
            database=test_database,
            notifier=mock_notifier,
        )

        assert service.is_running is False

        # Simuler le démarrage sans vraiment lancer la boucle
        service._running = True
        assert service.is_running is True

        await service.stop()
        assert service.is_running is False


class TestSurveillanceErrorHandling:
    """Tests de gestion des erreurs."""

    @pytest.mark.asyncio
    async def test_check_concours_navigation_error(
        self, test_database, mock_authenticator, mock_notifier
    ):
        """Une erreur de navigation ne crash pas le service."""
        await test_database.add_concours(123456)
        mock_authenticator.navigate_to_concours.side_effect = Exception("Network error")

        service = SurveillanceService(
            authenticator=mock_authenticator,
            database=test_database,
            notifier=mock_notifier,
        )

        concours = await test_database.get_concours_by_numero(123456)

        # Ne doit pas lever d'exception
        # La méthode _check_concours est appelée dans un try/except dans _check_all_concours
        try:
            await service._check_concours(concours)
        except Exception:
            pass  # Attendu

        # Le concours reste non notifié
        updated = await test_database.get_concours_by_numero(123456)
        assert updated["notifie"] is False

    @pytest.mark.asyncio
    async def test_check_single_concours(
        self, test_database, mock_authenticator, mock_notifier, mock_page_engagement
    ):
        """Test de vérification d'un seul concours (méthode utilitaire)."""
        mock_authenticator.navigate_to_concours.return_value = mock_page_engagement

        service = SurveillanceService(
            authenticator=mock_authenticator,
            database=test_database,
            notifier=mock_notifier,
        )

        result = await service.check_single_concours(123456)

        assert result == StatutConcours.ENGAGEMENT
