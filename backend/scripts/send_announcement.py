"""
Script pour envoyer un email d'annonce à tous les utilisateurs inscrits.
Usage: python -m backend.scripts.send_announcement
"""

import asyncio
import sys
import os

# Ajouter le dossier racine au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import httpx
from backend.config import settings
from backend.supabase_client import supabase


RESEND_API_URL = "https://api.resend.com/emails"

SUBJECT = "🐴 Hoofs — Les notifications email sont activées !"

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #FAF7F2;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #FAF7F2; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="100%" style="max-width: 500px;" cellpadding="0" cellspacing="0">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 32px; text-align: center; border-radius: 24px 24px 0 0; background-color: #FFFFFF;">
                            <div style="font-size: 48px; margin-bottom: 8px;">🐴</div>
                            <h1 style="margin: 0; font-size: 24px; color: #2D2D2D; font-weight: 600;">
                                Notifications email activées !
                            </h1>
                        </td>
                    </tr>
                    <!-- Body -->
                    <tr>
                        <td style="padding: 32px; background-color: #FFFFFF;">
                            <p style="margin: 0 0 20px 0; font-size: 16px; color: #4A4A4A; line-height: 1.6;">
                                Bonjour,
                            </p>
                            <p style="margin: 0 0 20px 0; font-size: 16px; color: #4A4A4A; line-height: 1.6;">
                                Les <strong>notifications par email</strong> sont désormais actives sur Hoofs !
                                Vous recevrez un email dès l'ouverture des engagements d'un concours que vous surveillez.
                            </p>

                            <div style="background-color: #D4E4D1; padding: 20px; border-radius: 16px; margin: 24px 0;">
                                <p style="margin: 0 0 12px 0; font-size: 14px; color: #2D2D2D; font-weight: 600;">
                                    ✅ Ce qui fonctionne :
                                </p>
                                <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #4A4A4A; line-height: 1.8;">
                                    <li>Notifications email à l'ouverture des concours</li>
                                    <li>Notifications push sur iOS (mode PWA)</li>
                                    <li>Surveillance automatique de vos concours</li>
                                </ul>
                            </div>

                            <div style="background-color: #F0E8D0; padding: 20px; border-radius: 16px; margin: 24px 0;">
                                <p style="margin: 0 0 12px 0; font-size: 14px; color: #2D2D2D; font-weight: 600;">
                                    🔧 En cours d'amélioration :
                                </p>
                                <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #4A4A4A; line-height: 1.8;">
                                    <li>Notifications push sur navigateur web (desktop/Android)</li>
                                </ul>
                            </div>

                            <p style="margin: 24px 0 0 0; font-size: 16px; color: #4A4A4A; line-height: 1.6;">
                                Pour surveiller un concours, rendez-vous sur l'application et ajoutez son numéro.
                            </p>

                            <div style="text-align: center; margin-top: 32px;">
                                <a href="https://hoofs.fr/app"
                                   style="display: inline-block; padding: 14px 32px; background-color: #2D2D2D; color: #FAF7F2; text-decoration: none; border-radius: 100px; font-weight: 600; font-size: 15px;">
                                    Ouvrir Hoofs
                                </a>
                            </div>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 32px; background-color: #FAF7F2; text-align: center; border-radius: 0 0 24px 24px;">
                            <p style="margin: 0; font-size: 12px; color: #8B8B8B;">
                                🐴 Hoofs — Surveillance des concours FFE
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

TEXT_CONTENT = """Bonjour,

Les notifications par email sont désormais actives sur Hoofs !
Vous recevrez un email dès l'ouverture des engagements d'un concours que vous surveillez.

Ce qui fonctionne :
- Notifications email à l'ouverture des concours
- Notifications push sur iOS (mode PWA)
- Surveillance automatique de vos concours

En cours d'amélioration :
- Notifications push sur navigateur web (desktop/Android)

Rendez-vous sur https://hoofs.fr/app pour surveiller vos concours.

Hoofs — Surveillance des concours FFE
"""


async def get_all_user_emails() -> list[str]:
    """Récupère tous les emails des utilisateurs inscrits via Supabase."""
    if not supabase.service_client:
        print("ERREUR: Supabase service client non disponible")
        return []

    response = supabase.service_client.table("profiles").select("email").execute()
    emails = [row["email"] for row in (response.data or []) if row.get("email")]
    return emails


async def send_email(client: httpx.AsyncClient, to_email: str) -> bool:
    """Envoie l'email d'annonce à un utilisateur."""
    payload = {
        "from": settings.resend_from_email,
        "to": [to_email],
        "subject": SUBJECT,
        "html": HTML_CONTENT,
        "text": TEXT_CONTENT,
    }

    response = await client.post(
        RESEND_API_URL,
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
    )

    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ {to_email} (id: {result.get('id')})")
        return True
    else:
        print(f"  ❌ {to_email} — Erreur {response.status_code}: {response.text}")
        return False


async def main():
    # Vérifications
    if not settings.resend_configured:
        print("ERREUR: RESEND_API_KEY non configuré dans .env")
        return

    if not settings.supabase_configured:
        print("ERREUR: Supabase non configuré dans .env")
        return

    # Récupérer les emails
    print("Récupération des utilisateurs depuis Supabase...")
    emails = await get_all_user_emails()

    if not emails:
        print("Aucun utilisateur trouvé.")
        return

    print(f"\n{len(emails)} utilisateur(s) trouvé(s):")
    for email in emails:
        print(f"  - {email}")

    # Confirmation
    print(f"\nSujet: {SUBJECT}")
    confirm = input(f"\nEnvoyer l'email à {len(emails)} utilisateur(s) ? (oui/non): ")
    if confirm.lower() not in ("oui", "o", "yes", "y"):
        print("Annulé.")
        return

    # Envoi
    print("\nEnvoi en cours...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        success_count = 0
        for email in emails:
            if await send_email(client, email):
                success_count += 1
            # Petit délai pour éviter le rate limiting Resend
            await asyncio.sleep(0.5)

    print(f"\nTerminé: {success_count}/{len(emails)} emails envoyés avec succès.")


if __name__ == "__main__":
    asyncio.run(main())
