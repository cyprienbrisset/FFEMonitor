'use client'

import { Concours, formatStatut, formatDate, formatDateShort } from '@/lib/api'

interface ConcoursCardProps {
  concours: Concours
  onDelete: (numero: number) => void
  index: number
}

export function ConcoursCard({ concours, onDelete, index }: ConcoursCardProps) {
  const c = concours

  const handleDelete = () => {
    if (confirm(`Retirer le concours ${c.numero} de la surveillance ?`)) {
      onDelete(c.numero)
    }
  }

  // Build subtitle parts
  const subtitleParts: string[] = []
  if (c.nom) {
    subtitleParts.push(`#${c.numero}`)
  }
  if (c.lieu && (!c.nom || !c.nom.includes(c.lieu))) {
    subtitleParts.push(c.lieu)
  }
  if (c.date_debut) {
    subtitleParts.push(formatDateShort(c.date_debut))
  }

  return (
    <div
      className={`concours-card status-${c.statut}`}
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      <div className="concours-header">
        <div className="concours-title-wrapper">
          <div className="concours-nom">{c.nom || `#${c.numero}`}</div>
          <div className="concours-subtitle">{subtitleParts.join(' • ')}</div>
        </div>
        <div className="concours-actions">
          <button
            className="btn-delete"
            onClick={handleDelete}
            title="Retirer de la surveillance"
          >
            ×
          </button>
        </div>
      </div>

      <div className="concours-meta">
        <span className={`concours-badge badge-status ${c.statut}`}>
          {formatStatut(c.statut)}
        </span>
        {c.statut !== 'ferme' && (
          <span className={`concours-badge badge-notif ${c.notifie ? 'sent' : 'pending'}`}>
            {c.notifie ? 'Notification envoyée' : 'Notification en attente'}
          </span>
        )}
      </div>

      <div className="concours-time">
        Dernière vérification : {formatDate(c.last_check)}
      </div>

      <a
        href={`https://ffecompet.ffe.com/concours/${encodeURIComponent(c.numero)}`}
        target="_blank"
        rel="noopener noreferrer"
        className="btn-access"
      >
        <span>Accéder au concours</span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M7 17L17 7M17 7H7M17 7V17"/>
        </svg>
      </a>
    </div>
  )
}
