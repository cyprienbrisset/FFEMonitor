'use client'

import { useEffect, useRef } from 'react'
import { updateProfile } from '@/lib/api'

// Note: Window.OneSignalDeferred est déjà déclaré dans ServiceWorkerRegistration.tsx

interface OneSignalSyncProps {
  accessToken?: string
}

// Helpers pour détecter iOS et PWA
export function isIOS(): boolean {
  if (typeof window === 'undefined') return false
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as any).MSStream
}

export function isPWA(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as any).standalone === true
}

export function isPushSupported(): boolean {
  if (typeof window === 'undefined') return false

  // iOS Safari ne supporte pas les push notifications du tout
  if (isIOS() && !isPWA()) {
    return false
  }

  // iOS PWA supporte les push depuis iOS 16.4
  // On vérifie simplement si l'API est disponible
  return 'Notification' in window && 'serviceWorker' in navigator
}

export function getPushStatus(): 'supported' | 'ios-browser' | 'ios-pwa' | 'unsupported' {
  if (typeof window === 'undefined') return 'unsupported'

  if (isIOS()) {
    if (isPWA()) {
      return 'ios-pwa'
    }
    return 'ios-browser'
  }

  if ('Notification' in window && 'serviceWorker' in navigator) {
    return 'supported'
  }

  return 'unsupported'
}

export async function requestPushPermission(): Promise<boolean> {
  if (!isPushSupported()) return false

  try {
    const permission = await Notification.requestPermission()
    return permission === 'granted'
  } catch (error) {
    console.error('[Push] Permission request failed:', error)
    return false
  }
}

export function OneSignalSync({ accessToken }: OneSignalSyncProps) {
  const hasRegistered = useRef(false)

  useEffect(() => {
    if (!accessToken || hasRegistered.current) return

    // Attendre que OneSignal soit chargé
    if (typeof window !== 'undefined' && window.OneSignalDeferred) {
      window.OneSignalDeferred.push(async (OneSignalUnknown: unknown) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const OneSignal = OneSignalUnknown as any
        try {
          // Récupérer le subscription ID actuel
          const subscriptionId = await OneSignal.User?.PushSubscription?.id

          if (subscriptionId) {
            console.log('[OneSignal] Subscription ID trouvé:', subscriptionId)
            await syncSubscriptionId(subscriptionId, accessToken)
            hasRegistered.current = true
          }

          // Écouter les changements de subscription (quand l'utilisateur accepte/refuse)
          OneSignal.User?.PushSubscription?.addEventListener('change', async (event: { current?: { id?: string } }) => {
            const newId = event.current?.id
            if (newId) {
              console.log('[OneSignal] Nouveau subscription ID:', newId)
              await syncSubscriptionId(newId, accessToken)
            }
          })
        } catch (error) {
          console.error('[OneSignal] Erreur sync:', error)
        }
      })
    }
  }, [accessToken])

  return null
}

async function syncSubscriptionId(subscriptionId: string, accessToken: string) {
  try {
    await updateProfile({ onesignal_player_id: subscriptionId }, accessToken)
    console.log('[OneSignal] Player ID synchronisé avec le backend:', subscriptionId)
    return true
  } catch (error) {
    console.error('[OneSignal] Erreur sync backend:', error)
    return false
  }
}

// Force sync OneSignal subscription ID to backend
export async function forceOneSignalSync(accessToken: string): Promise<{ success: boolean; message: string }> {
  if (typeof window === 'undefined' || !window.OneSignalDeferred) {
    return { success: false, message: 'OneSignal non disponible' }
  }

  return new Promise((resolve) => {
    window.OneSignalDeferred!.push(async (OneSignal: any) => {
      try {
        // Get current subscription
        const subscriptionId = await OneSignal.User?.PushSubscription?.id
        console.log('[OneSignal] Force sync - subscription ID:', subscriptionId)

        if (!subscriptionId) {
          // Check if permission is granted
          const permission = await OneSignal.Notifications?.permission
          console.log('[OneSignal] Permission status:', permission)

          if (permission !== true) {
            resolve({ success: false, message: 'Notifications non autorisées. Cliquez sur "Activer les notifications push".' })
            return
          }

          // Permission granted but no subscription ID - try to opt in
          try {
            await OneSignal.User?.PushSubscription?.optIn()
            // Wait a bit and try again
            await new Promise(r => setTimeout(r, 1000))
            const newId = await OneSignal.User?.PushSubscription?.id
            if (newId) {
              const synced = await syncSubscriptionId(newId, accessToken)
              resolve({ success: synced, message: synced ? 'Notifications activées et synchronisées !' : 'Erreur de synchronisation' })
              return
            }
          } catch (e) {
            console.error('[OneSignal] OptIn error:', e)
          }

          resolve({ success: false, message: 'Impossible d\'obtenir l\'ID de notification. Essayez de recharger la page.' })
          return
        }

        // Sync to backend
        const synced = await syncSubscriptionId(subscriptionId, accessToken)
        resolve({ success: synced, message: synced ? 'Notifications synchronisées !' : 'Erreur de synchronisation avec le serveur' })
      } catch (error: any) {
        console.error('[OneSignal] Force sync error:', error)
        resolve({ success: false, message: error.message || 'Erreur OneSignal' })
      }
    })
  })
}
