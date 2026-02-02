'use client'

import { useState, useEffect } from 'react'
import { loadCalendarEvents, CalendarEvent, formatStatut } from '@/lib/api'

interface CalendarProps {
  accessToken?: string
}

const MONTHS = [
  'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
  'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
]

const DAYS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']

export function Calendar({ accessToken }: CalendarProps) {
  const today = new Date()
  const [currentMonth, setCurrentMonth] = useState(today.getMonth() + 1)
  const [currentYear, setCurrentYear] = useState(today.getFullYear())
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedDay, setSelectedDay] = useState<number | null>(null)

  useEffect(() => {
    const fetchEvents = async () => {
      if (!accessToken) return
      setLoading(true)
      try {
        const data = await loadCalendarEvents(currentMonth, currentYear, accessToken)
        setEvents(data.events || [])
      } catch (error) {
        console.error('Error loading calendar events:', error)
        setEvents([])
      } finally {
        setLoading(false)
      }
    }
    fetchEvents()
  }, [currentMonth, currentYear, accessToken])

  const goToPreviousMonth = () => {
    if (currentMonth === 1) {
      setCurrentMonth(12)
      setCurrentYear(currentYear - 1)
    } else {
      setCurrentMonth(currentMonth - 1)
    }
    setSelectedDay(null)
  }

  const goToNextMonth = () => {
    if (currentMonth === 12) {
      setCurrentMonth(1)
      setCurrentYear(currentYear + 1)
    } else {
      setCurrentMonth(currentMonth + 1)
    }
    setSelectedDay(null)
  }

  const goToToday = () => {
    setCurrentMonth(today.getMonth() + 1)
    setCurrentYear(today.getFullYear())
    setSelectedDay(today.getDate())
  }

  // Get days in month
  const daysInMonth = new Date(currentYear, currentMonth, 0).getDate()

  // Get first day of month (0 = Sunday, convert to Monday = 0)
  const firstDayOfMonth = new Date(currentYear, currentMonth - 1, 1).getDay()
  const startOffset = firstDayOfMonth === 0 ? 6 : firstDayOfMonth - 1

  // Build calendar grid
  const calendarDays: (number | null)[] = []
  for (let i = 0; i < startOffset; i++) {
    calendarDays.push(null)
  }
  for (let day = 1; day <= daysInMonth; day++) {
    calendarDays.push(day)
  }

  // Get events for a specific day
  const getEventsForDay = (day: number): CalendarEvent[] => {
    return events.filter(event => {
      if (!event.date_debut) return false
      const eventDate = new Date(event.date_debut)
      return eventDate.getDate() === day &&
             eventDate.getMonth() + 1 === currentMonth &&
             eventDate.getFullYear() === currentYear
    })
  }

  // Check if a day has events
  const hasEvents = (day: number): boolean => {
    return getEventsForDay(day).length > 0
  }

  // Check if day is today
  const isToday = (day: number): boolean => {
    return day === today.getDate() &&
           currentMonth === today.getMonth() + 1 &&
           currentYear === today.getFullYear()
  }

  // Selected day events - sorted by date
  const selectedDayEvents = selectedDay
    ? getEventsForDay(selectedDay).sort((a, b) => {
        const dateA = a.date_debut ? new Date(a.date_debut).getTime() : 0
        const dateB = b.date_debut ? new Date(b.date_debut).getTime() : 0
        return dateA - dateB
      })
    : []

  return (
    <section className="bento-card card-calendar">
      <div className="card-header">
        <span className="card-icon">📅</span>
        <h2>Calendrier des Concours</h2>
      </div>

      <div className="calendar-layout">
        {/* Left: Calendar */}
        <div className="calendar-left">
          {/* Navigation */}
          <div className="calendar-nav">
            <button className="calendar-nav-btn" onClick={goToPreviousMonth}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 18l-6-6 6-6"/>
              </svg>
            </button>
            <div className="calendar-current">
              <span className="calendar-month">{MONTHS[currentMonth - 1]}</span>
              <span className="calendar-year">{currentYear}</span>
            </div>
            <button className="calendar-nav-btn" onClick={goToNextMonth}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>
            <button className="calendar-today-btn" onClick={goToToday}>
              Aujourd'hui
            </button>
          </div>

          {/* Calendar Grid */}
          <div className="calendar-grid">
            {/* Day headers */}
            {DAYS.map(day => (
              <div key={day} className="calendar-day-header">{day}</div>
            ))}

            {/* Calendar days */}
            {calendarDays.map((day, index) => (
              <div
                key={index}
                className={`calendar-day ${!day ? 'empty' : ''} ${day && isToday(day) ? 'today' : ''} ${day && hasEvents(day) ? 'has-events' : ''} ${day === selectedDay ? 'selected' : ''}`}
                onClick={() => day && setSelectedDay(day === selectedDay ? null : day)}
              >
                {day && (
                  <>
                    <span className="day-number">{day}</span>
                    {hasEvents(day) && (
                      <span className="event-dot"></span>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>

          {/* Loading indicator */}
          {loading && (
            <div className="calendar-loading">
              <span className="loading-spinner"></span>
            </div>
          )}
        </div>

        {/* Right: Selected day events */}
        <div className="calendar-right">
          {selectedDay ? (
            <div className="calendar-events">
              <h3 className="events-title">
                {selectedDay} {MONTHS[currentMonth - 1]}
                {selectedDayEvents.length > 0 && (
                  <span className="events-count">{selectedDayEvents.length} concours</span>
                )}
              </h3>
              {selectedDayEvents.length === 0 ? (
                <p className="no-events">Aucun concours ce jour</p>
              ) : (
                <div className="events-list">
                  {selectedDayEvents.map(event => (
                    <a
                      key={event.numero}
                      href={`https://ffecompet.ffe.com/concours/${event.numero}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`event-item status-${event.statut}`}
                    >
                      <div className="event-info">
                        <span className="event-name">{event.nom || `#${event.numero}`}</span>
                        <span className={`event-status ${event.statut}`}>{formatStatut(event.statut)}</span>
                      </div>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M7 17L17 7M17 7H7M17 7V17"/>
                      </svg>
                    </a>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="calendar-events-placeholder">
              <span className="placeholder-icon">👆</span>
              <p>Sélectionnez un jour pour voir les concours</p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
