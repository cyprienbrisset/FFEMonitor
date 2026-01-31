/**
 * FFE Monitor — Premium Frontend
 * Gestion de l'interface utilisateur, authentification et communication avec l'API
 */

// Configuration
const API_BASE = '';  // Même origine
const REFRESH_INTERVAL = 3000;  // 3 secondes
const TOKEN_KEY = 'ffemonitor_token';

// État de l'application
let refreshTimer = null;
let authToken = null;

// ============================================================================
// Initialisation
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Vérifier si un token existe
    authToken = localStorage.getItem(TOKEN_KEY);

    if (authToken) {
        // Vérifier la validité du token
        verifyToken();
    } else {
        // Afficher l'écran de connexion
        showLoginScreen();
    }

    // Initialiser les événements
    initLoginForm();
    initLogoutButton();
});

function initLoginForm() {
    const form = document.getElementById('loginForm');
    form.addEventListener('submit', handleLogin);
}

function initLogoutButton() {
    const button = document.getElementById('logoutButton');
    button.addEventListener('click', handleLogout);
}

function initApp() {
    const form = document.getElementById('addForm');
    form.addEventListener('submit', handleAddConcours);

    loadConcours();
    loadStatus();
    startAutoRefresh();
}

function startAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    refreshTimer = setInterval(() => {
        loadConcours();
        loadStatus();
    }, REFRESH_INTERVAL);
}

function stopAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
    }
}

// ============================================================================
// Screen Management
// ============================================================================

function showLoginScreen() {
    document.getElementById('loginScreen').style.display = 'flex';
    document.getElementById('appScreen').style.display = 'none';
    stopAutoRefresh();
}

function showAppScreen() {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('appScreen').style.display = 'flex';
    initApp();
}

// ============================================================================
// Authentication
// ============================================================================

async function verifyToken() {
    try {
        const response = await fetch(`${API_BASE}/auth/verify`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });

        if (response.ok) {
            showAppScreen();
        } else {
            // Token invalide
            localStorage.removeItem(TOKEN_KEY);
            authToken = null;
            showLoginScreen();
        }
    } catch (error) {
        console.error('Erreur vérification token:', error);
        showLoginScreen();
    }
}

async function handleLogin(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const button = document.getElementById('loginButton');
    const btnText = button.querySelector('.btn-text');
    const errorEl = document.getElementById('loginError');

    // Reset error
    errorEl.textContent = '';
    errorEl.classList.remove('visible');

    // Disable button
    button.disabled = true;
    btnText.textContent = 'Connexion...';

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            localStorage.setItem(TOKEN_KEY, authToken);

            // Animation de succès
            btnText.textContent = 'Connecté !';
            setTimeout(() => {
                showAppScreen();
            }, 500);
        } else {
            const data = await response.json();
            showLoginError(data.detail || 'Identifiants incorrects');
        }
    } catch (error) {
        console.error('Erreur connexion:', error);
        showLoginError('Erreur de connexion au serveur');
    } finally {
        button.disabled = false;
        btnText.textContent = 'Se connecter';
    }
}

function handleLogout() {
    // Supprimer le token
    localStorage.removeItem(TOKEN_KEY);
    authToken = null;

    // Afficher l'écran de connexion
    showLoginScreen();

    // Reset le formulaire
    document.getElementById('loginForm').reset();
    document.getElementById('loginError').classList.remove('visible');
}

function showLoginError(message) {
    const errorEl = document.getElementById('loginError');
    errorEl.textContent = message;
    errorEl.classList.add('visible');
}

// ============================================================================
// API Calls (avec authentification)
// ============================================================================

function getAuthHeaders() {
    return {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
    };
}

async function authenticatedFetch(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            ...getAuthHeaders(),
            ...(options.headers || {}),
        },
    });

    // Si 401, déconnecter
    if (response.status === 401) {
        handleLogout();
        throw new Error('Session expirée');
    }

    return response;
}

async function loadConcours() {
    try {
        const response = await authenticatedFetch(`${API_BASE}/concours`);
        if (!response.ok) throw new Error('Erreur chargement');

        const data = await response.json();
        renderConcoursList(data.concours);
        updateCount(data.total);

    } catch (error) {
        if (error.message !== 'Session expirée') {
            console.error('Erreur chargement concours:', error);
        }
    }
}

async function loadStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (!response.ok) throw new Error('Erreur status');

        const data = await response.json();
        updateStatusBar(data);

    } catch (error) {
        console.error('Erreur chargement status:', error);
        updateStatusBar({ ffe_connected: false, surveillance_active: false });
    }
}

async function handleAddConcours(event) {
    event.preventDefault();

    const input = document.getElementById('numeroInput');
    const button = document.getElementById('addButton');
    const btnText = button.querySelector('.btn-text');

    const numero = parseInt(input.value);
    if (!numero || numero <= 0) {
        showMessage('Veuillez entrer un numéro de concours valide', 'error');
        return;
    }

    // Désactiver le formulaire
    button.disabled = true;
    btnText.textContent = 'Ajout...';

    try {
        const response = await authenticatedFetch(`${API_BASE}/concours`, {
            method: 'POST',
            body: JSON.stringify({ numero }),
        });

        if (response.status === 201) {
            showMessage(`Concours ${numero} ajouté à la surveillance`, 'success');
            input.value = '';
            loadConcours();
        } else if (response.status === 409) {
            showMessage(`Le concours ${numero} est déjà surveillé`, 'error');
        } else {
            throw new Error('Erreur serveur');
        }

    } catch (error) {
        if (error.message !== 'Session expirée') {
            showMessage('Erreur lors de l\'ajout du concours', 'error');
        }
    } finally {
        button.disabled = false;
        btnText.textContent = 'Surveiller';
    }
}

async function deleteConcours(numero) {
    if (!confirm(`Retirer le concours ${numero} de la surveillance ?`)) {
        return;
    }

    try {
        const response = await authenticatedFetch(`${API_BASE}/concours/${numero}`, {
            method: 'DELETE',
        });

        if (response.ok) {
            loadConcours();
        } else {
            alert('Erreur lors de la suppression');
        }

    } catch (error) {
        if (error.message !== 'Session expirée') {
            alert('Erreur lors de la suppression');
        }
    }
}

// ============================================================================
// Rendering (Safe DOM methods)
// ============================================================================

function renderConcoursList(concours) {
    const container = document.getElementById('concoursContainer');
    const emptyState = document.getElementById('emptyState');

    // Clear existing cards
    while (container.firstChild) {
        container.removeChild(container.firstChild);
    }

    if (concours.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'flex';
        return;
    }

    container.style.display = 'grid';
    emptyState.style.display = 'none';

    // Build concours cards using safe DOM methods
    concours.forEach((c, index) => {
        const card = document.createElement('div');
        card.className = `concours-card status-${c.statut}`;
        card.style.animationDelay = `${index * 0.05}s`;

        // Header with numero and actions
        const header = document.createElement('div');
        header.className = 'concours-header';

        const numero = document.createElement('div');
        numero.className = 'concours-numero';
        const link = document.createElement('a');
        link.href = `https://ffecompet.ffe.com/concours/${encodeURIComponent(c.numero)}`;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = `#${c.numero}`;
        numero.appendChild(link);

        const actions = document.createElement('div');
        actions.className = 'concours-actions';
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn-delete';
        deleteBtn.textContent = '×';
        deleteBtn.title = 'Retirer de la surveillance';
        deleteBtn.addEventListener('click', () => deleteConcours(c.numero));
        actions.appendChild(deleteBtn);

        header.appendChild(numero);
        header.appendChild(actions);

        // Meta badges
        const meta = document.createElement('div');
        meta.className = 'concours-meta';

        // Status badge
        const statusBadge = document.createElement('span');
        statusBadge.className = `concours-badge badge-status ${c.statut}`;
        statusBadge.textContent = formatStatut(c.statut);
        meta.appendChild(statusBadge);

        // Notification badge
        const notifBadge = document.createElement('span');
        notifBadge.className = `concours-badge badge-notif ${c.notifie ? 'sent' : 'pending'}`;
        notifBadge.textContent = c.notifie ? 'Notifié' : 'En attente';
        meta.appendChild(notifBadge);

        // Time info
        const timeInfo = document.createElement('div');
        timeInfo.className = 'concours-time';
        timeInfo.textContent = `Dernière vérification : ${formatDate(c.last_check)}`;

        // Assemble card
        card.appendChild(header);
        card.appendChild(meta);
        card.appendChild(timeInfo);

        container.appendChild(card);
    });
}

function updateStatusBar(status) {
    const ffeIndicator = document.getElementById('ffeStatus');
    const ffeText = document.getElementById('ffeStatusText');

    const survIndicator = document.getElementById('surveillanceStatus');
    const survText = document.getElementById('surveillanceStatusText');

    const lastUpdate = document.getElementById('lastUpdate');

    // FFE Connection
    if (status.ffe_connected) {
        ffeIndicator.className = 'status-dot connected';
        ffeText.textContent = 'Connecté';
    } else {
        ffeIndicator.className = 'status-dot disconnected';
        ffeText.textContent = 'Déconnecté';
    }

    // Surveillance
    if (status.surveillance_active) {
        survIndicator.className = 'status-dot connected';
        survText.textContent = 'Active';
    } else {
        survIndicator.className = 'status-dot disconnected';
        survText.textContent = 'Inactive';
    }

    // Last update time
    const now = new Date();
    lastUpdate.textContent = `Mise à jour : ${now.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    })}`;
}

function updateCount(count) {
    const countEl = document.getElementById('concoursCount');
    const currentCount = parseInt(countEl.textContent) || 0;

    if (currentCount !== count) {
        // Add a subtle animation when count changes
        countEl.style.transform = 'scale(1.1)';
        countEl.textContent = count;
        setTimeout(() => {
            countEl.style.transform = 'scale(1)';
        }, 200);
    }
}

// ============================================================================
// Helpers
// ============================================================================

function formatStatut(statut) {
    const labels = {
        'ferme': 'Fermé',
        'engagement': 'Engagement',
        'demande': 'Demande',
    };
    return labels[statut] || statut;
}

function formatDate(isoString) {
    if (!isoString) return '—';

    const date = new Date(isoString);
    return date.toLocaleString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
}

function showMessage(text, type) {
    const messageEl = document.getElementById('formMessage');
    messageEl.textContent = text;
    messageEl.className = `form-message ${type}`;

    // Masquer après 5 secondes
    setTimeout(() => {
        messageEl.className = 'form-message';
    }, 5000);
}
