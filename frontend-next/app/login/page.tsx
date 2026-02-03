'use client'

import { useState } from 'react'
import Image from 'next/image'
import { LoginForm } from '@/components/auth/LoginForm'
import { SignupForm } from '@/components/auth/SignupForm'
import { ResetForm } from '@/components/auth/ResetForm'

type Tab = 'login' | 'signup'
type View = 'auth' | 'reset'

export default function LoginPage() {
  const [activeTab, setActiveTab] = useState<Tab>('login')
  const [view, setView] = useState<View>('auth')

  const handleTabClick = (tab: Tab) => {
    setActiveTab(tab)
    setView('auth')
  }

  return (
    <div className="login-screen">
      <div className="login-container">
        <div className="login-card">
          {/* Logo et titre */}
          <div className="login-header">
            <div className="login-logo-wrapper">
              <Image
                src="/logo.svg"
                alt="Hoofs Logo"
                width={72}
                height={72}
                className="login-logo"
                priority
              />
            </div>
            <p className="login-tagline">Surveillance Premium des Concours FFE</p>
          </div>

          {/* Tabs pour basculer entre login et signup */}
          {view === 'auth' && (
            <div className="auth-tabs">
              <button
                type="button"
                className={`auth-tab ${activeTab === 'login' ? 'active' : ''}`}
                onClick={() => handleTabClick('login')}
              >
                Connexion
              </button>
              <button
                type="button"
                className={`auth-tab ${activeTab === 'signup' ? 'active' : ''}`}
                onClick={() => handleTabClick('signup')}
              >
                Inscription
              </button>
            </div>
          )}

          {/* Forms */}
          {view === 'auth' && activeTab === 'login' && (
            <LoginForm onForgotPassword={() => setView('reset')} />
          )}

          {view === 'auth' && activeTab === 'signup' && (
            <SignupForm onSuccess={() => setActiveTab('login')} />
          )}

          {view === 'reset' && (
            <ResetForm onBack={() => setView('auth')} />
          )}

          {/* Footer */}
          <div className="login-footer">
            <p>Accès sécurisé à votre espace de surveillance</p>
            <div className="plan-badges">
              <span className="plan-badge free">Free</span>
              <span className="plan-badge premium">Premium</span>
              <span className="plan-badge pro">Pro</span>
            </div>
          </div>
        </div>

        {/* Decoration */}
        <div className="login-decoration">
          <div className="decoration-circle circle-1"></div>
          <div className="decoration-circle circle-2"></div>
          <div className="decoration-circle circle-3"></div>
        </div>
      </div>
    </div>
  )
}
