// Supabase Edge Function pour envoyer des emails
// Utilise le service email intégré de Supabase (Resend sous le capot)

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY")

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
}

interface EmailRequest {
  to: string
  subject: string
  html: string
  text?: string
  type?: "test" | "concours"
  // Pour les notifications de concours
  concours?: {
    numero: number
    statut: string
    nom?: string
    lieu?: string
    date_debut?: string
    date_fin?: string
  }
}

function generateConcoursEmail(concours: EmailRequest["concours"]): { subject: string; html: string; text: string } {
  if (!concours) {
    return { subject: "", html: "", text: "" }
  }

  const { numero, statut, nom, lieu, date_debut, date_fin } = concours

  // Déterminer le type d'ouverture
  let emoji = "🔔"
  let type_ouverture = "Concours mis à jour"
  let color = "#C4A35A"

  if (statut === "engagement") {
    emoji = "🟢"
    type_ouverture = "Engagements ouverts"
    color = "#6B9B7A"
  } else if (statut === "demande") {
    emoji = "🔵"
    type_ouverture = "Demandes ouvertes"
    color = "#7090C0"
  }

  const titre = nom || `Concours #${numero}`
  const url = `https://ffecompet.ffe.com/concours/${numero}`

  const subject = `${emoji} ${type_ouverture} — ${titre}`

  const html = `
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
                <table width="100%" style="max-width: 500px;" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 24px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, ${color}20, ${color}40); padding: 32px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 8px;">${emoji}</div>
                            <h1 style="margin: 0; font-size: 24px; color: #2D2D2D; font-weight: 600;">${type_ouverture}</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px; background-color: #FFFFFF;">
                            <h2 style="margin: 0 0 16px 0; font-size: 20px; color: #2D2D2D;">${titre}</h2>
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                                <tr>
                                    <td style="padding: 8px 0; color: #8B8B8B; font-size: 14px;">Numéro</td>
                                    <td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; text-align: right; font-weight: 500;">#${numero}</td>
                                </tr>
                                ${lieu ? `<tr><td style="padding: 8px 0; color: #8B8B8B; font-size: 14px;">Lieu</td><td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; text-align: right;">${lieu}</td></tr>` : ""}
                                ${date_debut ? `<tr><td style="padding: 8px 0; color: #8B8B8B; font-size: 14px;">Date</td><td style="padding: 8px 0; color: #2D2D2D; font-size: 14px; text-align: right;">${date_debut}${date_fin ? ` - ${date_fin}` : ""}</td></tr>` : ""}
                            </table>
                            <a href="${url}" style="display: block; width: 100%; padding: 16px; background-color: #2D2D2D; color: #FFFFFF; text-decoration: none; border-radius: 100px; text-align: center; font-weight: 600; font-size: 16px; box-sizing: border-box;">
                                Accéder au concours →
                            </a>
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
</html>`

  const text = `
${type_ouverture} — ${titre}

Numéro: #${numero}
${lieu ? `Lieu: ${lieu}` : ""}
${date_debut ? `Date: ${date_debut}${date_fin ? ` - ${date_fin}` : ""}` : ""}

Accéder au concours: ${url}

---
🐴 Hoofs — Surveillance des concours FFE
`

  return { subject, html, text }
}

function generateTestEmail(): { subject: string; html: string; text: string } {
  const subject = "🐴 Hoofs — Test des notifications email"

  const html = `
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
                    <tr>
                        <td style="background: linear-gradient(135deg, #D4E4D120, #D4E4D140); padding: 32px; text-align: center; border-radius: 24px 24px 0 0; background-color: #FFFFFF;">
                            <div style="font-size: 48px; margin-bottom: 8px;">🐴</div>
                            <h1 style="margin: 0; font-size: 24px; color: #2D2D2D; font-weight: 600;">Test réussi !</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 32px; text-align: center; background-color: #FFFFFF;">
                            <p style="margin: 0 0 24px 0; font-size: 16px; color: #4A4A4A; line-height: 1.6;">
                                Les notifications email fonctionnent correctement.<br>
                                Vous recevrez un email à chaque ouverture de concours surveillé.
                            </p>
                            <div style="display: inline-block; padding: 12px 24px; background-color: #D4E4D1; color: #6B9B7A; border-radius: 100px; font-weight: 600; font-size: 14px;">
                                ✓ Configuration validée
                            </div>
                        </td>
                    </tr>
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
</html>`

  const text = "Test réussi ! Les notifications email fonctionnent correctement."

  return { subject, html, text }
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders })
  }

  try {
    // Vérifier la clé API Resend
    if (!RESEND_API_KEY) {
      console.error("RESEND_API_KEY not configured")
      return new Response(
        JSON.stringify({ success: false, error: "Email service not configured" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      )
    }

    const body: EmailRequest = await req.json()
    const { to, type, concours } = body
    let { subject, html, text } = body

    // Générer le contenu selon le type
    if (type === "test") {
      const generated = generateTestEmail()
      subject = generated.subject
      html = generated.html
      text = generated.text
    } else if (type === "concours" && concours) {
      const generated = generateConcoursEmail(concours)
      subject = generated.subject
      html = generated.html
      text = generated.text
    }

    // Valider les champs requis
    if (!to || !subject || !html) {
      return new Response(
        JSON.stringify({ success: false, error: "Missing required fields: to, subject, html" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      )
    }

    // Envoyer l'email via Resend
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${RESEND_API_KEY}`,
      },
      body: JSON.stringify({
        from: "Hoofs <notifications@hoofs.fr>",
        to: [to],
        subject,
        html,
        text,
      }),
    })

    const data = await res.json()

    if (res.ok) {
      console.log(`Email sent to ${to}, id: ${data.id}`)
      return new Response(
        JSON.stringify({ success: true, message: `Email envoyé à ${to}`, id: data.id }),
        { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      )
    } else {
      console.error("Resend error:", data)
      return new Response(
        JSON.stringify({ success: false, error: data.message || "Failed to send email" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      )
    }
  } catch (error) {
    console.error("Error:", error)
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    )
  }
})
