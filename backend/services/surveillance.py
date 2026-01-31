"""
Service de surveillance des concours FFE.
Boucle asynchrone de vérification et détection d'ouverture.
"""

import asyncio
from typing import Optional

from backend.database import Database
from backend.models import StatutConcours
from backend.services.auth import FFEAuthenticator
from backend.services.notification import MultiNotifier
from backend.utils.logger import get_logger
from backend.utils.retry import retry_async, rate_limiter, RetryError

logger = get_logger("surveillance")


class SurveillanceService:
    """
    Moteur de surveillance des concours FFE.

    Vérifie périodiquement l'état des concours et envoie des
    notifications lors de l'ouverture des engagements.
    """

    # Sélecteurs pour détecter l'ouverture des concours
    # Plusieurs variantes pour plus de robustesse
    SELECTORS = {
        "engager": [
            "button:has-text('Engager')",
            "a:has-text('Engager')",
            ".btn-engager",
            "[data-action='engager']",
            "button.engagement",
        ],
        "demande": [
            "button:has-text('Demande de participation')",
            "a:has-text('Demande de participation')",
            "button:has-text('Demande')",
            ".btn-demande",
            "[data-action='demande']",
        ],
    }

    # Nombre max de tentatives en cas d'erreur
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # secondes

    def __init__(
        self,
        authenticator: FFEAuthenticator,
        database: Database,
        notifier: MultiNotifier,
        check_interval: int = 5,
    ):
        """
        Initialise le service de surveillance.

        Args:
            authenticator: Service d'authentification FFE
            database: Instance de la base de données
            notifier: Service de notification multi-canal
            check_interval: Intervalle entre les vérifications (secondes)
        """
        self.auth = authenticator
        self.db = database
        self.notifier = notifier
        self.check_interval = check_interval

        self._running = False
        self._error_count = 0

    @property
    def is_running(self) -> bool:
        """Retourne True si la surveillance est active."""
        return self._running

    async def start(self) -> None:
        """
        Démarre la boucle de surveillance.

        Cette méthode tourne indéfiniment jusqu'à l'arrêt de l'application.
        """
        self._running = True
        logger.info(f"Surveillance démarrée (intervalle: {self.check_interval}s)")

        # Message de démarrage Telegram
        await self.notifier.send_startup_message()

        while self._running:
            try:
                await self._check_all_concours()
                self._error_count = 0  # Reset après succès

            except asyncio.CancelledError:
                logger.info("Surveillance annulée")
                break

            except Exception as e:
                self._error_count += 1
                logger.error(f"Erreur surveillance (tentative {self._error_count}): {e}")

                if self._error_count >= self.MAX_RETRIES:
                    logger.error("Trop d'erreurs consécutives, pause prolongée...")
                    await self.notifier.send_error_message(
                        f"Erreurs répétées de surveillance: {e}"
                    )
                    await asyncio.sleep(60)  # Pause d'une minute
                    self._error_count = 0
                else:
                    await asyncio.sleep(self.RETRY_DELAY)
                continue

            # Attendre avant la prochaine vérification
            await asyncio.sleep(self.check_interval)

        self._running = False
        logger.info("Surveillance arrêtée")

    async def stop(self) -> None:
        """Arrête la surveillance."""
        logger.info("Arrêt de la surveillance demandé...")
        self._running = False

    async def _check_all_concours(self) -> None:
        """Vérifie l'état de tous les concours non notifiés."""
        # Récupérer les concours à surveiller
        concours_list = await self.db.get_concours_non_notifies()

        if not concours_list:
            logger.debug("Aucun concours à surveiller")
            return

        logger.debug(f"Vérification de {len(concours_list)} concours...")

        for concours in concours_list:
            if not self._running:
                break

            try:
                await self._check_concours(concours)
            except Exception as e:
                logger.error(f"Erreur vérification concours {concours['numero']}: {e}")
                continue

            # Petite pause entre chaque concours pour éviter la surcharge
            await asyncio.sleep(1)

    async def _check_concours(self, concours: dict) -> None:
        """
        Vérifie l'état d'un concours spécifique.

        Args:
            concours: Données du concours depuis la base
        """
        numero = concours["numero"]
        logger.debug(f"Vérification concours {numero}...")

        # Utiliser le rate limiter pour éviter de surcharger FFE
        async with rate_limiter:
            # Naviguer vers la page du concours avec retry
            try:
                page = await retry_async(
                    self.auth.navigate_to_concours,
                    numero,
                    max_attempts=2,
                    base_delay=3.0,
                    exceptions=(Exception,),
                )
            except RetryError as e:
                logger.error(f"Impossible d'accéder au concours {numero}: {e}")
                return

            # Détecter l'ouverture
            statut = await self._detect_opening(page)

        # Mettre à jour le timestamp de dernière vérification
        await self.db.update_last_check(numero)

        # Si un bouton a été détecté
        if statut and statut != StatutConcours.FERME:
            logger.info(f"🎯 Concours {numero} OUVERT ({statut.value})")

            # Envoyer la notification avec retry
            try:
                notif_sent = await retry_async(
                    self.notifier.send_notification,
                    numero,
                    statut,
                    max_attempts=3,
                    base_delay=1.0,
                )
            except RetryError:
                notif_sent = False
                logger.error(f"Échec notification pour concours {numero}")

            # Mettre à jour le statut en base
            await self.db.update_statut(numero, statut, notifie=notif_sent)

        else:
            logger.debug(f"Concours {numero}: fermé")

    async def _detect_opening(self, page) -> Optional[StatutConcours]:
        """
        Détecte l'ouverture d'un concours via les boutons DOM.

        Args:
            page: Page Playwright du concours

        Returns:
            StatutConcours si ouvert, None si fermé
        """
        # Vérifier le bouton "Engager" (concours amateur)
        for selector in self.SELECTORS["engager"]:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    logger.debug(f"Bouton 'Engager' détecté avec: {selector}")
                    return StatutConcours.ENGAGEMENT
            except Exception:
                continue

        # Vérifier le bouton "Demande de participation" (concours international)
        for selector in self.SELECTORS["demande"]:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    logger.debug(f"Bouton 'Demande' détecté avec: {selector}")
                    return StatutConcours.DEMANDE
            except Exception:
                continue

        return None

    async def check_single_concours(self, numero: int) -> StatutConcours:
        """
        Vérifie l'état d'un seul concours (pour tests).

        Args:
            numero: Numéro du concours

        Returns:
            Statut du concours
        """
        page = await self.auth.navigate_to_concours(numero)
        statut = await self._detect_opening(page)
        return statut or StatutConcours.FERME
