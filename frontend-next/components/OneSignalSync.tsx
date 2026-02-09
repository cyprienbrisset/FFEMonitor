'use client'

import { useEffect, useRef } from 'react'
import { updateProfile } from '@/lib/api'

// Note: Window.OneSignalDeferred est déjà déclaré dans ServiceWorkerRegistration.tsx

interface OneSignalSyncProps {
  accessToken?: string
  userId?: string
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

// Poll for OneSignal subscription ID — OneSignal needs time to register with the push service
// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function waitForSubscriptionId(OneSignal: any, maxAttempts = 15, intervalMs = 800): Promise<string | null> {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const id = await OneSignal.User?.PushSubscription?.id
      if (id) {
        console.log(`[OneSignal] Subscription ID obtained after ${i + 1} attempt(s):`, id)
        return id
      }
    } catch (e) {
      console.warn('[OneSignal] Error checking subscription ID (attempt', i + 1, '):', e)
    }
    if (i < maxAttempts - 1) {
      await new Promise(r => setTimeout(r, intervalMs))
    }
  }
  return null
}

export function OneSignalSync({ accessToken, userId }: OneSignalSyncProps) {
  const hasRegistered = useRef(false)

  useEffect(() => {
    if (!accessToken || hasRegistered.current) return

    // Attendre que OneSignal soit chargé
    if (typeof window !== 'undefined' && window.OneSignalDeferred) {
      window.OneSignalDeferred.push(async (OneSignalUnknown: unknown) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const OneSignal = OneSignalUnknown as any
        try {
          // Diagnostic complet
          const onesignalId = await OneSignal.User?.onesignalId
          const subId = await OneSignal.User?.PushSubscription?.id
          const subToken = await OneSignal.User?.PushSubscription?.token
          const subOptedIn = await OneSignal.User?.PushSubscription?.optedIn
          const permission = await OneSignal.Notifications?.permission
          console.log('[OneSignal] === DIAGNOSTIC ===')
          console.log('[OneSignal] onesignalId:', onesignalId)
          console.log('[OneSignal] subscription.id:', subId)
          console.log('[OneSignal] subscription.token:', subToken ? subToken.substring(0, 30) + '...' : null)
          console.log('[OneSignal] subscription.optedIn:', subOptedIn)
          console.log('[OneSignal] notification.permission:', permission)

          // Lier l'utilisateur Supabase à OneSignal via external_id
          if (userId) {
            console.log('[OneSignal] Login avec external_id:', userId)
            await OneSignal.login(userId)
            // Re-check after login
            const newOsId = await OneSignal.User?.onesignalId
            console.log('[OneSignal] onesignalId après login:', newOsId)
          }

          // Récupérer le subscription ID — avec polling si nécessaire
          let subscriptionId = await OneSignal.User?.PushSubscription?.id

          if (!subscriptionId) {
            if (permission) {
              console.log('[OneSignal] Permission granted but no subscription ID yet, trying opt-in + polling...')
              try { await OneSignal.User?.PushSubscription?.optIn() } catch (e) {
                console.log('[OneSignal] OptIn attempt (may be normal):', e)
              }
              subscriptionId = await waitForSubscriptionId(OneSignal, 10, 1000)
            }
          }

          if (subscriptionId) {
            console.log('[OneSignal] Subscription ID trouvé:', subscriptionId)
            await syncSubscriptionId(subscriptionId, accessToken)
            hasRegistered.current = true
          } else {
            console.log('[OneSignal] No subscription ID available (permission not granted or pending)')
          }

          // Écouter les changements de subscription (quand l'utilisateur accepte/refuse)
          OneSignal.User?.PushSubscription?.addEventListener('change', async (event: { current?: { id?: string } }) => {
            const newId = event.current?.id
            if (newId) {
              console.log('[OneSignal] Nouveau subscription ID (change event):', newId)
              await syncSubscriptionId(newId, accessToken)
              hasRegistered.current = true
            }
          })
        } catch (error) {
          console.error('[OneSignal] Erreur sync:', error)
        }
      })
    }
  }, [accessToken, userId])

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

// Force sync OneSignal subscription ID to backend (with robust polling)
export async function forceOneSignalSync(accessToken: string): Promise<{ success: boolean; message: string }> {
  if (typeof window === 'undefined' || !window.OneSignalDeferred) {
    return { success: false, message: 'OneSignal non disponible. Rechargez la page.' }
  }

  return new Promise((resolve) => {
    window.OneSignalDeferred!.push(async (OneSignal: any) => {
      try {
        // Get current subscription
        let subscriptionId = await OneSignal.User?.PushSubscription?.id
        console.log('[OneSignal] Force sync - subscription ID:', subscriptionId)

        if (!subscriptionId) {
          // Check if permission is granted
          const permission = await OneSignal.Notifications?.permission
          console.log('[OneSignal] Permission status:', permission)

          if (permission !== true) {
            resolve({ success: false, message: 'Notifications non autorisées. Cliquez sur "Activer les notifications push".' })
            return
          }

          // Permission granted but no subscription ID — try opt-in + poll
          console.log('[OneSignal] Permission OK, attempting opt-in + polling...')
          try {
            await OneSignal.User?.PushSubscription?.optIn()
          } catch (e) {
            console.log('[OneSignal] OptIn attempt (may be normal):', e)
          }

          subscriptionId = await waitForSubscriptionId(OneSignal, 15, 800)

          if (!subscriptionId) {
            resolve({ success: false, message: 'Impossible d\'obtenir l\'ID de notification après plusieurs tentatives. Rechargez la page.' })
            return
          }
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

// Request permission + opt-in + poll + sync — all in one robust flow
export async function requestAndSyncPush(accessToken: string): Promise<{
  success: boolean
  message: string
  permission: NotificationPermission
  subscriptionId: string | null
}> {
  if (typeof window === 'undefined' || !window.OneSignalDeferred) {
    return { success: false, message: 'OneSignal non chargé. Rechargez la page.', permission: 'default', subscriptionId: null }
  }

  return new Promise((resolve) => {
    window.OneSignalDeferred!.push(async (OneSignal: any) => {
      try {
        // 1. Request permission via OneSignal
        console.log('[Push] Requesting permission via OneSignal...')
        await OneSignal.Notifications.requestPermission()

        const permission = Notification.permission
        console.log('[Push] Permission result:', permission)

        if (permission !== 'granted') {
          resolve({
            success: false,
            message: permission === 'denied'
              ? 'Notifications bloquées. Cliquez sur le cadenas dans la barre d\'adresse → Notifications → Autoriser.'
              : 'Permission non accordée. Réessayez.',
            permission,
            subscriptionId: null,
          })
          return
        }

        // 2. Opt-in to create subscription
        console.log('[Push] Opting in to push subscription...')
        try {
          await OneSignal.User.PushSubscription.optIn()
        } catch (e) {
          console.log('[Push] OptIn attempt (may be normal):', e)
        }

        // 3. Poll for subscription ID
        console.log('[Push] Polling for subscription ID...')
        const subscriptionId = await waitForSubscriptionId(OneSignal, 15, 800)

        if (!subscriptionId) {
          resolve({
            success: false,
            message: 'Permission OK mais ID de souscription non créé. Rechargez la page et réessayez.',
            permission,
            subscriptionId: null,
          })
          return
        }

        // 4. Sync to backend
        console.log('[Push] Syncing subscription ID to backend...')
        const synced = await syncSubscriptionId(subscriptionId, accessToken)
        resolve({
          success: synced,
          message: synced ? 'Notifications push activées !' : 'Erreur de synchronisation avec le serveur.',
          permission,
          subscriptionId,
        })
      } catch (error: any) {
        console.error('[Push] requestAndSyncPush error:', error)
        resolve({
          success: false,
          message: error.message || 'Erreur inconnue',
          permission: typeof Notification !== 'undefined' ? Notification.permission : 'default',
          subscriptionId: null,
        })
      }
    })
  })
}
