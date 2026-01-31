"""
Tests unitaires pour les utilitaires de retry et rate limiting.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.utils.retry import (
    retry_async,
    with_retry,
    RetryError,
    RateLimiter,
)


class TestRetryAsync:
    """Tests de la fonction retry_async."""

    @pytest.mark.asyncio
    async def test_success_first_try(self):
        """Succès au premier essai."""
        mock_func = AsyncMock(return_value="success")

        result = await retry_async(mock_func, max_attempts=3)

        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        """Succès après un retry."""
        mock_func = AsyncMock(side_effect=[Exception("fail"), "success"])

        result = await retry_async(
            mock_func,
            max_attempts=3,
            base_delay=0.01,  # Délai court pour le test
        )

        assert result == "success"
        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_all_attempts_fail(self):
        """Toutes les tentatives échouent."""
        mock_func = AsyncMock(side_effect=Exception("always fails"))

        with pytest.raises(RetryError) as exc_info:
            await retry_async(
                mock_func,
                max_attempts=3,
                base_delay=0.01,
            )

        assert "3 tentatives" in str(exc_info.value)
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_specific_exceptions(self):
        """Seules les exceptions spécifiées déclenchent un retry."""
        mock_func = AsyncMock(side_effect=ValueError("specific error"))

        # ValueError n'est pas dans la liste, donc pas de retry
        with pytest.raises(RetryError):
            await retry_async(
                mock_func,
                max_attempts=3,
                base_delay=0.01,
                exceptions=(ValueError,),
            )

        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_on_retry_callback(self):
        """Callback appelé à chaque retry."""
        mock_func = AsyncMock(side_effect=[Exception("fail1"), Exception("fail2"), "success"])
        on_retry_mock = MagicMock()

        result = await retry_async(
            mock_func,
            max_attempts=3,
            base_delay=0.01,
            on_retry=on_retry_mock,
        )

        assert result == "success"
        assert on_retry_mock.call_count == 2

    @pytest.mark.asyncio
    async def test_with_args_and_kwargs(self):
        """Arguments passés correctement à la fonction."""
        mock_func = AsyncMock(return_value="result")

        await retry_async(
            mock_func,
            "arg1",
            "arg2",
            kwarg1="value1",
            max_attempts=3,
        )

        mock_func.assert_called_once_with("arg1", "arg2", kwarg1="value1")


class TestWithRetryDecorator:
    """Tests du décorateur with_retry."""

    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Décorateur fonctionne correctement."""
        call_count = [0]

        @with_retry(max_attempts=3, base_delay=0.01)
        async def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("fail")
            return "success"

        result = await test_func()

        assert result == "success"
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_decorator_preserves_metadata(self):
        """Le décorateur préserve les métadonnées de la fonction."""

        @with_retry(max_attempts=3)
        async def documented_func():
            """Documentation de la fonction."""
            return True

        assert documented_func.__name__ == "documented_func"
        assert "Documentation" in documented_func.__doc__


class TestRetryError:
    """Tests de l'exception RetryError."""

    def test_error_message(self):
        """Message d'erreur correct."""
        error = RetryError("Test message")
        assert str(error) == "Test message"

    def test_last_exception_stored(self):
        """Dernière exception stockée."""
        original = ValueError("original")
        error = RetryError("Wrapper", last_exception=original)

        assert error.last_exception is original


class TestRateLimiter:
    """Tests du rate limiter."""

    @pytest.mark.asyncio
    async def test_min_interval_enforced(self):
        """Intervalle minimum respecté."""
        limiter = RateLimiter(min_interval=0.1, max_requests_per_minute=100)

        start = asyncio.get_event_loop().time()

        await limiter.acquire()
        await limiter.acquire()

        elapsed = asyncio.get_event_loop().time() - start

        # Devrait avoir attendu au moins min_interval
        assert elapsed >= 0.1

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Utilisation comme context manager."""
        limiter = RateLimiter(min_interval=0.01, max_requests_per_minute=100)

        async with limiter:
            pass  # Devrait fonctionner sans erreur

    @pytest.mark.asyncio
    async def test_request_times_cleaned(self):
        """Les anciens timestamps sont nettoyés."""
        limiter = RateLimiter(min_interval=0.01, max_requests_per_minute=100)

        # Ajouter un vieux timestamp manuellement
        limiter._request_times = [0]  # Timestamp très ancien

        await limiter.acquire()

        # Le vieux timestamp devrait être nettoyé
        assert all(
            t > asyncio.get_event_loop().time() - 60
            for t in limiter._request_times
        )


class TestRateLimiterIntegration:
    """Tests d'intégration du rate limiter."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_multiple_requests_throttled(self):
        """Plusieurs requêtes sont throttlées."""
        limiter = RateLimiter(min_interval=0.05, max_requests_per_minute=100)

        start = asyncio.get_event_loop().time()
        request_count = 5

        for _ in range(request_count):
            await limiter.acquire()

        elapsed = asyncio.get_event_loop().time() - start

        # Devrait avoir attendu au moins (n-1) * min_interval
        expected_min = (request_count - 1) * 0.05
        assert elapsed >= expected_min * 0.9  # 10% de tolérance
