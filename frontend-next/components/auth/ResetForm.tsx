'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'

interface ResetFormProps {
  onBack: () => void
}

export function ResetForm({ onBack }: ResetFormProps) {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const supabase = createClient()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      })

      if (error) throw error

      setSuccess('Un email de réinitialisation a été envoyé.')
    } catch (err: any) {
      setError(err.message || 'Erreur lors de l\'envoi')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="login-form active">
      <div className="form-group">
        <label htmlFor="resetEmail">Email</label>
        <div className="input-wrapper">
          <input
            type="email"
            id="resetEmail"
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

      {error && <p className="login-error visible">{error}</p>}
      {success && <p className="login-success visible">{success}</p>}

      <button type="submit" className="btn-login" disabled={loading}>
        <span className="btn-text">{loading ? 'Envoi...' : 'Envoyer le lien'}</span>
        <span className="btn-icon">→</span>
      </button>

      <button type="button" className="back-to-login" onClick={onBack}>
        ← Retour à la connexion
      </button>
    </form>
  )
}
