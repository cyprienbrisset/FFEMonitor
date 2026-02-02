'use client'

import { useState } from 'react'

interface AddConcoursFormProps {
  onAdd: (numero: number) => Promise<void>
  message: { text: string; type: 'success' | 'error' } | null
}

export function AddConcoursForm({ onAdd, message }: AddConcoursFormProps) {
  const [numero, setNumero] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const num = parseInt(numero)
    if (!num || num <= 0) {
      return
    }

    setLoading(true)
    try {
      await onAdd(num)
      setNumero('')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="bento-card card-add">
      <div className="card-header">
        <span className="card-icon">+</span>
        <h2>Nouveau Concours</h2>
      </div>
      <form onSubmit={handleSubmit} className="add-form">
        <div className="input-wrapper">
          <input
            type="number"
            value={numero}
            onChange={(e) => setNumero(e.target.value)}
            placeholder="N° du concours"
            min="1"
            required
            autoComplete="off"
          />
          <div className="input-border"></div>
        </div>
        <button type="submit" className="btn-add" disabled={loading}>
          <span className="btn-text">{loading ? 'Ajout...' : 'Surveiller'}</span>
          <span className="btn-icon">→</span>
        </button>
      </form>
      {message && (
        <p className={`form-message ${message.type}`}>{message.text}</p>
      )}
    </section>
  )
}
