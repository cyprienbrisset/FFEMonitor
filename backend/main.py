"""
Point d'entrée de l'application FFE Monitor.
Configuration FastAPI et gestion du cycle de vie.
Utilise Supabase comme base de données unique.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse

from backend.config import settings
from backend.supabase_client import supabase
from backend.routers import health, concours, auth, stats, calendar, subscriptions
from backend.utils.logger import setup_logger, get_logger

# Configuration du logger principal
setup_logger("ffemonitor", settings.log_level)
logger = get_logger("main")

# État global de l'application (partagé entre modules)
app_state: dict = {
    "surveillance_active": False,
    "concours_count": 0,
    "surveillance_task": None,
    "notifier": None,
    "notification_worker_task": None,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    Initialise les services au démarrage et les ferme à l'arrêt.
    """
    logger.info("=" * 50)
    logger.info("FFE Monitor - Démarrage")
    logger.info("=" * 50)

    # Vérifier la configuration Supabase
    if not settings.supabase_configured:
        logger.error("Supabase non configuré ! Vérifiez les variables d'environnement.")
        raise RuntimeError("Supabase configuration missing")

    logger.info("Connexion Supabase établie")

    # Compter les concours existants
    all_concours = await supabase.get_all_concours()
    app_state["concours_count"] = len(all_concours)

    # Import différé pour éviter les imports circulaires
    from backend.services.surveillance import SurveillanceService
    from backend.services.notification import get_notification_dispatcher

    # Initialisation des services
    try:
        # Dispatcher de notifications OneSignal
        notifier = get_notification_dispatcher()
        app_state["notifier"] = notifier

        # Démarrer le worker de notifications
        notification_worker_task = asyncio.create_task(notifier.start_worker())
        app_state["notification_worker_task"] = notification_worker_task
        logger.info("Worker de notifications démarré")

        # Démarrage de la surveillance (mode scraper uniquement)
        surveillance = SurveillanceService(
            notifier=notifier,
            check_interval=settings.check_interval,
        )

        # Lancer la surveillance en tâche de fond
        task = asyncio.create_task(surveillance.start())
        app_state["surveillance_task"] = task
        app_state["surveillance_active"] = True

        logger.info("Surveillance démarrée (mode scraper)")

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

    # Arrêter le worker de notifications
    if app_state.get("notification_worker_task"):
        app_state["notification_worker_task"].cancel()
        try:
            await app_state["notification_worker_task"]
        except asyncio.CancelledError:
            pass

    # Fermer le notifier
    if app_state.get("notifier"):
        await app_state["notifier"].close()

    logger.info("FFE Monitor arrêté proprement")


# Création de l'application FastAPI
app = FastAPI(
    title="FFE Monitor",
    description="Surveillance d'ouverture des concours FFE",
    version="2.0.0",
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
app.include_router(stats.router)
app.include_router(calendar.router)
app.include_router(subscriptions.router)

# Servir les fichiers statiques du frontend (ancien frontend HTML)
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def redirect_root():
    """Redirige vers la page de login."""
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@app.get("/manifest.json")
async def serve_manifest():
    """Sert le manifest PWA."""
    manifest_path = frontend_path / "manifest.json"
    if manifest_path.exists():
        return FileResponse(manifest_path, media_type="application/manifest+json")
    return {"error": "Manifest non disponible"}


@app.get("/sw.js")
async def serve_service_worker():
    """Sert le Service Worker."""
    sw_path = frontend_path / "sw.js"
    if sw_path.exists():
        return FileResponse(
            sw_path,
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/"},
        )
    return {"error": "Service Worker non disponible"}


@app.get("/offline.html")
async def serve_offline():
    """Sert la page hors ligne."""
    offline_path = frontend_path / "offline.html"
    if offline_path.exists():
        return FileResponse(offline_path)
    return {"message": "Page hors ligne non disponible"}


@app.get("/login")
async def serve_login():
    """Sert la page de connexion avec injection de la config Supabase."""
    login_path = frontend_path / "login.html"
    if login_path.exists():
        # Lire le HTML et injecter la configuration Supabase
        with open(login_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Injecter les variables Supabase
        html_content = html_content.replace(
            "{{ supabase_url }}", settings.supabase_url or ""
        )
        html_content = html_content.replace(
            "{{ supabase_anon_key }}", settings.supabase_anon_key or ""
        )

        return HTMLResponse(content=html_content)
    return {"message": "Page de connexion non disponible"}


@app.get("/app")
async def serve_app(request: Request):
    """
    Sert l'application principale (protégée).
    Vérifie le token JWT côté serveur avant de servir la page.
    """
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
