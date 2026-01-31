#!/usr/bin/env python3
"""
Script de lancement en mode DEMO de EngageWatch.
Permet de tester l'interface sans identifiants FFE/Telegram réels.
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire racine au path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Configurer des variables d'environnement de démo
os.environ["FFE_USERNAME"] = "demo@example.com"
os.environ["FFE_PASSWORD"] = "demo_password"
os.environ["TELEGRAM_BOT_TOKEN"] = "000000000:DEMO_TOKEN"
os.environ["TELEGRAM_CHAT_ID"] = "000000000"
os.environ["CHECK_INTERVAL"] = "10"
os.environ["LOG_LEVEL"] = "INFO"


def main():
    """Point d'entrée principal en mode démo."""
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    from backend.database import db
    from backend.routers import health, concours
    from backend.utils.logger import setup_logger

    # Setup logger
    setup_logger("engagewatch", "INFO")

    # Créer une app FastAPI simplifiée (sans authentification FFE)
    app = FastAPI(
        title="EngageWatch - DEMO",
        description="Mode démonstration - Sans connexion FFE",
        version="1.0.0-demo",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # État global simulé
    from backend.main import app_state
    app_state["ffe_connected"] = False
    app_state["surveillance_active"] = False
    app_state["concours_count"] = 0

    # Routers
    app.include_router(health.router)
    app.include_router(concours.router)

    # Frontend
    frontend_path = root_dir / "frontend"
    if frontend_path.exists():
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    async def serve_frontend():
        index_path = frontend_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"message": "Frontend non disponible"}

    @app.on_event("startup")
    async def startup():
        await db.connect()
        print()
        print("=" * 55)
        print("  EngageWatch - MODE DEMO")
        print("=" * 55)
        print()
        print("  Interface disponible sur: http://localhost:8000")
        print()
        print("  NOTE: La connexion FFE et les notifications")
        print("        sont désactivées en mode démo.")
        print()
        print("  Vous pouvez:")
        print("    - Ajouter des concours (stockés en base)")
        print("    - Voir l'interface utilisateur")
        print("    - Tester l'API")
        print()
        print("=" * 55)

    @app.on_event("shutdown")
    async def shutdown():
        await db.disconnect()

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
