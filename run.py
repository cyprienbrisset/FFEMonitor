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


def check_env_file():
    """Vérifie que le fichier .env existe."""
    env_file = root_dir / ".env"
    env_example = root_dir / ".env.example"

    if not env_file.exists():
        print("=" * 50)
        print("ERREUR: Fichier .env manquant")
        print("=" * 50)
        print()
        print("Créez un fichier .env à partir du template:")
        print(f"  cp {env_example} {env_file}")
        print()
        print("Puis remplissez vos identifiants FFE et Telegram.")
        print()
        sys.exit(1)


def check_dependencies():
    """Vérifie que les dépendances sont installées."""
    try:
        import fastapi
        import uvicorn
        import playwright
        import aiosqlite
        import telegram
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

    check_env_file()
    check_dependencies()

    print()
    print("=" * 50)
    print("  EngageWatch - Surveillance Concours FFE")
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
