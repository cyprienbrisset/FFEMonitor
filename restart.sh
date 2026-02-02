#!/bin/bash
# Restart FFE Monitor (Backend + Frontend Next.js)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend-next"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

echo "🛑 Arrêt des applications..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 -ti:3001 | xargs kill -9 2>/dev/null || true

sleep 1

# Vérifier que le venv existe
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Environnement virtuel non trouvé: $VENV_PYTHON"
    echo "   Créez-le avec: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Vérifier que les dépendances frontend sont installées
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "📦 Installation des dépendances frontend..."
    (cd "$FRONTEND_DIR" && npm install)
fi

echo "🚀 Démarrage du Backend (port 8000)..."
nohup "$VENV_PYTHON" "$SCRIPT_DIR/run.py" > /tmp/ffem-backend.log 2>&1 &
BACKEND_PID=$!

sleep 3

echo "🚀 Démarrage du Frontend Next.js (port 3000)..."
(cd "$FRONTEND_DIR" && nohup npm run dev > /tmp/ffem-frontend.log 2>&1 &)

sleep 5

# Vérifier que les apps tournent
echo ""
echo "📊 État des services:"

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API:    http://localhost:8000"
else
    echo "❌ Backend API:    Erreur au démarrage"
    echo "   Logs: tail -f /tmp/ffem-backend.log"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend:       http://localhost:3000"
else
    echo "⏳ Frontend:       En cours de compilation..."
    echo "   Attendez quelques secondes puis accédez à http://localhost:3000"
    echo "   Logs: tail -f /tmp/ffem-frontend.log"
fi

echo ""
echo "📝 Logs disponibles:"
echo "   Backend:  tail -f /tmp/ffem-backend.log"
echo "   Frontend: tail -f /tmp/ffem-frontend.log"
