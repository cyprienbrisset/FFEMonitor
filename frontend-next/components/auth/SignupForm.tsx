'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'

interface SignupFormProps {
  onSuccess: () => void
}

export function SignupForm({ onSuccess }: SignupFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const supabase = createClient()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (password !== passwordConfirm) {
      setError('Les mots de passe ne correspondent pas')
      return
    }

    if (password.length < 6) {
      setError('Le mot de passe doit contenir au moins 6 caractères')
      return
    }

    setLoading(true)

    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      })

      if (error) throw error

      if (data.user && !data.session) {
        // Email confirmation required
        setSuccess('Vérifiez votre email pour confirmer votre inscription.')
        setTimeout(() => {
          onSuccess()
        }, 3000)
      } else {
        // Auto-logged in
        window.location.href = '/app'
      }
    } catch (err: any) {
      setError(err.message || 'Erreur lors de l\'inscription')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="login-form active">
      <div className="form-group">
        <label htmlFor="signupEmail">Email</label>
        <div className="input-wrapper">
          <input
            type="email"
            id="signupEmail"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="votre@email.com"
            required
            autoComplete="email"
          />
          <span className="input-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
          </span>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="signupPassword">Mot de passe</label>
        <div className="input-wrapper">
          <input
            type="password"
            id="signupPassword"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Minimum 6 caractères"
            required
            minLength={6}
            autoComplete="new-password"
          />
          <span className="input-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </span>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="signupPasswordConfirm">Confirmer le mot de passe</label>
        <div className="input-wrapper">
          <input
            type="password"
            id="signupPasswordConfirm"
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
            placeholder="Confirmez votre mot de passe"
            required
            minLength={6}
            autoComplete="new-password"
          />
          <span className="input-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </span>
        </div>
      </div>

      {error && <p className="login-error visible">{error}</p>}
      {success && <p className="login-success visible">{success}</p>}

      <button type="submit" className="btn-login" disabled={loading}>
        <span className="btn-text">{loading ? 'Création...' : 'Créer mon compte'}</span>
        <span className="btn-icon">→</span>
      </button>

      <p className="signup-info">
        En créant un compte, vous acceptez nos conditions d'utilisation.
        Vous commencez avec un plan <strong>Free</strong>.
      </p>
    </form>
  )
}
