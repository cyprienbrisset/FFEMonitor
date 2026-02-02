const API_BASE = ''

export interface Concours {
  id: number
  numero: number
  nom?: string
  lieu?: string
  date_debut?: string
  date_fin?: string
  statut: 'ferme' | 'previsionnel' | 'engagement' | 'demande' | 'cloture' | 'en_cours' | 'termine' | 'annule'
  notifie: boolean
  last_check?: string
  created_at: string
}

export interface ConcoursListResponse {
  concours: Concours[]
  total: number
}

export interface HealthStatus {
  status: string
  surveillance_active: boolean
  concours_count?: number
}

export interface GlobalStats {
  total_checks: number
  checks_today: number
  total_openings: number
  avg_response_time_ms: number
}

export interface ActivityData {
  labels: string[]
  checks: number[]
  openings: number[]
}

export interface CalendarEvent {
  numero: number
  nom?: string
  date_debut?: string
  date_fin?: string
  statut: string
}

function getAuthHeaders(accessToken?: string): HeadersInit {
  return {
    'Authorization': accessToken ? `Bearer ${accessToken}` : '',
    'Content-Type': 'application/json',
  }
}

async function authenticatedFetch(
  url: string,
  accessToken?: string,
  options: RequestInit = {}
): Promise<Response> {
  const headers = getAuthHeaders(accessToken)

  const response = await fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...(options.headers || {}),
    },
  })

  return response
}

export async function loadConcours(accessToken?: string): Promise<ConcoursListResponse> {
  const response = await authenticatedFetch(`${API_BASE}/concours`, accessToken)

  if (!response.ok) {
    const text = await response.text()
    console.error('API Error:', response.status, text)
    throw new Error(`Erreur chargement concours: ${response.status}`)
  }

  return response.json()
}

export async function addConcours(numero: number, accessToken?: string): Promise<Concours> {
  const response = await authenticatedFetch(`${API_BASE}/concours`, accessToken, {
    method: 'POST',
    body: JSON.stringify({ numero }),
  })

  if (response.status === 409) {
    throw new Error(`Le concours ${numero} est déjà surveillé`)
  }

  if (!response.ok) {
    throw new Error('Erreur lors de l\'ajout du concours')
  }

  return response.json()
}

export async function deleteConcours(numero: number, accessToken?: string): Promise<void> {
  const response = await authenticatedFetch(`${API_BASE}/concours/${numero}`, accessToken, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error('Erreur lors de la suppression')
  }
}

export async function loadHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/health`)

  if (!response.ok) {
    throw new Error('Erreur status')
  }

  return response.json()
}

export async function loadGlobalStats(accessToken?: string): Promise<GlobalStats> {
  const response = await authenticatedFetch(`${API_BASE}/stats/global`, accessToken)

  if (!response.ok) {
    throw new Error('Erreur stats')
  }

  return response.json()
}

export async function loadActivityData(period: '24h' | '7d', accessToken?: string): Promise<ActivityData> {
  const response = await authenticatedFetch(`${API_BASE}/stats/activity?period=${period}`, accessToken)

  if (!response.ok) {
    throw new Error('Erreur activity data')
  }

  return response.json()
}

export async function loadCalendarEvents(month: number, year: number, accessToken?: string): Promise<{ events: CalendarEvent[] }> {
  const response = await authenticatedFetch(`${API_BASE}/calendar/events?month=${month}&year=${year}`, accessToken)

  if (!response.ok) {
    return { events: [] }
  }

  return response.json()
}

export async function testNotification(channel: 'telegram' | 'email' | 'whatsapp', accessToken?: string): Promise<{ success: boolean; message: string }> {
  const response = await authenticatedFetch(`${API_BASE}/test-${channel}`, accessToken, {
    method: 'POST',
  })

  return response.json()
}

// Helper functions
export function formatStatut(statut: string): string {
  const labels: Record<string, string> = {
    'previsionnel': 'Prévisionnel',
    'engagement': 'Ouvert',
    'demande': 'Demande',
    'cloture': 'Clôturé',
    'en_cours': 'En cours',
    'termine': 'Terminé',
    'annule': 'Annulé',
    'ferme': 'Inconnu'
  }
  return labels[statut] || statut
}

export function formatDate(isoString?: string): string {
  if (!isoString) return '—'
  const date = new Date(isoString)
  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

export function formatDateShort(isoString?: string): string {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short'
  })
}

export function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}
