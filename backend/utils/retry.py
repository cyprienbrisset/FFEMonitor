"""
Utilitaires de retry et backoff pour la gestion des erreurs réseau.
"""

import asyncio
import functools
from typing import Callable, TypeVar, Any
from backend.utils.logger import get_logger

logger = get_logger("retry")

T = TypeVar("T")


class RetryError(Exception):
    """Exception levée quand toutes les tentatives ont échoué."""

    def __init__(self, message: str, last_exception: Exception | None = None):
        super().__init__(message)
        self.last_exception = last_exception


async def retry_async(
    func: Callable[..., T],
    *args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential: bool = True,
    exceptions: tuple = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
    **kwargs,
) -> T:
    """
    Exécute une fonction async avec retry et backoff exponentiel.

    Args:
        func: Fonction async à exécuter
        *args: Arguments positionnels
        max_attempts: Nombre maximum de tentatives
        base_delay: Délai initial entre les tentatives (secondes)
        max_delay: Délai maximum entre les tentatives
        exponential: Utiliser un backoff exponentiel
        exceptions: Types d'exceptions à intercepter
        on_retry: Callback appelé à chaque retry (attempt, exception)
        **kwargs: Arguments nommés

    Returns:
        Résultat de la fonction

    Raises:
        RetryError: Si toutes les tentatives ont échoué
    """
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)

        except exceptions as e:
            last_exception = e

            if attempt == max_attempts:
                logger.error(
                    f"Toutes les tentatives ont échoué ({max_attempts}): {e}"
                )
                raise RetryError(
                    f"Échec après {max_attempts} tentatives",
                    last_exception=e,
                )

            # Calculer le délai
            if exponential:
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            else:
                delay = base_delay

            logger.warning(
                f"Tentative {attempt}/{max_attempts} échouée: {e}. "
                f"Retry dans {delay:.1f}s..."
            )

            if on_retry:
                on_retry(attempt, e)

            await asyncio.sleep(delay)

    # Ne devrait jamais arriver
    raise RetryError("Erreur inattendue", last_exception=last_exception)


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential: bool = True,
    exceptions: tuple = (Exception,),
):
    """
    Décorateur pour ajouter un retry automatique à une fonction async.

    Exemple:
        @with_retry(max_attempts=3, base_delay=2.0)
        async def fetch_data():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_async(
                func,
                *args,
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential=exponential,
                exceptions=exceptions,
                **kwargs,
            )

        return wrapper

    return decorator


class RateLimiter:
    """
    Limiteur de débit pour éviter de surcharger le serveur FFE.

    Utilise un algorithme de token bucket simplifié.
    """

    def __init__(
        self,
        min_interval: float = 1.0,
        max_requests_per_minute: int = 30,
    ):
        """
        Initialise le rate limiter.

        Args:
            min_interval: Intervalle minimum entre les requêtes (secondes)
            max_requests_per_minute: Nombre maximum de requêtes par minute
        """
        self.min_interval = min_interval
        self.max_requests_per_minute = max_requests_per_minute
        self._last_request_time: float = 0
        self._request_times: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Attend si nécessaire pour respecter les limites de débit.
        """
        async with self._lock:
            now = asyncio.get_event_loop().time()

            # Nettoyer les anciens timestamps (> 1 minute)
            self._request_times = [
                t for t in self._request_times if now - t < 60
            ]

            # Vérifier la limite par minute
            if len(self._request_times) >= self.max_requests_per_minute:
                oldest = self._request_times[0]
                wait_time = 60 - (now - oldest)
                if wait_time > 0:
                    logger.warning(
                        f"Rate limit atteint, attente de {wait_time:.1f}s"
                    )
                    await asyncio.sleep(wait_time)
                    now = asyncio.get_event_loop().time()

            # Vérifier l'intervalle minimum
            elapsed = now - self._last_request_time
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)

            # Enregistrer la requête
            self._last_request_time = asyncio.get_event_loop().time()
            self._request_times.append(self._last_request_time)

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Instance globale du rate limiter
rate_limiter = RateLimiter(min_interval=2.0, max_requests_per_minute=20)
