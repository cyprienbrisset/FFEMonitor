'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import Link from 'next/link'
import { useAuth } from '@/components/auth/AuthProvider'
import {
  loadConcours,
  loadHealth,
  addConcours,
  deleteConcours,
  Concours,
  HealthStatus,
} from '@/lib/api'
import { AddConcoursForm } from '@/components/dashboard/AddConcoursForm'
import { StatsCard } from '@/components/dashboard/StatsCard'
import { ConcoursList } from '@/components/dashboard/ConcoursList'
import { Calendar } from '@/components/dashboard/Calendar'
import { UserProfileModal } from '@/components/dashboard/UserProfileModal'
import { ExtensionModal } from '@/components/dashboard/ExtensionModal'
import { MobileNav } from '@/components/dashboard/MobileNav'

const REFRESH_INTERVAL = 3000

export default function DashboardPage() {
  const [concours, setConcours] = useState<Concours[]>([])
  const [total, setTotal] = useState(0)
  const [status, setStatus] = useState<HealthStatus | null>(null)
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null)
  const [showProfile, setShowProfile] = useState(false)
  const [showExtension, setShowExtension] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const router = useRouter()
  const { session, user, signOut, loading: authLoading } = useAuth()

  // Refs for mobile navigation
  const addFormRef = useRef<HTMLDivElement>(null)
  const calendarRef = useRef<HTMLDivElement>(null)

  const accessToken = session?.access_token

  const fetchData = useCallback(async () => {
    if (!accessToken) return

    try {
      const [concoursData, healthData] = await Promise.all([
        loadConcours(accessToken),
        loadHealth(),
      ])

      setConcours(concoursData.concours)
      setTotal(concoursData.total)
      setStatus(healthData)
    } catch (error) {
      console.error('Error fetching data:', error)
    }
  }, [accessToken])

  useEffect(() => {
    if (authLoading || !accessToken) return

    fetchData()

    const interval = setInterval(fetchData, REFRESH_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchData, authLoading, accessToken])

  const handleAddConcours = async (numero: number) => {
    try {
      await addConcours(numero, accessToken)
      setMessage({ text: `Concours ${numero} ajouté à la surveillance`, type: 'success' })
      fetchData()
    } catch (error: any) {
      setMessage({ text: error.message || 'Erreur lors de l\'ajout', type: 'error' })
    }

    setTimeout(() => setMessage(null), 5000)
  }

  const handleDeleteConcours = async (numero: number) => {
    try {
      await deleteConcours(numero, accessToken)
      fetchData()
    } catch (error) {
      alert('Erreur lors de la suppression')
    }
  }

  const handleLogout = async () => {
    await signOut()
    router.push('/login')
    router.refresh()
  }

  // Mobile nav handlers
  const scrollToAddForm = () => {
    setShowAddForm(true)
    setTimeout(() => {
      addFormRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // Focus the input
      const input = addFormRef.current?.querySelector('input')
      input?.focus()
    }, 100)
  }

  const scrollToCalendar = () => {
    calendarRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="logo-wrapper">
          <Image
            src="/logo.svg"
            alt="FFE Monitor"
            width={40}
            height={40}
            className="logo"
          />
        </div>
        <div className="header-text">
          <h1>FFE Monitor</h1>
          <p className="tagline">Surveillance Premium des Concours FFE</p>
        </div>
        <div className="header-actions">
          <Link href="/guide" className="btn-guide" title="Guide utilisateur">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
            <span>Guide</span>
          </Link>
          <button
            onClick={() => setShowExtension(true)}
            className="btn-extension"
            title="Installer l'extension Chrome"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C8.21 0 4.831 1.757 2.632 4.501l3.953 6.848A5.454 5.454 0 0 1 12 6.545h10.691A12 12 0 0 0 12 0zM1.931 5.47A11.943 11.943 0 0 0 0 12c0 6.012 4.42 10.991 10.189 11.864l3.953-6.847a5.45 5.45 0 0 1-6.865-2.29zm13.342 2.166a5.446 5.446 0 0 1 1.45 7.09l.002.001h-.002l-3.952 6.848a12.014 12.014 0 0 0 11.229-9.455H15.273z"/>
            </svg>
            <span>Extension</span>
          </button>
          <button onClick={() => setShowProfile(true)} className="btn-profile" title="Mon profil">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            <span>Profil</span>
          </button>
          <button onClick={handleLogout} className="btn-logout" title="Se déconnecter">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            <span>Déconnexion</span>
          </button>
          <div
            className={`status-indicator ${status?.status === 'ok' ? 'online' : 'offline'}`}
            title={status?.status === 'ok' ? 'Système en ligne' : 'Système hors service'}
          >
            <span className="status-indicator-dot"></span>
          </div>
        </div>
      </header>

      {/* Bento Grid */}
      <main className="bento-grid">
        <div ref={addFormRef}>
          <AddConcoursForm onAdd={handleAddConcours} message={message} />
        </div>

        <StatsCard count={total} />

        <ConcoursList concours={concours} onDelete={handleDeleteConcours} />

        <div ref={calendarRef}>
          <Calendar accessToken={accessToken} />
        </div>
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <span className="footer-brand">FFE Monitor</span>
          <span className="footer-divider">•</span>
          <span className="footer-version">v1.0</span>
          <span className="footer-divider">•</span>
          <span className="footer-refresh">Actualisation automatique</span>
        </div>
      </footer>

      {/* Profile Modal */}
      {showProfile && user && (
        <UserProfileModal
          user={user}
          accessToken={accessToken}
          onClose={() => setShowProfile(false)}
          onSignOut={handleLogout}
        />
      )}

      {/* Extension Modal */}
      {showExtension && (
        <ExtensionModal onClose={() => setShowExtension(false)} />
      )}

      {/* Mobile Navigation */}
      <MobileNav
        onAddConcours={scrollToAddForm}
        onOpenCalendar={scrollToCalendar}
        onOpenProfile={() => setShowProfile(true)}
      />
    </div>
  )
}
