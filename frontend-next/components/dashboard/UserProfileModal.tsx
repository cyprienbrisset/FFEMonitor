'use client'

import { useState, useEffect } from 'react'
import { User } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase/client'
import { testNotification, loadProfile, UserProfile } from '@/lib/api'
import { getPushStatus, requestPushPermission, isIOS, isPWA, forceOneSignalSync } from '@/components/OneSignalSync'

interface UserProfileModalProps {
  user: User
  accessToken?: string
  getAccessToken?: () => Promise<string | null>
  onClose: () => void
  onSignOut: () => void
}

type Tab = 'info' | 'security' | 'notifications'

const PLAN_LABELS: Record<string, { label: string; color: string }> = {
  free: { label: 'Gratuit', color: 'var(--gray)' },
  premium: { label: 'Premium', color: 'var(--warning)' },
  pro: { label: 'Pro', color: 'var(--success)' },
}

export function UserProfileModal({ user, accessToken, getAccessToken, onClose, onSignOut }: UserProfileModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>('info')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)

  // Edit states
  const [newEmail, setNewEmail] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState('')
  const [testingNotif, setTestingNotif] = useState<string | null>(null)
  const [notifPermission, setNotifPermission] = useState<NotificationPermission | 'unsupported'>('default')
  const [debugInfo, setDebugInfo] = useState<{
    isIOS: boolean
    isPWA: boolean
    permission: string
    oneSignalLoaded: boolean
    subscriptionId: string | null
  } | null>(null)

  // Check notification permission and gather debug info on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      if ('Notification' in window) {
        setNotifPermission(Notification.permission)
      } else {
        setNotifPermission('unsupported')
      }

      // Gather debug info
      const gatherDebugInfo = async () => {
        const info: typeof debugInfo = {
          isIOS: isIOS(),
          isPWA: isPWA(),
          permission: 'Notification' in window ? Notification.permission : 'unsupported',
          oneSignalLoaded: !!window.OneSignalDeferred,
          subscriptionId: null
        }

        // Try to get OneSignal subscription ID
        if (window.OneSignalDeferred) {
          window.OneSignalDeferred.push(async (OneSignal: any) => {
            try {
              const subId = await OneSignal.User?.PushSubscription?.id
              setDebugInfo(prev => prev ? { ...prev, subscriptionId: subId || 'non disponible' } : null)
            } catch (e) {
              setDebugInfo(prev => prev ? { ...prev, subscriptionId: 'erreur' } : null)
            }
          })
        }

        setDebugInfo(info)
      }

      gatherDebugInfo()
    }
  }, [])

  // Fetch profile on mount
  useEffect(() => {
    async function fetchProfile() {
      try {
        const data = await loadProfile(accessToken)
        setProfile(data)
      } catch (error) {
        console.error('Failed to load profile:', error)
      }
    }
    fetchProfile()
  }, [accessToken])

  // User plan from profile or default to free
  const userPlan = profile?.plan || 'free'
  const planInfo = PLAN_LABELS[userPlan] || PLAN_LABELS.free

  const supabase = createClient()

  const createdAt = user.created_at
    ? new Date(user.created_at).toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      })
    : '—'

  const lastSignIn = user.last_sign_in_at
    ? new Date(user.last_sign_in_at).toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—'

  const showMessage = (text: string, type: 'success' | 'error') => {
    setMessage({ text, type })
    setTimeout(() => setMessage(null), 5000)
  }

  const handleUpdateEmail = async () => {
    if (!newEmail) {
      showMessage('Veuillez entrer un nouvel email', 'error')
      return
    }

    setLoading(true)
    try {
      const { error } = await supabase.auth.updateUser({ email: newEmail })
      if (error) throw error
      showMessage('Un email de confirmation a été envoyé à votre nouvelle adresse', 'success')
      setNewEmail('')
    } catch (error: any) {
      showMessage(error.message || 'Erreur lors de la mise à jour', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdatePassword = async () => {
    if (!newPassword || !confirmPassword) {
      showMessage('Veuillez remplir tous les champs', 'error')
      return
    }
    if (newPassword !== confirmPassword) {
      showMessage('Les mots de passe ne correspondent pas', 'error')
      return
    }
    if (newPassword.length < 6) {
      showMessage('Le mot de passe doit contenir au moins 6 caractères', 'error')
      return
    }

    setLoading(true)
    try {
      const { error } = await supabase.auth.updateUser({ password: newPassword })
      if (error) throw error
      showMessage('Mot de passe mis à jour avec succès', 'success')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (error: any) {
      showMessage(error.message || 'Erreur lors de la mise à jour', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteAccount = async () => {
    if (deleteConfirm !== 'SUPPRIMER') {
      showMessage('Veuillez taper SUPPRIMER pour confirmer', 'error')
      return
    }

    setLoading(true)
    try {
      // Call backend to delete user data then delete auth account
      const response = await fetch('/api/user/delete', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      })

      if (!response.ok) {
        throw new Error('Erreur lors de la suppression')
      }

      // Sign out and close modal
      await supabase.auth.signOut()
      onSignOut()
    } catch (error: any) {
      showMessage(error.message || 'Erreur lors de la suppression', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleTestNotification = async (channel: 'telegram' | 'email' | 'push') => {
    setTestingNotif(channel)
    try {
      // Get fresh token to avoid expiration issues
      const token = getAccessToken ? await getAccessToken() : accessToken
      if (!token) {
        showMessage('Session expirée. Veuillez vous reconnecter.', 'error')
        return
      }

      // For push notifications, sync OneSignal ID first
      if (channel === 'push') {
        showMessage('Synchronisation en cours...', 'success')
        const syncResult = await forceOneSignalSync(token)
        if (!syncResult.success) {
          showMessage(syncResult.message, 'error')
          return
        }
      }

      const result = await testNotification(channel as any, token)
      showMessage(result.message || 'Notification envoyée !', result.success ? 'success' : 'error')
    } catch (error: any) {
      if (error.message?.includes('401') || error.message?.includes('expiré') || error.message?.includes('invalide')) {
        showMessage('Session expirée. Veuillez vous reconnecter.', 'error')
      } else {
        showMessage(error.message || 'Erreur lors du test', 'error')
      }
    } finally {
      setTestingNotif(null)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content profile-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>

        {/* Header */}
        <div className="profile-header">
          <div className="profile-avatar">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <div className="profile-title">
            <h2>Mon Profil</h2>
            <span className="profile-plan-badge" style={{ background: planInfo.color }}>
              {planInfo.label}
            </span>
          </div>
        </div>

        {/* Message */}
        {message && (
          <div className={`profile-message ${message.type}`}>
            {message.text}
          </div>
        )}

        {/* Tabs */}
        <div className="profile-tabs">
          <button
            className={`profile-tab ${activeTab === 'info' ? 'active' : ''}`}
            onClick={() => setActiveTab('info')}
          >
            Informations
          </button>
          <button
            className={`profile-tab ${activeTab === 'security' ? 'active' : ''}`}
            onClick={() => setActiveTab('security')}
          >
            Sécurité
          </button>
          <button
            className={`profile-tab ${activeTab === 'notifications' ? 'active' : ''}`}
            onClick={() => setActiveTab('notifications')}
          >
            Notifications
          </button>
        </div>

        {/* Tab Content */}
        <div className="profile-tab-content">
          {activeTab === 'info' && (
            <div className="profile-info">
              <div className="profile-field">
                <label>Email actuel</label>
                <span>{user.email || '—'}</span>
              </div>

              <div className="profile-field">
                <label>Abonnement</label>
                <span className="profile-plan" style={{ color: planInfo.color }}>
                  {planInfo.label}
                  {userPlan === 'free' && (
                    <a href="#upgrade" className="upgrade-link">Passer à Premium</a>
                  )}
                </span>
              </div>

              <div className="profile-field">
                <label>Membre depuis</label>
                <span>{createdAt}</span>
              </div>

              <div className="profile-field">
                <label>Dernière connexion</label>
                <span>{lastSignIn}</span>
              </div>

              <div className="profile-field">
                <label>Identifiant</label>
                <span className="profile-id">{user.id.slice(0, 8)}...{user.id.slice(-4)}</span>
              </div>

              <div className="profile-section">
                <h3>Modifier l'email</h3>
                <div className="profile-form">
                  <input
                    type="email"
                    placeholder="Nouvel email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    className="profile-input"
                  />
                  <button
                    className="btn-primary-small"
                    onClick={handleUpdateEmail}
                    disabled={loading}
                  >
                    {loading ? 'Envoi...' : 'Mettre à jour'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="profile-security">
              <div className="profile-section">
                <h3>Changer le mot de passe</h3>
                <div className="profile-form-vertical">
                  <input
                    type="password"
                    placeholder="Nouveau mot de passe"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="profile-input"
                  />
                  <input
                    type="password"
                    placeholder="Confirmer le mot de passe"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="profile-input"
                  />
                  <button
                    className="btn-primary-small"
                    onClick={handleUpdatePassword}
                    disabled={loading}
                  >
                    {loading ? 'Mise à jour...' : 'Changer le mot de passe'}
                  </button>
                </div>
              </div>

              <div className="profile-section danger-zone">
                <h3>Zone de danger</h3>
                <p className="danger-text">
                  La suppression de votre compte est irréversible. Toutes vos données seront perdues.
                </p>
                <div className="profile-form-vertical">
                  <input
                    type="text"
                    placeholder="Tapez SUPPRIMER pour confirmer"
                    value={deleteConfirm}
                    onChange={(e) => setDeleteConfirm(e.target.value)}
                    className="profile-input danger-input"
                  />
                  <button
                    className="btn-danger"
                    onClick={handleDeleteAccount}
                    disabled={loading || deleteConfirm !== 'SUPPRIMER'}
                  >
                    {loading ? 'Suppression...' : 'Supprimer mon compte'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="profile-notifications">
              <div className="profile-section">
                <h3>Tester les notifications</h3>
                <p className="section-hint">
                  Vérifiez que vos notifications fonctionnent correctement.
                </p>
                <div className="notification-buttons">
                  <button
                    className={`btn-test-notif ${testingNotif === 'email' ? 'loading' : ''}`}
                    onClick={() => handleTestNotification('email')}
                    disabled={testingNotif !== null}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="2" y="4" width="20" height="16" rx="2"/>
                      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                    </svg>
                    <span>Email</span>
                  </button>
                  <button
                    className={`btn-test-notif ${testingNotif === 'push' ? 'loading' : ''}`}
                    onClick={() => handleTestNotification('push')}
                    disabled={testingNotif !== null || getPushStatus() === 'ios-browser'}
                    title={getPushStatus() === 'ios-browser' ? 'Non disponible sur Safari iOS' : undefined}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                    </svg>
                    <span>Push</span>
                  </button>
                </div>

                {/* iOS-specific messages */}
                {isIOS() && !isPWA() && (
                  <div className="ios-push-notice">
                    <p>
                      <strong>Safari iOS ne supporte pas les notifications push.</strong><br/>
                      Pour recevoir des notifications push, ajoutez Hoofs à votre écran d'accueil :
                    </p>
                    <ol>
                      <li>Appuyez sur le bouton partage <span style={{fontSize: '16px'}}>⎙</span></li>
                      <li>Sélectionnez "Sur l'écran d'accueil"</li>
                      <li>Ouvrez l'app depuis votre écran d'accueil</li>
                    </ol>
                    <p className="ios-hint">Les notifications email fonctionnent dans tous les cas.</p>
                  </div>
                )}

                {isIOS() && isPWA() && (
                  <div className="ios-push-notice ios-pwa">
                    <p>
                      <strong>Notifications push sur iOS</strong><br/>
                      Appuyez sur le bouton ci-dessous pour autoriser les notifications.
                    </p>
                    <button
                      className="btn-primary-small"
                      onClick={async () => {
                        const granted = await requestPushPermission()
                        if (granted) {
                          showMessage('Notifications autorisées ! Vous pouvez maintenant tester.', 'success')
                        } else {
                          showMessage('Notifications refusées. Activez-les dans Réglages > Hoofs.', 'error')
                        }
                      }}
                    >
                      Autoriser les notifications
                    </button>
                  </div>
                )}

                {/* Bouton pour activer les notifications sur tous les navigateurs */}
                <div className={`push-permission-section ${notifPermission === 'granted' ? 'granted' : notifPermission === 'denied' ? 'denied' : ''}`}>
                  {notifPermission === 'granted' && debugInfo?.subscriptionId && debugInfo.subscriptionId !== 'non disponible' ? (
                    <>
                      <div className="push-status-granted">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                          <polyline points="22 4 12 14.01 9 11.01"/>
                        </svg>
                        Notifications activées
                      </div>
                      <p className="push-hint">Vous recevrez les notifications push</p>
                    </>
                  ) : notifPermission === 'denied' ? (
                    <>
                      <div className="push-status-denied">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="10"/>
                          <line x1="15" y1="9" x2="9" y2="15"/>
                          <line x1="9" y1="9" x2="15" y2="15"/>
                        </svg>
                        Notifications bloquées
                      </div>
                      <p className="push-hint">
                        Pour les activer : cliquez sur le cadenas dans la barre d'adresse → Notifications → Autoriser
                      </p>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn-enable-push"
                        onClick={async () => {
                          showMessage('Activation en cours...', 'success')

                          // Utiliser OneSignal pour demander la permission
                          if (typeof window !== 'undefined' && window.OneSignalDeferred) {
                            window.OneSignalDeferred.push(async (OneSignal: any) => {
                              try {
                                // 1. Demander la permission via OneSignal
                                console.log('[Push] Requesting permission via OneSignal...')
                                await OneSignal.Notifications.requestPermission()

                                // 2. Attendre et vérifier la permission
                                await new Promise(r => setTimeout(r, 500))
                                const perm = Notification.permission
                                setNotifPermission(perm)
                                console.log('[Push] Permission result:', perm)

                                if (perm === 'granted') {
                                  // 3. Forcer l'opt-in pour créer la subscription
                                  console.log('[Push] Opting in to push...')
                                  try {
                                    await OneSignal.User.PushSubscription.optIn()
                                  } catch (e) {
                                    console.log('[Push] OptIn error (may be normal):', e)
                                  }

                                  // 4. Attendre la création de la subscription
                                  await new Promise(r => setTimeout(r, 1500))

                                  // 5. Récupérer l'ID
                                  const subId = await OneSignal.User?.PushSubscription?.id
                                  console.log('[Push] Subscription ID:', subId)

                                  if (subId) {
                                    // 6. Sync avec le backend
                                    const token = getAccessToken ? await getAccessToken() : accessToken
                                    if (token) {
                                      const result = await forceOneSignalSync(token)
                                      showMessage(result.message, result.success ? 'success' : 'error')
                                    }
                                    setDebugInfo(prev => prev ? { ...prev, subscriptionId: subId, permission: 'granted' } : null)
                                  } else {
                                    showMessage('Permission OK mais ID non créé. Rechargez la page et réessayez.', 'error')
                                  }
                                } else if (perm === 'denied') {
                                  showMessage('Notifications bloquées. Vérifiez les paramètres.', 'error')
                                } else {
                                  showMessage('Permission non accordée. Réessayez.', 'error')
                                }
                              } catch (error: any) {
                                console.error('[Push] Error:', error)
                                showMessage(`Erreur: ${error.message || 'Inconnue'}`, 'error')
                              }
                            })
                          } else {
                            showMessage('OneSignal non chargé. Rechargez la page.', 'error')
                          }
                        }}
                      >
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                        </svg>
                        {notifPermission === 'granted' ? 'Réactiver les notifications' : 'Activer les notifications push'}
                      </button>
                      <p className="push-hint">
                        {notifPermission === 'granted'
                          ? 'Permission OK mais ID manquant. Cliquez pour réessayer.'
                          : 'Cliquez pour autoriser les notifications'
                        }
                      </p>
                    </>
                  )}
                </div>
              </div>

              {/* Debug info */}
              {debugInfo && (
                <div className="profile-section debug-section">
                  <h3>Diagnostic Push</h3>
                  <div className="debug-info">
                    <div className="debug-row">
                      <span>iOS:</span>
                      <span className={debugInfo.isIOS ? 'yes' : 'no'}>{debugInfo.isIOS ? 'Oui' : 'Non'}</span>
                    </div>
                    <div className="debug-row">
                      <span>Mode PWA:</span>
                      <span className={debugInfo.isPWA ? 'yes' : 'no'}>{debugInfo.isPWA ? 'Oui' : 'Non'}</span>
                    </div>
                    <div className="debug-row">
                      <span>Permission:</span>
                      <span className={debugInfo.permission === 'granted' ? 'yes' : 'no'}>{debugInfo.permission}</span>
                    </div>
                    <div className="debug-row">
                      <span>OneSignal:</span>
                      <span className={debugInfo.oneSignalLoaded ? 'yes' : 'no'}>{debugInfo.oneSignalLoaded ? 'Chargé' : 'Non chargé'}</span>
                    </div>
                    <div className="debug-row">
                      <span>ID Push:</span>
                      <span className={debugInfo.subscriptionId && debugInfo.subscriptionId !== 'non disponible' ? 'yes' : 'no'}>
                        {debugInfo.subscriptionId || 'En attente...'}
                      </span>
                    </div>
                  </div>
                  {debugInfo.isIOS && !debugInfo.isPWA && (
                    <p className="debug-warning">⚠️ Vous n'êtes pas en mode PWA. Ajoutez l'app à l'écran d'accueil depuis Safari.</p>
                  )}
                  {debugInfo.permission === 'denied' && (
                    <p className="debug-warning">⚠️ Notifications bloquées. Allez dans Réglages → Safari → Notifications.</p>
                  )}
                  {debugInfo.permission === 'granted' && (!debugInfo.subscriptionId || debugInfo.subscriptionId === 'non disponible') && (
                    <p className="debug-warning">⚠️ Permission OK mais pas d'ID. Essayez de recharger l'app.</p>
                  )}
                </div>
              )}

              <div className="profile-section">
                <h3>Délai de notification</h3>
                <p className="section-hint">
                  Le délai dépend de votre abonnement.
                </p>
                <div className="plan-comparison">
                  <div className={`plan-item ${userPlan === 'free' ? 'current' : ''}`}>
                    <span className="plan-name">Gratuit</span>
                    <span className="plan-delay">10 minutes</span>
                  </div>
                  <div className={`plan-item ${userPlan === 'premium' ? 'current' : ''}`}>
                    <span className="plan-name">Premium</span>
                    <span className="plan-delay">1 minute</span>
                  </div>
                  <div className={`plan-item ${userPlan === 'pro' ? 'current' : ''}`}>
                    <span className="plan-name">Pro</span>
                    <span className="plan-delay">10 secondes</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="profile-actions">
          <button className="btn-secondary" onClick={onClose}>
            Fermer
          </button>
        </div>
      </div>
    </div>
  )
}
