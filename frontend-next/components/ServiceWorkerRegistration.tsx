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
          const hasSwRegistration = registrations.some((r) => {
            const sw = r.active || r.installing || r.waiting
            return sw?.scriptURL?.includes('/sw.js')
          })
          if (!hasSwRegistration) {
            const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' })
            console.log('[App] Service Worker enregistré (fallback):', reg.scope)
          }
        } catch (error) {
          console.error('[App] Erreur enregistrement SW:', error)
        }
      }, 5000)

      return () => clearTimeout(timeout)
    }
  }, [])

  return null
}
