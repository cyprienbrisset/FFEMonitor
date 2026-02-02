'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

interface MobileNavProps {
  onAddConcours?: () => void
  onOpenCalendar?: () => void
  onOpenProfile?: () => void
}

export function MobileNav({ onAddConcours, onOpenCalendar, onOpenProfile }: MobileNavProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isClosing, setIsClosing] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  // Close menu when clicking outside
  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (!target.closest('.mobile-nav')) {
        handleClose()
      }
    }

    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [isOpen])

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        handleClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen])

  const handleClose = useCallback(() => {
    setIsClosing(true)
    setTimeout(() => {
      setIsOpen(false)
      setIsClosing(false)
    }, 300)
  }, [])

  const handleToggle = () => {
    if (isOpen) {
      handleClose()
    } else {
      setIsOpen(true)
    }
  }

  const handleAction = (action: () => void) => {
    handleClose()
    setTimeout(action, 150)
  }

  const handleLogout = async () => {
    handleClose()
    await supabase.auth.signOut()
    router.push('/login')
  }

  const menuItems = [
    {
      id: 'add',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
          <path d="M12 5v14M5 12h14" />
        </svg>
      ),
      label: 'Ajouter',
      color: 'var(--pastel-sage)',
      action: () => onAddConcours?.(),
    },
    {
      id: 'calendar',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <rect x="3" y="4" width="18" height="18" rx="2" />
          <path d="M16 2v4M8 2v4M3 10h18" />
        </svg>
      ),
      label: 'Calendrier',
      color: 'var(--pastel-lavender)',
      action: () => onOpenCalendar?.(),
    },
    {
      id: 'profile',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 20c0-4 4-6 8-6s8 2 8 6" />
        </svg>
      ),
      label: 'Profil',
      color: 'var(--pastel-mint)',
      action: () => onOpenProfile?.(),
    },
    {
      id: 'logout',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
        </svg>
      ),
      label: 'Déconnexion',
      color: 'var(--pastel-coral)',
      action: handleLogout,
    },
  ]

  // Calculate orbital positions (quarter circle, bottom-right)
  const getItemStyle = (index: number, total: number) => {
    const startAngle = 180 // Start from left
    const endAngle = 270 // End at top
    const angleStep = (endAngle - startAngle) / (total - 1)
    const angle = startAngle + angleStep * index
    const radius = 110 // Distance from center - increased for better spacing

    const x = Math.cos((angle * Math.PI) / 180) * radius
    const y = Math.sin((angle * Math.PI) / 180) * radius

    return {
      '--item-x': `${x}px`,
      '--item-y': `${y}px`,
      '--item-delay': `${index * 50}ms`,
    } as React.CSSProperties
  }

  return (
    <nav className={`mobile-nav ${isOpen ? 'open' : ''} ${isClosing ? 'closing' : ''}`}>
      {/* Backdrop */}
      <div className="mobile-nav-backdrop" onClick={handleClose} />

      {/* Orbital Menu Items */}
      <div className="mobile-nav-orbital">
        {menuItems.map((item, index) => (
          <button
            key={item.id}
            className="orbital-item"
            style={{
              ...getItemStyle(index, menuItems.length),
              '--item-color': item.color,
            } as React.CSSProperties}
            onClick={() => handleAction(item.action)}
            aria-label={item.label}
          >
            <span className="orbital-icon">{item.icon}</span>
            <span className="orbital-label">{item.label}</span>
          </button>
        ))}
      </div>

      {/* Main FAB Button */}
      <button
        className="mobile-nav-fab"
        onClick={handleToggle}
        aria-label={isOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
        aria-expanded={isOpen}
      >
        <span className="fab-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <path className="fab-line-1" d="M12 5v14" />
            <path className="fab-line-2" d="M5 12h14" />
          </svg>
        </span>
        <span className="fab-ripple" />
      </button>
    </nav>
  )
}
