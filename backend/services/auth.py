"""
Service d'authentification FFE via Playwright.
Gère la connexion, la persistance des cookies et la reconnexion automatique.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger("auth")

# Reconnection backoff parameters
MAX_RECONNECT_ATTEMPTS = 5
INITIAL_BACKOFF = 2.0  # seconds
MAX_BACKOFF = 300.0  # 5 minutes
BACKOFF_MULTIPLIER = 2.0


class FFEAuthenticator:
    """
    Gestionnaire d'authentification au site FFE.

    Utilise Playwright en mode headless pour simuler un navigateur
    et maintenir une session authentifiée.
    """

    # Sélecteurs pour le formulaire de connexion FFE
    SELECTORS = {
        "username_input": "input[name='username'], input[type='email'], #username",
        "password_input": "input[name='password'], input[type='password'], #password",
        "submit_button": "button[type='submit'], input[type='submit']",
        "logged_in_indicator": ".user-menu, .logged-in, .mon-compte, a[href*='logout']",
        "login_error": ".error-message, .alert-danger, .login-error",
    }

    def __init__(
        self,
        username: str,
        password: str,
        cookies_path: Path | str,
        headless: bool = True,
    ):
        """
        Initialise l'authentificateur FFE.

        Args:
            username: Email/identifiant FFE
            password: Mot de passe FFE
            cookies_path: Chemin pour sauvegarder les cookies
            headless: Mode sans interface graphique
        """
        self.username = username
        self.password = password
        self.cookies_path = Path(cookies_path)
        self.headless = headless

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Retourne True si connecté à FFE."""
        return self._connected

    @property
    def page(self) -> Page:
        """Retourne la page Playwright active."""
        if not self._page:
            raise RuntimeError("Page non initialisée. Appelez login() d'abord.")
        return self._page

    async def login(self) -> bool:
        """
        Effectue la connexion à FFE.

        Tente d'abord de charger les cookies existants.
        Si invalides, effectue une nouvelle connexion.

        Returns:
            True si connexion réussie, False sinon
        """
        try:
            # Initialiser Playwright
            await self._init_browser()

            # Tenter de charger les cookies existants
            if await self._load_cookies():
                if await self._is_session_valid():
                    logger.info("Session FFE restaurée depuis les cookies")
                    self._connected = True
                    return True
                else:
                    logger.info("Cookies expirés, nouvelle connexion requise")

            # Nouvelle connexion
            return await self._perform_login()

        except Exception as e:
            logger.error(f"Erreur lors de la connexion FFE: {e}")
            return False

    async def _init_browser(self) -> None:
        """Initialise le navigateur Playwright."""
        if self._browser:
            return

        logger.info("Initialisation du navigateur Playwright...")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._page = await self._context.new_page()

        logger.info("Navigateur initialisé")

    async def _load_cookies(self) -> bool:
        """
        Charge les cookies depuis le fichier.

        Returns:
            True si cookies chargés, False sinon
        """
        if not self.cookies_path.exists():
            logger.info("Aucun fichier de cookies trouvé")
            return False

        try:
            with open(self.cookies_path, "r") as f:
                cookies = json.load(f)

            await self._context.add_cookies(cookies)
            logger.info(f"Cookies chargés depuis {self.cookies_path}")
            return True

        except Exception as e:
            logger.warning(f"Erreur chargement cookies: {e}")
            return False

    async def _save_cookies(self) -> None:
        """Sauvegarde les cookies dans le fichier."""
        try:
            cookies = await self._context.cookies()

            # Créer le dossier parent si nécessaire
            self.cookies_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.cookies_path, "w") as f:
                json.dump(cookies, f, indent=2)

            logger.info(f"Cookies sauvegardés dans {self.cookies_path}")

        except Exception as e:
            logger.error(f"Erreur sauvegarde cookies: {e}")

    async def _is_session_valid(self) -> bool:
        """
        Vérifie si la session actuelle est valide.

        Returns:
            True si session valide, False sinon
        """
        try:
            # Naviguer vers une page protégée
            await self._page.goto(
                f"{settings.ffe_concours_url}",
                wait_until="networkidle",
                timeout=30000,
            )

            # Vérifier si on est redirigé vers le login
            current_url = self._page.url
            if "login" in current_url.lower():
                return False

            # Vérifier la présence d'un indicateur de connexion
            logged_in = await self._page.locator(
                self.SELECTORS["logged_in_indicator"]
            ).count()

            return logged_in > 0

        except Exception as e:
            logger.warning(f"Erreur vérification session: {e}")
            return False

    async def _perform_login(self) -> bool:
        """
        Effectue la connexion au site FFE.

        Returns:
            True si connexion réussie, False sinon
        """
        logger.info("Connexion au site FFE...")

        try:
            # Aller sur la page de login
            await self._page.goto(
                settings.ffe_login_url,
                wait_until="networkidle",
                timeout=30000,
            )

            # Attendre le formulaire
            await self._page.wait_for_selector(
                self.SELECTORS["username_input"],
                timeout=10000,
            )

            # Remplir le formulaire
            await self._page.fill(self.SELECTORS["username_input"], self.username)
            await self._page.fill(self.SELECTORS["password_input"], self.password)

            # Soumettre
            await self._page.click(self.SELECTORS["submit_button"])

            # Attendre la navigation
            await self._page.wait_for_load_state("networkidle", timeout=30000)

            # Petite pause pour laisser la page se stabiliser
            await asyncio.sleep(2)

            # Vérifier si la connexion a réussi
            current_url = self._page.url

            # Si on est toujours sur la page de login, vérifier les erreurs
            if "login" in current_url.lower():
                error_element = await self._page.locator(
                    self.SELECTORS["login_error"]
                ).count()
                if error_element > 0:
                    error_text = await self._page.locator(
                        self.SELECTORS["login_error"]
                    ).first.text_content()
                    logger.error(f"Erreur de connexion FFE: {error_text}")
                else:
                    logger.error("Connexion échouée - toujours sur la page de login")
                return False

            # Sauvegarder les cookies
            await self._save_cookies()

            self._connected = True
            logger.info("Connexion FFE réussie")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de la connexion: {e}")
            return False

    async def reconnect(self) -> bool:
        """
        Tente une reconnexion automatique simple.

        Returns:
            True si reconnexion réussie, False sinon
        """
        logger.info("Tentative de reconnexion FFE...")
        self._connected = False

        # Réinitialiser le contexte
        if self._context:
            await self._context.close()
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 720},
            )
            self._page = await self._context.new_page()

        return await self._perform_login()

    async def reconnect_with_backoff(self) -> bool:
        """
        Tente une reconnexion avec backoff exponentiel.

        Utilise un délai croissant entre les tentatives pour éviter
        de surcharger le serveur FFE en cas de problèmes prolongés.

        Returns:
            True si reconnexion réussie après N tentatives, False sinon
        """
        backoff = INITIAL_BACKOFF

        for attempt in range(1, MAX_RECONNECT_ATTEMPTS + 1):
            logger.info(
                f"Tentative de reconnexion {attempt}/{MAX_RECONNECT_ATTEMPTS} "
                f"(backoff: {backoff:.1f}s)"
            )

            # Attendre avant la tentative (sauf la première)
            if attempt > 1:
                await asyncio.sleep(backoff)
                # Augmenter le backoff pour la prochaine tentative
                backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)

            try:
                success = await self.reconnect()
                if success:
                    logger.info(
                        f"Reconnexion réussie après {attempt} tentative(s)"
                    )
                    return True
            except Exception as e:
                logger.warning(f"Erreur lors de la tentative {attempt}: {e}")
                continue

        logger.error(
            f"Échec de reconnexion après {MAX_RECONNECT_ATTEMPTS} tentatives"
        )
        return False

    async def navigate_to_concours(self, numero: int) -> Page:
        """
        Navigue vers la page d'un concours spécifique.

        Args:
            numero: Numéro du concours

        Returns:
            La page du concours

        Raises:
            RuntimeError: Si non connecté ou erreur de navigation
        """
        if not self._connected:
            raise RuntimeError("Non connecté à FFE")

        url = f"{settings.ffe_concours_url}/{numero}"

        try:
            await self._page.goto(url, wait_until="networkidle", timeout=30000)

            # Vérifier si redirigé vers login (session expirée)
            if "login" in self._page.url.lower():
                logger.warning("Session expirée, reconnexion...")
                if await self.reconnect():
                    await self._page.goto(url, wait_until="networkidle", timeout=30000)
                else:
                    raise RuntimeError("Impossible de se reconnecter à FFE")

            return self._page

        except Exception as e:
            logger.error(f"Erreur navigation vers concours {numero}: {e}")
            raise

    async def close(self) -> None:
        """Ferme proprement le navigateur."""
        logger.info("Fermeture du navigateur...")

        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        self._connected = False

        logger.info("Navigateur fermé")
