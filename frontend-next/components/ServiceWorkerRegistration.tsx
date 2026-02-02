'use client'

import { useEffect } from 'react'

declare global {
  interface Window {
    OneSignalDeferred?: Array<(OneSignal: unknown) => void>;
  }
}

export function ServiceWorkerRegistration() {
  useEffect(() => {
    // Si OneSignal est présent, il gère l'enregistrement du service worker
    // Sinon, on enregistre manuellement pour le support hors ligne
    if ('serviceWorker' in navigator) {
      // Attendre un peu pour voir si OneSignal est initialisé
      const timeout = setTimeout(() => {
        // Vérifier si OneSignal n'a pas déjà enregistré le service worker
        navigator.serviceWorker.getRegistration('/sw.js').then((registration) => {
          if (!registration) {
            // OneSignal n'a pas enregistré le SW, on le fait nous-mêmes
            navigator.serviceWorker
              .register('/sw.js', { scope: '/' })
              .then((reg) => {
                console.log('[App] Service Worker enregistré:', reg.scope)
              })
              .catch((error) => {
                console.error('[App] Erreur enregistrement SW:', error)
              })
          } else {
            console.log('[App] Service Worker déjà enregistré (OneSignal):', registration.scope)
          }
        })
      }, 2000) // Attendre 2 secondes pour laisser OneSignal s'initialiser

      return () => clearTimeout(timeout)
    }
  }, [])

  return null
}
