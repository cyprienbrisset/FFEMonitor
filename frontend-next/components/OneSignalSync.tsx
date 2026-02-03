'use client'

import { useEffect, useRef } from 'react'
import { updateProfile } from '@/lib/api'

// Note: Window.OneSignalDeferred est déjà déclaré dans ServiceWorkerRegistration.tsx

interface OneSignalSyncProps {
  accessToken?: string
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
    console.log('[OneSignal] Player ID synchronisé avec le backend')
  } catch (error) {
    console.error('[OneSignal] Erreur sync backend:', error)
  }
}
