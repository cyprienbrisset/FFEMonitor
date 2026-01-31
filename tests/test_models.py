"""
Tests unitaires pour les modèles Pydantic.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from backend.models import (
    StatutConcours,
    ConcoursCreate,
    ConcoursResponse,
    ConcoursListResponse,
    HealthResponse,
    StatusResponse,
    MessageResponse,
)


class TestStatutConcours:
    """Tests de l'enum StatutConcours."""

    def test_values(self):
        """Vérification des valeurs de l'enum."""
        assert StatutConcours.FERME.value == "ferme"
        assert StatutConcours.ENGAGEMENT.value == "engagement"
        assert StatutConcours.DEMANDE.value == "demande"

    def test_from_string(self):
        """Création depuis une string."""
        assert StatutConcours("ferme") == StatutConcours.FERME
        assert StatutConcours("engagement") == StatutConcours.ENGAGEMENT
        assert StatutConcours("demande") == StatutConcours.DEMANDE


class TestConcoursCreate:
    """Tests du modèle ConcoursCreate."""

    def test_valid_numero(self):
        """Numéro valide accepté."""
        concours = ConcoursCreate(numero=123456)
        assert concours.numero == 123456

    def test_numero_must_be_positive(self):
        """Numéro doit être positif."""
        with pytest.raises(ValidationError) as exc_info:
            ConcoursCreate(numero=0)

        assert "greater than 0" in str(exc_info.value).lower()

    def test_numero_negative_rejected(self):
        """Numéro négatif rejeté."""
        with pytest.raises(ValidationError):
            ConcoursCreate(numero=-1)

    def test_numero_required(self):
        """Numéro est obligatoire."""
        with pytest.raises(ValidationError):
            ConcoursCreate()

    def test_numero_as_float_rejected(self):
        """Float est rejeté par Pydantic 2."""
        # Pydantic 2 est strict par défaut pour les conversions float -> int
        with pytest.raises(ValidationError):
            ConcoursCreate(numero=123.9)


class TestConcoursResponse:
    """Tests du modèle ConcoursResponse."""

    def test_valid_response(self):
        """Réponse valide créée."""
        now = datetime.now()
        response = ConcoursResponse(
            id=1,
            numero=123456,
            statut=StatutConcours.FERME,
            notifie=False,
            last_check=now,
            created_at=now,
        )

        assert response.id == 1
        assert response.numero == 123456
        assert response.statut == StatutConcours.FERME
        assert response.notifie is False

    def test_last_check_nullable(self):
        """last_check peut être None."""
        response = ConcoursResponse(
            id=1,
            numero=123456,
            statut=StatutConcours.FERME,
            notifie=False,
            last_check=None,
            created_at=datetime.now(),
        )

        assert response.last_check is None

    def test_from_attributes(self):
        """Création depuis un objet avec attributs."""

        class FakeConcours:
            id = 1
            numero = 123456
            statut = "engagement"
            notifie = True
            last_check = datetime.now()
            created_at = datetime.now()

        response = ConcoursResponse.model_validate(FakeConcours())

        assert response.id == 1
        assert response.statut == StatutConcours.ENGAGEMENT


class TestConcoursListResponse:
    """Tests du modèle ConcoursListResponse."""

    def test_empty_list(self):
        """Liste vide valide."""
        response = ConcoursListResponse(concours=[], total=0)

        assert response.concours == []
        assert response.total == 0

    def test_with_concours(self):
        """Liste avec concours."""
        now = datetime.now()
        concours1 = ConcoursResponse(
            id=1,
            numero=111111,
            statut=StatutConcours.FERME,
            notifie=False,
            last_check=None,
            created_at=now,
        )
        concours2 = ConcoursResponse(
            id=2,
            numero=222222,
            statut=StatutConcours.ENGAGEMENT,
            notifie=True,
            last_check=now,
            created_at=now,
        )

        response = ConcoursListResponse(
            concours=[concours1, concours2],
            total=2,
        )

        assert len(response.concours) == 2
        assert response.total == 2


class TestHealthResponse:
    """Tests du modèle HealthResponse."""

    def test_defaults(self):
        """Valeurs par défaut."""
        response = HealthResponse()

        assert response.status == "ok"
        assert response.ffe_connected is False
        assert response.surveillance_active is False
        assert response.concours_count == 0

    def test_custom_values(self):
        """Valeurs personnalisées."""
        response = HealthResponse(
            status="ok",
            ffe_connected=True,
            surveillance_active=True,
            concours_count=5,
        )

        assert response.ffe_connected is True
        assert response.surveillance_active is True
        assert response.concours_count == 5


class TestStatusResponse:
    """Tests du modèle StatusResponse."""

    def test_valid_status(self):
        """Statut valide."""
        response = StatusResponse(
            ffe_connected=True,
            surveillance_active=True,
            last_check=datetime.now(),
            concours_surveilles=10,
            concours_ouverts=2,
        )

        assert response.ffe_connected is True
        assert response.concours_surveilles == 10
        assert response.concours_ouverts == 2

    def test_last_check_nullable(self):
        """last_check peut être None."""
        response = StatusResponse(
            ffe_connected=False,
            surveillance_active=False,
            last_check=None,
            concours_surveilles=0,
            concours_ouverts=0,
        )

        assert response.last_check is None


class TestMessageResponse:
    """Tests du modèle MessageResponse."""

    def test_default_success(self):
        """success est True par défaut."""
        response = MessageResponse(message="Test")

        assert response.message == "Test"
        assert response.success is True

    def test_failure(self):
        """Message d'échec."""
        response = MessageResponse(message="Erreur", success=False)

        assert response.success is False
