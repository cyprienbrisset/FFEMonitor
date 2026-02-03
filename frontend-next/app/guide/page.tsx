import Image from 'next/image'
import Link from 'next/link'
import './guide.css'

export const metadata = {
  title: 'Hoofs — Guide Utilisateur',
}

export default function GuidePage() {
  return (
    <div className="guide-container">
      {/* Header */}
      <header className="guide-header">
        <Link href="/app" className="guide-back-link">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          Retour
        </Link>
        <div className="guide-logo">
          <Image src="/logo_hoofs.png" alt="Hoofs" width={48} height={48} />
        </div>
        <h1>Guide Utilisateur</h1>
        <p className="guide-subtitle">Tout savoir sur Hoofs</p>
      </header>

      {/* Content */}
      <main className="guide-main">
        {/* Introduction Card */}
        <section className="guide-card guide-card-intro">
          <div className="guide-card-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 16v-4M12 8h.01"/>
            </svg>
          </div>
          <h2>Qu'est-ce qu'Hoofs ?</h2>
          <p><strong>Hoofs</strong> surveille automatiquement les concours équestres FFE et vous alerte instantanément dès l'ouverture des engagements.</p>
          <p className="guide-highlight">Plus besoin de rafraîchir la page manuellement, on s'en charge pour vous.</p>
        </section>

        {/* How it works */}
        <section className="guide-card">
          <h2>Comment ça marche ?</h2>
          <div className="guide-steps">
            <div className="guide-step">
              <span className="guide-step-number">1</span>
              <div className="guide-step-content">
                <h3>Ajoutez un concours</h3>
                <p>Entrez le numéro du concours (visible dans l'URL FFE)</p>
              </div>
            </div>
            <div className="guide-step">
              <span className="guide-step-number">2</span>
              <div className="guide-step-content">
                <h3>Surveillance automatique</h3>
                <p>Notre système vérifie le concours toutes les quelques secondes</p>
              </div>
            </div>
            <div className="guide-step">
              <span className="guide-step-number">3</span>
              <div className="guide-step-content">
                <h3>Notification instantanée</h3>
                <p>Recevez une alerte dès que les engagements ouvrent</p>
              </div>
            </div>
          </div>
        </section>

        {/* Finding contest number */}
        <section className="guide-card guide-card-tip">
          <h2>Où trouver le numéro du concours ?</h2>
          <p>Le numéro se trouve dans l'URL de la page FFE :</p>
          <div className="guide-url-example">
            <code>https://ffecompet.ffe.com/concours/<strong>123456</strong></code>
          </div>
          <p className="guide-note">Dans cet exemple, le numéro est <strong>123456</strong></p>
        </section>

        {/* Status meanings */}
        <section className="guide-card">
          <h2>Comprendre les statuts</h2>
          <div className="guide-status-grid">
            <div className="guide-status-item">
              <span className="guide-status-badge guide-status-closed">Fermé</span>
              <p>Engagements pas encore ouverts</p>
            </div>
            <div className="guide-status-item">
              <span className="guide-status-badge guide-status-open">Ouvert</span>
              <p>Bouton "Engager" disponible</p>
            </div>
            <div className="guide-status-item">
              <span className="guide-status-badge guide-status-request">Demande</span>
              <p>Concours international</p>
            </div>
            <div className="guide-status-item">
              <span className="guide-status-badge guide-status-preview">Prévisionnel</span>
              <p>Concours annoncé mais pas encore ouvert</p>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className="guide-card">
          <h2>Questions fréquentes</h2>
          <div className="guide-faq">
            <details className="guide-faq-item">
              <summary>À quelle fréquence les concours sont-ils vérifiés ?</summary>
              <p>Selon votre abonnement : <strong>10 secondes</strong> (Pro), <strong>1 minute</strong> (Premium) ou <strong>10 minutes</strong> (Gratuit).</p>
            </details>
            <details className="guide-faq-item">
              <summary>Puis-je surveiller plusieurs concours ?</summary>
              <p>Oui, vous pouvez surveiller autant de concours que vous le souhaitez.</p>
            </details>
            <details className="guide-faq-item">
              <summary>Puis-je m'engager depuis l'application ?</summary>
              <p>Non, Hoofs est un outil de surveillance. Une fois notifié, rendez-vous sur le site FFE pour vous engager.</p>
            </details>
            <details className="guide-faq-item">
              <summary>L'application fonctionne-t-elle 24h/24 ?</summary>
              <p>Oui, la surveillance est continue, jour et nuit.</p>
            </details>
          </div>
        </section>

        {/* Notifications */}
        <section className="guide-card">
          <h2>Notifications</h2>
          <p>Testez vos notifications depuis le tableau de bord pour vous assurer qu'elles fonctionnent correctement.</p>
          <div className="guide-notif-icons">
            <div className="guide-notif-item">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.18 1.897-.962 6.502-1.359 8.627-.168.9-.5 1.201-.82 1.23-.697.064-1.226-.461-1.901-.903-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.139-5.062 3.345-.479.329-.913.489-1.302.481-.428-.009-1.252-.242-1.865-.44-.751-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.831-2.529 6.998-3.015 3.333-1.386 4.025-1.627 4.477-1.635.099-.002.321.023.465.141.121.1.154.234.169.348-.001.052.014.21-.012.328z"/>
              </svg>
              <span>Telegram</span>
            </div>
            <div className="guide-notif-item">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="4" width="20" height="16" rx="2"/>
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
              </svg>
              <span>Email</span>
            </div>
            <div className="guide-notif-item">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
              <span>Push</span>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="guide-footer">
        <p className="guide-tagline">Ne manquez plus jamais l'ouverture d'un concours</p>
        <p className="guide-brand">Hoofs — Surveillance Premium</p>
      </footer>
    </div>
  )
}
