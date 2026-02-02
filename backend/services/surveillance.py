"""
Service de surveillance des concours FFE.
Boucle asynchrone de vérification et détection d'ouverture.
Utilise Supabase comme base de données.
"""

import asyncio
import time
from datetime import datetime
from typing import Optional

from backend.supabase_client import supabase
from backend.models import StatutConcours
from backend.services.notification import NotificationDispatcher
from backend.utils.logger import get_logger

logger = get_logger("surveillance")


class SurveillanceService:
    """
    Moteur de surveillance des concours FFE.

    Vérifie périodiquement l'état des concours et envoie des
    notifications lors de l'ouverture des engagements.
    """

    # Nombre max de tentatives en cas d'erreur
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # secondes

    def __init__(
        self,
        notifier: NotificationDispatcher,
        check_interval: int = 5,
    ):
        """
        Initialise le service de surveillance.

        Args:
            notifier: Dispatcher de notifications OneSignal
            check_interval: Intervalle entre les vérifications (secondes)
        """
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
        """Vérifie l'état de tous les concours non ouverts."""
        from backend.services.scraper import scraper

        # Récupérer les concours à surveiller (non encore ouverts)
        concours_list = await supabase.get_concours_non_notifies()

        if not concours_list:
            logger.debug("Aucun concours à surveiller")
            return

        logger.debug(f"Vérification de {len(concours_list)} concours...")

        for concours in concours_list:
            if not self._running:
                break

            try:
                await self._check_concours_scraper(concours, scraper)
            except Exception as e:
                logger.error(f"Erreur vérification concours {concours.get('numero')}: {e}")
                continue

            # Petite pause entre chaque concours pour éviter la surcharge
            await asyncio.sleep(1)

    async def _check_concours_scraper(self, concours: dict, scraper) -> None:
        """
        Vérifie l'état d'un concours via le scraper HTTP.

        Args:
            concours: Données du concours depuis Supabase
            scraper: Instance du scraper FFE
        """
        numero = concours.get("numero")
        statut_before = concours.get("statut", "previsionnel")
        logger.debug(f"Vérification concours {numero} (scraper)...")

        start_time = time.time()

        # Scraper les infos du concours
        info = await scraper.fetch_concours_info(numero)

        # Calculer le temps de réponse
        response_time_ms = int((time.time() - start_time) * 1000)

        # Déterminer le nouveau statut
        statut_after = info.statut or "previsionnel"

        # Enregistrer dans l'historique
        await supabase.record_check(
            concours_numero=numero,
            statut_before=statut_before,
            statut_after=statut_after,
            response_time_ms=response_time_ms,
            success=True,
        )

        # Mettre à jour les infos du concours
        update_data = {"last_check": datetime.now().isoformat()}

        if info.nom:
            update_data["nom"] = info.nom
        if info.lieu:
            update_data["lieu"] = info.lieu
        if info.date_debut:
            update_data["date_debut"] = info.date_debut
        if info.date_fin:
            update_data["date_fin"] = info.date_fin

        await supabase.update_concours(numero, update_data)

        # Si le concours vient d'ouvrir (statut change vers engagement/demande)
        if info.is_open and statut_before not in ("engagement", "demande"):
            statut = "engagement" if info.statut == "engagement" else "demande"
            logger.info(f"Concours {numero} OUVERT ({statut})")

            # Planifier les notifications pour tous les abonnés
            opened_at = datetime.now()
            try:
                queued_count = await self.notifier.queue_notifications_for_concours(
                    concours_numero=numero,
                    opened_at=opened_at,
                )
                logger.info(f"{queued_count} notifications planifiées pour concours {numero}")
            except Exception as e:
                logger.error(f"Échec planification notifications pour concours {numero}: {e}")

            # Enregistrer l'événement d'ouverture
            await supabase.record_opening(
                concours_numero=numero,
                statut=statut,
                notification_sent_at=opened_at.isoformat(),
            )

            # Mettre à jour le statut en base
            await supabase.update_concours_status(numero, is_open=True, statut=statut)

        elif info.statut and info.statut != statut_before:
            # Mettre à jour le statut même si pas d'ouverture
            is_open = info.statut in ("engagement", "demande")
            await supabase.update_concours_status(numero, is_open=is_open, statut=info.statut)

        else:
            logger.debug(f"Concours {numero}: {info.statut}")

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse une date en format ISO.

        Args:
            date_str: Date en format texte (ex: "15/01/2024")

        Returns:
            Date en format ISO ou None
        """
        import re

        # Essayer différents formats de date
        patterns = [
            (r"(\d{2})/(\d{2})/(\d{4})", lambda m: f"{m.group(3)}-{m.group(2)}-{m.group(1)}"),
            (r"(\d{4})-(\d{2})-(\d{2})", lambda m: m.group(0)),
            (r"(\d{2})-(\d{2})-(\d{4})", lambda m: f"{m.group(3)}-{m.group(2)}-{m.group(1)}"),
        ]

        for pattern, formatter in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    date_iso = formatter(match)
                    # Valider que c'est une date valide
                    datetime.fromisoformat(date_iso)
                    return date_iso
                except ValueError:
                    continue

        return None
