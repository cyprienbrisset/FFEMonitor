'use client'

import { useEffect } from 'react'

declare global {
  interface Window {
    OneSignalDeferred?: Array<(OneSignal: unknown) => void>;
  }
}

export function ServiceWorkerRegistration() {
  useEffect(() => {
    // OneSignal gère l'enregistrement de /sw.js (configuré dans layout.tsx).
    // Ce composant sert uniquement de fallback si OneSignal n'est pas disponible.
    if ('serviceWorker' in navigator) {
      const timeout = setTimeout(async () => {
        try {
          const registrations = await navigator.serviceWorker.getRegistrations()

          // Nettoyer l'ancien OneSignalSDKWorker.js (migration)
          for (const reg of registrations) {
            if (reg.active?.scriptURL?.includes('OneSignalSDKWorker')) {
              console.log('[App] Suppression ancien SW OneSignal:', reg.active.scriptURL)
              await reg.unregister()
            }
          }

          const hasSwRegistration = registrations.some(
            (r) => r.active?.scriptURL?.includes('/sw.js')
          )
          if (!hasSwRegistration) {
            // OneSignal n'a pas enregistré le SW, on le fait nous-mêmes
            const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' })
            console.log('[App] Service Worker enregistré (fallback):', reg.scope)
          } else {
            console.log('[App] Service Worker déjà enregistré par OneSignal')
          }
        } catch (error) {
          console.error('[App] Erreur enregistrement SW:', error)
        }
      }, 3000) // Laisser le temps à OneSignal d'enregistrer /sw.js

      return () => clearTimeout(timeout)
    }
  }, [])

  return null
}
