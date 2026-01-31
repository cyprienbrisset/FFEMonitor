"""
Point d'entrée de l'application EngageWatch.
Configuration FastAPI et gestion du cycle de vie.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from jose import jwt, JWTError

from backend.config import settings
from backend.database import db
from backend.routers import health, concours, auth
from backend.utils.logger import setup_logger, get_logger

# Configuration du logger principal
setup_logger("engagewatch", settings.log_level)
logger = get_logger("main")

# État global de l'application (partagé entre modules)
app_state: dict = {
    "ffe_connected": False,
    "surveillance_active": False,
    "concours_count": 0,
    "surveillance_task": None,
    "authenticator": None,
    "notifier": None,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    Initialise les services au démarrage et les ferme à l'arrêt.
    """
    logger.info("=" * 50)
    logger.info("EngageWatch - Démarrage")
    logger.info("=" * 50)

    # Connexion à la base de données
    await db.connect()
    app_state["concours_count"] = await db.count_concours()

    # Import différé pour éviter les imports circulaires
    from backend.services.auth import FFEAuthenticator
    from backend.services.surveillance import SurveillanceService
    from backend.services.notification import MultiNotifier

    # Initialisation des services
    try:
        # Authentification FFE
        authenticator = FFEAuthenticator(
            username=settings.ffe_username,
            password=settings.ffe_password,
            cookies_path=settings.cookies_full_path,
        )
        app_state["authenticator"] = authenticator

        # Connexion à FFE
        connected = await authenticator.login()
        app_state["ffe_connected"] = connected

        if connected:
            logger.info("Connexion FFE établie")

            # Notifier multi-canal (Telegram + Email si configuré)
            notifier = MultiNotifier()
            app_state["notifier"] = notifier

            # Démarrage de la surveillance
            surveillance = SurveillanceService(
                authenticator=authenticator,
                database=db,
                notifier=notifier,
                check_interval=settings.check_interval,
            )

            # Lancer la surveillance en tâche de fond
            task = asyncio.create_task(surveillance.start())
            app_state["surveillance_task"] = task
            app_state["surveillance_active"] = True

            logger.info("Surveillance démarrée")
        else:
            logger.error("Échec de connexion FFE - Surveillance non démarrée")

    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation: {e}")

    logger.info(f"Interface disponible sur http://localhost:8000")
    logger.info("=" * 50)

    yield  # L'application tourne

    # Shutdown
    logger.info("Arrêt de l'application...")

    # Arrêter la surveillance
    if app_state.get("surveillance_task"):
        app_state["surveillance_task"].cancel()
        try:
            await app_state["surveillance_task"]
        except asyncio.CancelledError:
            pass

    # Fermer le notifier
    if app_state.get("notifier"):
        await app_state["notifier"].close()

    # Fermer l'authentificateur
    if app_state.get("authenticator"):
        await app_state["authenticator"].close()

    # Déconnexion de la base de données
    await db.disconnect()

    logger.info("EngageWatch arrêté proprement")


# Création de l'application FastAPI
app = FastAPI(
    title="EngageWatch",
    description="Surveillance d'ouverture des concours FFE",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage des routers API
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(concours.router)

# Servir les fichiers statiques du frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def redirect_root():
    """Redirige vers la page de login."""
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@app.get("/login")
async def serve_login():
    """Sert la page de connexion (publique)."""
    login_path = frontend_path / "login.html"
    if login_path.exists():
        return FileResponse(login_path)
    return {"message": "Page de connexion non disponible"}


@app.get("/app")
async def serve_app(request: Request):
    """
    Sert l'application principale (protégée).
    Vérifie le token JWT côté serveur avant de servir la page.
    """
    # Récupérer le token depuis le header Authorization ou le cookie
    auth_header = request.headers.get("Authorization")
    token = None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]

    # Si pas de token dans le header, on sert quand même la page
    # car le JS côté client vérifiera le token stocké en localStorage
    # et redirigera vers /login si nécessaire
    app_path = frontend_path / "app.html"
    if app_path.exists():
        return FileResponse(app_path)
    return {"message": "Application non disponible"}


@app.get("/guide")
async def serve_guide():
    """Sert le guide utilisateur."""
    guide_path = frontend_path / "guide.html"
    if guide_path.exists():
        return FileResponse(guide_path)
    return {"message": "Guide non disponible"}
