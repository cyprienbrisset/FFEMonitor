#!/bin/bash
# Restart FFE Monitor

echo "🛑 Arrêt de l'application..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

sleep 1

echo "🚀 Démarrage de FFE Monitor..."
nohup python run.py > /tmp/ffem.log 2>&1 &

sleep 3

# Vérifier que l'app tourne
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Application démarrée sur http://localhost:8000"
else
    echo "❌ Erreur au démarrage. Logs:"
    tail -20 /tmp/ffem.log
fi
