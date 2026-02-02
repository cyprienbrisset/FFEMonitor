'use client'

import { useMemo } from 'react'
import { Concours } from '@/lib/api'
import { ConcoursCard } from './ConcoursCard'

interface ConcoursListProps {
  concours: Concours[]
  onDelete: (numero: number) => void
}

export function ConcoursList({ concours, onDelete }: ConcoursListProps) {
  // Trier les concours par date (plus proche en premier)
  const sortedConcours = useMemo(() => {
    return [...concours].sort((a, b) => {
      const dateA = a.date_debut ? new Date(a.date_debut).getTime() : Infinity
      const dateB = b.date_debut ? new Date(b.date_debut).getTime() : Infinity
      return dateA - dateB
    })
  }, [concours])

  if (sortedConcours.length === 0) {
    return (
      <section className="bento-card card-list">
        <div className="card-header">
          <span className="card-icon">☰</span>
          <h2>Concours en Surveillance</h2>
        </div>
        <div className="empty-state">
          <div className="empty-icon">
            <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="50" cy="50" r="45" stroke="currentColor" strokeWidth="2" strokeDasharray="8 4"/>
              <path d="M35 50 L45 60 L65 40" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" opacity="0.3"/>
            </svg>
          </div>
          <p className="empty-title">Aucun concours surveillé</p>
          <p className="empty-hint">Ajoutez un numéro de concours pour démarrer la surveillance automatique</p>
        </div>
      </section>
    )
  }

  return (
    <section className="bento-card card-list">
      <div className="card-header">
        <span className="card-icon">☰</span>
        <h2>Concours en Surveillance</h2>
      </div>
      <div className="concours-grid">
        {sortedConcours.map((c, index) => (
          <ConcoursCard
            key={c.numero}
            concours={c}
            onDelete={onDelete}
            index={index}
          />
        ))}
      </div>
    </section>
  )
}
