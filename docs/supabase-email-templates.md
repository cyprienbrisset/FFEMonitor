# Templates Email Supabase pour Hoofs

Copie-colle chaque template dans Supabase Dashboard → Authentication → Email Templates

---

## 1. Confirm sign up

**Subject:** `Confirmez votre inscription à Hoofs`

```html
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
                <table width="100%" style="max-width: 500px; background-color: #FFFFFF; border-radius: 24px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06);" cellpadding="0" cellspacing="0">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #D4E4D120, #D4E4D140); padding: 32px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 8px;">🐴</div>
                            <h1 style="margin: 0; font-size: 24px; color: #2D2D2D; font-weight: 600;">Bienvenue sur Hoofs !</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px; background-color: #FFFFFF;">
                            <p style="margin: 0 0 24px 0; font-size: 16px; color: #4A4A4A; line-height: 1.6; text-align: center;">
                                Confirmez votre adresse email pour activer votre compte et commencer à surveiller vos concours.
                            </p>
                            <a href="{{ .ConfirmationURL }}" style="display: block; width: 100%; padding: 16px; background-color: #2D2D2D; color: #FFFFFF; text-decoration: none; border-radius: 100px; text-align: center; font-weight: 600; font-size: 16px; box-sizing: border-box;">
                                Confirmer mon email →
                            </a>
                            <p style="margin: 24px 0 0 0; font-size: 13px; color: #8B8B8B; text-align: center; line-height: 1.5;">
                                Si vous n'avez pas créé de compte sur Hoofs, ignorez cet email.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 32px; background-color: #FAF7F2; text-align: center;">
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
```

---

## 2. Invite user

**Subject:** `Vous êtes invité à rejoindre Hoofs`

```html
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
                <table width="100%" style="max-width: 500px; background-color: #FFFFFF; border-radius: 24px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06);" cellpadding="0" cellspacing="0">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #E8DFD420, #E8DFD440); padding: 32px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 8px;">✉️</div>
                            <h1 style="margin: 0; font-size: 24px; color: #2D2D2D; font-weight: 600;">Vous êtes invité !</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px; background-color: #FFFFFF;">
                            <p style="margin: 0 0 24px 0; font-size: 16px; color: #4A4A4A; line-height: 1.6; text-align: center;">
                                Vous avez été invité à rejoindre Hoofs, l'outil de surveillance des concours équestres FFE.
                            </p>
                            <a href="{{ .ConfirmationURL }}" style="display: block; width: 100%; padding: 16px; background-color: #2D2D2D; color: #FFFFFF; text-decoration: none; border-radius: 100px; text-align: center; font-weight: 600; font-size: 16px; box-sizing: border-box;">
                                Accepter l'invitation →
                            </a>
                            <p style="margin: 24px 0 0 0; font-size: 13px; color: #8B8B8B; text-align: center; line-height: 1.5;">
                                Ce lien expire dans 24 heures.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 32px; background-color: #FAF7F2; text-align: center;">
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
```

---

## 3. Magic link

**Subject:** `Votre lien de connexion Hoofs`

```html
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
                <table width="100%" style="max-width: 500px; background-color: #FFFFFF; border-radius: 24px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06);" cellpadding="0" cellspacing="0">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #7090C020, #7090C040); padding: 32px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 8px;">🔗</div>
                            <h1 style="margin: 0; font-size: 24px; color: #2D2D2D; font-weight: 600;">Connexion rapide</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px; background-color: #FFFFFF;">
                            <p style="margin: 0 0 24px 0; font-size: 16px; color: #4A4A4A; line-height: 1.6; text-align: center;">
                                Cliquez sur le bouton ci-dessous pour vous connecter instantanément à Hoofs.
                            </p>
                            <a href="{{ .ConfirmationURL }}" style="display: block; width: 100%; padding: 16px; background-color: #2D2D2D; color: #FFFFFF; text-decoration: none; border-radius: 100px; text-align: center; font-weight: 600; font-size: 16px; box-sizing: border-box;">
                                Se connecter →
                            </a>
                            <p style="margin: 24px 0 0 0; font-size: 13px; color: #8B8B8B; text-align: center; line-height: 1.5;">
                                Ce lien est valable 1 heure et ne peut être utilisé qu'une seule fois.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 32px; background-color: #FAF7F2; text-align: center;">
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
```

---

## 4. Change email address

**Subject:** `Confirmez votre nouvelle adresse email`

```html
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
                <table width="100%" style="max-width: 500px; background-color: #FFFFFF; border-radius: 24px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06);" cellpadding="0" cellspacing="0">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #C4A35A20, #C4A35A40); padding: 32px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 8px;">📧</div>
                            <h1 style="margin: 0; font-size: 24px; color: #2D2D2D; font-weight: 600;">Nouvelle adresse email</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px; background-color: #FFFFFF;">
                            <p style="margin: 0 0 24px 0; font-size: 16px; color: #4A4A4A; line-height: 1.6; text-align: center;">
                                Vous avez demandé à changer votre adresse email. Cliquez ci-dessous pour confirmer cette nouvelle adresse.
                            </p>
                            <a href="{{ .ConfirmationURL }}" style="display: block; width: 100%; padding: 16px; background-color: #2D2D2D; color: #FFFFFF; text-decoration: none; border-radius: 100px; text-align: center; font-weight: 600; font-size: 16px; box-sizing: border-box;">
                                Confirmer le changement →
                            </a>
                            <p style="margin: 24px 0 0 0; font-size: 13px; color: #8B8B8B; text-align: center; line-height: 1.5;">
                                Si vous n'avez pas demandé ce changement, ignorez cet email.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 32px; background-color: #FAF7F2; text-align: center;">
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
```

---

## 5. Reset password

**Subject:** `Réinitialisez votre mot de passe Hoofs`

```html
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
                <table width="100%" style="max-width: 500px; background-color: #FFFFFF; border-radius: 24px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06);" cellpadding="0" cellspacing="0">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #E8828220, #E8828240); padding: 32px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 8px;">🔐</div>
                            <h1 style="margin: 0; font-size: 24px; color: #2D2D2D; font-weight: 600;">Mot de passe oublié ?</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px; background-color: #FFFFFF;">
                            <p style="margin: 0 0 24px 0; font-size: 16px; color: #4A4A4A; line-height: 1.6; text-align: center;">
                                Pas de souci ! Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe.
                            </p>
                            <a href="{{ .ConfirmationURL }}" style="display: block; width: 100%; padding: 16px; background-color: #2D2D2D; color: #FFFFFF; text-decoration: none; border-radius: 100px; text-align: center; font-weight: 600; font-size: 16px; box-sizing: border-box;">
                                Réinitialiser le mot de passe →
                            </a>
                            <p style="margin: 24px 0 0 0; font-size: 13px; color: #8B8B8B; text-align: center; line-height: 1.5;">
                                Ce lien expire dans 1 heure. Si vous n'avez pas fait cette demande, ignorez cet email.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 32px; background-color: #FAF7F2; text-align: center;">
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
```

---

## 6. Reauthentication (OTP)

**Subject:** `Votre code de vérification Hoofs`

```html
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
                <table width="100%" style="max-width: 500px; background-color: #FFFFFF; border-radius: 24px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06);" cellpadding="0" cellspacing="0">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #6B9B7A20, #6B9B7A40); padding: 32px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 8px;">🛡️</div>
                            <h1 style="margin: 0; font-size: 24px; color: #2D2D2D; font-weight: 600;">Vérification requise</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px; background-color: #FFFFFF;">
                            <p style="margin: 0 0 24px 0; font-size: 16px; color: #4A4A4A; line-height: 1.6; text-align: center;">
                                Pour confirmer cette action, entrez le code ci-dessous dans l'application :
                            </p>
                            <div style="background-color: #FAF7F2; border-radius: 16px; padding: 24px; text-align: center; margin-bottom: 24px;">
                                <span style="font-size: 32px; font-weight: 700; color: #2D2D2D; letter-spacing: 8px; font-family: monospace;">{{ .Token }}</span>
                            </div>
                            <p style="margin: 0; font-size: 13px; color: #8B8B8B; text-align: center; line-height: 1.5;">
                                Ce code expire dans 10 minutes. Si vous n'avez pas initié cette action, changez votre mot de passe immédiatement.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 32px; background-color: #FAF7F2; text-align: center;">
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
```

---

## Récapitulatif des sujets

| Template | Subject |
|----------|---------|
| Confirm sign up | `Confirmez votre inscription à Hoofs` |
| Invite user | `Vous êtes invité à rejoindre Hoofs` |
| Magic link | `Votre lien de connexion Hoofs` |
| Change email | `Confirmez votre nouvelle adresse email` |
| Reset password | `Réinitialisez votre mot de passe Hoofs` |
| Reauthentication | `Votre code de vérification Hoofs` |
