# ============================================
# EngageWatch - Dockerfile
# Surveillance d'ouverture des concours FFE
# ============================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="EngageWatch"
LABEL description="Surveillance automatique des concours FFE"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système pour Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Dépendances Playwright/Chromium
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    # Utilitaires
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Installer Playwright et Chromium
RUN playwright install chromium \
    && playwright install-deps chromium

# Copier le code source
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY run.py .

# Créer le répertoire data avec les bonnes permissions
RUN mkdir -p /app/data && chmod 755 /app/data

# Volume pour la persistance des données
VOLUME ["/app/data"]

# Port exposé
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Commande de démarrage
CMD ["python", "run.py"]
