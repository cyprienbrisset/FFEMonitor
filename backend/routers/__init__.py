# Hoofs Routers

from backend.routers import auth, health, concours, stats, calendar

# Import conditionnel de subscriptions (nécessite Supabase)
try:
    from backend.routers import subscriptions
except ImportError:
    subscriptions = None

__all__ = ["auth", "health", "concours", "stats", "calendar", "subscriptions"]
