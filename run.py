#!/usr/bin/env python3
"""
Script de lancement de EngageWatch.
Lance le serveur FastAPI avec uvicorn.
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))


def check_env_config():
    """Vérifie que la configuration est disponible (.env ou variables d'environnement)."""
    import os

    env_file = root_dir / ".env"
    env_example = root_dir / ".env.example"

    # Variables obligatoires
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_KEY", "ONESIGNAL_APP_ID", "ONESIGNAL_API_KEY"]

    # Si le fichier .env existe, c'est bon
    if env_file.exists():
        return

    # Sinon, vérifier que les variables d'environnement sont définies (mode Docker)
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        print("=" * 50)
        print("ERREUR: Configuration manquante")
        print("=" * 50)
        print()
        print("Variables manquantes:", ", ".join(missing_vars))
        print()
        print("Option 1 - Créez un fichier .env:")
        print(f"  cp {env_example} {env_file}")
        print()
        print("Option 2 - Définissez les variables d'environnement (Docker):")
        print("  Vérifiez votre docker-compose.yml ou .env sur l'hôte")
        print()
        sys.exit(1)

    print("Mode Docker détecté (variables d'environnement)")


def check_dependencies():
    """Vérifie que les dépendances sont installées."""
    try:
        import fastapi
        import uvicorn
        import playwright
        import aiosqlite
        import httpx
    except ImportError as e:
        print("=" * 50)
        print("ERREUR: Dépendances manquantes")
        print("=" * 50)
        print()
        print(f"Module manquant: {e.name}")
        print()
        print("Installez les dépendances avec:")
        print("  pip install -r requirements.txt")
        print()
        print("Puis installez Playwright:")
        print("  playwright install chromium")
        print()
        sys.exit(1)


def main():
    """Point d'entrée principal."""
    import uvicorn

    check_env_config()
    check_dependencies()

    print()
    print("=" * 50)
    print("  Hoofs - Surveillance Concours FFE")
    print("=" * 50)
    print()

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
