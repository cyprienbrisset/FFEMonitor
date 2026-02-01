"""
Service de surveillance des concours FFE.
Boucle asynchrone de vérification et détection d'ouverture.
"""

import asyncio
import time
from datetime import datetime
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
        # Sélecteurs pour scraper les informations du concours
        "date_debut": [
            ".date-debut",
            "[data-date-debut]",
            ".concours-date-debut",
            "span:has-text('Du') + span",
        ],
        "date_fin": [
            ".date-fin",
            "[data-date-fin]",
            ".concours-date-fin",
            "span:has-text('Au') + span",
        ],
        "lieu": [
            ".lieu",
            ".concours-lieu",
            "[data-lieu]",
            ".location",
            "span:has-text('Lieu') + span",
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
        from backend.services.scraper import scraper

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
                await self._check_concours_scraper(concours, scraper)
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
        statut_before = concours.get("statut", "ferme")
        logger.debug(f"Vérification concours {numero}...")

        start_time = time.time()
        success = True
        statut = None

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
                success = False
                # Enregistrer l'échec dans l'historique
                response_time_ms = int((time.time() - start_time) * 1000)
                await self.db.record_check(
                    concours_numero=numero,
                    statut_before=statut_before,
                    statut_after=None,
                    response_time_ms=response_time_ms,
                    success=False,
                )
                return

            # Détecter l'ouverture
            statut = await self._detect_opening(page)

            # Scraper les informations de date/lieu si pas encore enregistrées
            if not concours.get("date_debut"):
                await self._scrape_concours_info(numero, page)

        # Calculer le temps de réponse
        response_time_ms = int((time.time() - start_time) * 1000)

        # Déterminer le statut après vérification
        statut_after = statut.value if statut else "ferme"

        # Enregistrer dans l'historique
        await self.db.record_check(
            concours_numero=numero,
            statut_before=statut_before,
            statut_after=statut_after,
            response_time_ms=response_time_ms,
            success=True,
        )

        # Mettre à jour le timestamp de dernière vérification
        await self.db.update_last_check(numero)

        # Si un bouton a été détecté
        if statut and statut != StatutConcours.FERME:
            logger.info(f"Concours {numero} OUVERT ({statut.value})")

            # Envoyer la notification avec retry
            notification_sent_at = None
            try:
                notif_sent = await retry_async(
                    self.notifier.send_notification,
                    numero,
                    statut,
                    max_attempts=3,
                    base_delay=1.0,
                )
                if notif_sent:
                    notification_sent_at = datetime.now().isoformat()
            except RetryError:
                notif_sent = False
                logger.error(f"Échec notification pour concours {numero}")

            # Enregistrer l'événement d'ouverture
            await self.db.record_opening(
                concours_numero=numero,
                statut=statut.value,
                notification_sent_at=notification_sent_at,
            )

            # Mettre à jour le statut en base
            await self.db.update_statut(numero, statut, notifie=notif_sent)

        else:
            logger.debug(f"Concours {numero}: fermé")

    async def _check_concours_scraper(self, concours: dict, scraper) -> None:
        """
        Vérifie l'état d'un concours via le scraper HTTP (sans Playwright).

        Args:
            concours: Données du concours depuis la base
            scraper: Instance du scraper FFE
        """
        numero = concours["numero"]
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
        await self.db.record_check(
            concours_numero=numero,
            statut_before=statut_before,
            statut_after=statut_after,
            response_time_ms=response_time_ms,
            success=True,
        )

        # Mettre à jour les infos du concours
        if info.nom or info.lieu or info.date_debut:
            await self.db.update_concours_info(
                numero=numero,
                nom=info.nom,
                lieu=info.lieu,
                date_debut=info.date_debut,
                date_fin=info.date_fin,
            )

        # Mettre à jour le timestamp
        await self.db.update_last_check(numero)

        # Si le concours vient d'ouvrir (statut change vers engagement/demande)
        if info.is_open and statut_before not in ("engagement", "demande"):
            statut = StatutConcours.ENGAGEMENT if info.statut == "engagement" else StatutConcours.DEMANDE
            logger.info(f"Concours {numero} OUVERT ({statut.value})")

            # Envoyer la notification
            notification_sent_at = None
            try:
                notif_sent = await self.notifier.send_notification(numero, statut)
                if notif_sent:
                    notification_sent_at = datetime.now().isoformat()
            except Exception as e:
                notif_sent = False
                logger.error(f"Échec notification pour concours {numero}: {e}")

            # Enregistrer l'événement d'ouverture
            await self.db.record_opening(
                concours_numero=numero,
                statut=statut.value,
                notification_sent_at=notification_sent_at,
            )

            # Mettre à jour le statut en base
            await self.db.update_statut(numero, statut, notifie=notif_sent)
        elif info.statut and info.statut != statut_before:
            # Mettre à jour le statut même si pas d'ouverture
            try:
                statut = StatutConcours(info.statut)
                await self.db.update_statut(numero, statut, notifie=False)
            except ValueError:
                pass
        else:
            logger.debug(f"Concours {numero}: {info.statut}")

    async def _detect_opening(self, page) -> Optional[StatutConcours]:
        """
        Détecte l'ouverture d'un concours via les boutons DOM ou le texte.

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

        # Fallback: vérifier le texte "Ouvert aux engagements" dans la page
        try:
            page_content = await page.content()
            import re
            if re.search(r'[Oo]uvert(?:e)?(?:s)?\s+aux\s+engagements', page_content, re.IGNORECASE):
                logger.debug("Texte 'Ouvert aux engagements' détecté")
                return StatutConcours.ENGAGEMENT
        except Exception:
            pass

        return None

    async def _scrape_concours_info(self, numero: int, page) -> None:
        """
        Scrape les informations depuis la page du concours.
        Utilise d'abord le scraper httpx léger, puis Playwright en fallback.

        Args:
            numero: Numéro du concours
            page: Page Playwright du concours
        """
        from backend.services.scraper import scraper

        # Utiliser le scraper httpx (plus fiable pour le parsing)
        try:
            info = await scraper.fetch_concours_info(numero)
            if info.nom or info.lieu or info.date_debut:
                await self.db.update_concours_info(
                    numero=numero,
                    nom=info.nom,
                    lieu=info.lieu,
                    date_debut=info.date_debut,
                    date_fin=info.date_fin,
                )
                logger.debug(
                    f"Infos concours {numero}: {info.nom}, "
                    f"{info.date_debut} - {info.date_fin}, {info.lieu}"
                )
                return
        except Exception as e:
            logger.debug(f"Scraper httpx échoué pour {numero}: {e}")

        # Fallback: essayer avec Playwright
        date_debut = None
        date_fin = None
        lieu = None

        # Essayer de récupérer la date de début
        for selector in self.SELECTORS["date_debut"]:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    text = await element.text_content()
                    if text:
                        date_debut = self._parse_date(text.strip())
                        break
            except Exception:
                continue

        # Essayer de récupérer la date de fin
        for selector in self.SELECTORS["date_fin"]:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    text = await element.text_content()
                    if text:
                        date_fin = self._parse_date(text.strip())
                        break
            except Exception:
                continue

        # Essayer de récupérer le lieu
        for selector in self.SELECTORS["lieu"]:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    text = await element.text_content()
                    if text:
                        lieu = text.strip()
                        break
            except Exception:
                continue

        # Mettre à jour en base si on a trouvé des informations
        if date_debut or date_fin or lieu:
            await self.db.update_concours_info(
                numero=numero,
                date_debut=date_debut,
                date_fin=date_fin,
                lieu=lieu,
            )
            logger.debug(f"Infos concours {numero} (Playwright): {date_debut} - {date_fin}, {lieu}")

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
