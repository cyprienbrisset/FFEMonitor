'use client'

import { useState, useEffect } from 'react'
import { User } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase/client'
import { testNotification, loadProfile, UserProfile } from '@/lib/api'

interface UserProfileModalProps {
  user: User
  accessToken?: string
  onClose: () => void
  onSignOut: () => void
}

type Tab = 'info' | 'security' | 'notifications'

const PLAN_LABELS: Record<string, { label: string; color: string }> = {
  free: { label: 'Gratuit', color: 'var(--gray)' },
  premium: { label: 'Premium', color: 'var(--warning)' },
  pro: { label: 'Pro', color: 'var(--success)' },
}

export function UserProfileModal({ user, accessToken, onClose, onSignOut }: UserProfileModalProps) {
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
      const result = await testNotification(channel as any, accessToken)
      showMessage(result.message || 'Notification envoyée !', result.success ? 'success' : 'error')
    } catch (error: any) {
      showMessage(error.message || 'Erreur lors du test', 'error')
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
                    disabled={testingNotif !== null}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                    </svg>
                    <span>Push</span>
                  </button>
                </div>
              </div>

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
