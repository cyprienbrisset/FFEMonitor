'use client'

interface ExtensionModalProps {
  onClose: () => void
}

export function ExtensionModal({ onClose }: ExtensionModalProps) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content extension-modal" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>

        <div className="modal-header">
          <div className="modal-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C8.21 0 4.831 1.757 2.632 4.501l3.953 6.848A5.454 5.454 0 0 1 12 6.545h10.691A12 12 0 0 0 12 0zM1.931 5.47A11.943 11.943 0 0 0 0 12c0 6.012 4.42 10.991 10.189 11.864l3.953-6.847a5.45 5.45 0 0 1-6.865-2.29zm13.342 2.166a5.446 5.446 0 0 1 1.45 7.09l.002.001h-.002l-3.952 6.848a12.014 12.014 0 0 0 11.229-9.455H15.273z"/>
            </svg>
          </div>
          <h2>Installer l'Extension Chrome</h2>
        </div>

        <div className="extension-download">
          <a
            href="/chrome-extension.zip"
            download="ffe-monitor-extension.zip"
            className="btn-download-extension"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            <span>Télécharger l'extension</span>
          </a>
        </div>

        <div className="extension-steps">
          <div className="step">
            <span className="step-number">1</span>
            <div className="step-content">
              <h3>Télécharger et extraire</h3>
              <p>Téléchargez le fichier ZIP ci-dessus et extrayez-le sur votre ordinateur</p>
            </div>
          </div>

          <div className="step">
            <span className="step-number">2</span>
            <div className="step-content">
              <h3>Ouvrir les extensions Chrome</h3>
              <p>Accédez à <code>chrome://extensions</code> dans votre navigateur</p>
              <button
                className="btn-copy"
                onClick={() => navigator.clipboard.writeText('chrome://extensions')}
              >
                Copier l'URL
              </button>
            </div>
          </div>

          <div className="step">
            <span className="step-number">3</span>
            <div className="step-content">
              <h3>Activer le mode développeur</h3>
              <p>Activez le toggle "Mode développeur" en haut à droite de la page</p>
            </div>
          </div>

          <div className="step">
            <span className="step-number">4</span>
            <div className="step-content">
              <h3>Charger l'extension</h3>
              <p>Cliquez sur "Charger l'extension non empaquetée" et sélectionnez le dossier <code>chrome-extension</code></p>
            </div>
          </div>

          <div className="step">
            <span className="step-number">5</span>
            <div className="step-content">
              <h3>Épingler l'extension</h3>
              <p>Cliquez sur l'icône puzzle puis épinglez FFE Monitor pour un accès rapide</p>
            </div>
          </div>
        </div>

        <div className="extension-note">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 16v-4M12 8h.01"/>
          </svg>
          <span>L'extension permet d'ajouter rapidement des concours depuis le site FFE</span>
        </div>
      </div>
    </div>
  )
}
