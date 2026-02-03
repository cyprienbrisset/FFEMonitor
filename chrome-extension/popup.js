/**
 * Hoofs Chrome Extension - Popup Script
 * Gère l'authentification Supabase et l'état de connexion
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Elements
    const apiUrlInput = document.getElementById('apiUrl');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const openAppBtn = document.getElementById('openAppBtn');
    const message = document.getElementById('message');
    const messageConnected = document.getElementById('messageConnected');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const statusEmail = document.getElementById('statusEmail');
    const viewLogin = document.getElementById('viewLogin');
    const viewConnected = document.getElementById('viewConnected');
    const concoursCount = document.getElementById('concoursCount');
    const surveillanceStatus = document.getElementById('surveillanceStatus');

    // Load saved settings
    const settings = await chrome.storage.sync.get([
        'apiUrl',
        'supabaseUrl',
        'supabaseAnonKey',
        'accessToken',
        'refreshToken',
        'userEmail'
    ]);

    if (settings.apiUrl) apiUrlInput.value = settings.apiUrl;

    // Check if already logged in
    if (settings.accessToken && settings.apiUrl) {
        await checkSession();
    }

    // Login handler
    loginBtn.addEventListener('click', async () => {
        const apiUrl = apiUrlInput.value.trim().replace(/\/$/, '');
        const email = emailInput.value.trim();
        const password = passwordInput.value;

        if (!apiUrl || !email || !password) {
            showMessage('Veuillez remplir tous les champs', 'error');
            return;
        }

        loginBtn.disabled = true;
        loginBtn.textContent = 'Connexion...';

        try {
            // Login via backend (qui gère l'auth Supabase côté serveur)
            const loginResponse = await fetch(`${apiUrl}/auth/extension/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            if (!loginResponse.ok) {
                const error = await loginResponse.json();
                throw new Error(error.detail || 'Identifiants incorrects');
            }

            const authData = await loginResponse.json();

            // Save tokens
            await chrome.storage.sync.set({
                apiUrl,
                accessToken: authData.access_token,
                refreshToken: authData.refresh_token,
                userEmail: authData.user_email,
            });

            showMessage('Connecté avec succès !', 'success');
            await showConnectedView(authData.user_email, apiUrl, authData.access_token);

        } catch (error) {
            console.error('Login error:', error);
            showMessage(error.message, 'error');
        } finally {
            loginBtn.disabled = false;
            loginBtn.textContent = 'Se connecter';
        }
    });

    // Logout handler
    logoutBtn.addEventListener('click', async () => {
        await chrome.storage.sync.remove([
            'accessToken',
            'refreshToken',
            'userEmail',
        ]);

        statusDot.classList.remove('connected');
        statusText.textContent = 'Non connecté';
        statusEmail.textContent = '';
        viewLogin.classList.add('active');
        viewConnected.classList.remove('active');
    });

    // Open app handler
    openAppBtn.addEventListener('click', async () => {
        const settings = await chrome.storage.sync.get(['apiUrl']);
        if (settings.apiUrl) {
            // Try to open the frontend (assumed to be on port 3000 or same domain)
            const frontendUrl = settings.apiUrl.replace(':8000', ':3000').replace('/api', '');
            chrome.tabs.create({ url: `${frontendUrl}/app` });
        }
    });

    // Check session and show connected view
    async function checkSession() {
        const settings = await chrome.storage.sync.get([
            'apiUrl',
            'supabaseUrl',
            'supabaseAnonKey',
            'accessToken',
            'refreshToken',
            'userEmail'
        ]);

        if (!settings.accessToken || !settings.apiUrl) {
            return;
        }

        try {
            // Verify token with backend
            const response = await fetch(`${settings.apiUrl}/health`, {
                headers: {
                    'Authorization': `Bearer ${settings.accessToken}`,
                },
            });

            if (response.ok) {
                await showConnectedView(settings.userEmail, settings.apiUrl, settings.accessToken);
            } else if (response.status === 401 && settings.refreshToken) {
                // Try to refresh token
                const refreshed = await refreshAccessToken(settings);
                if (refreshed) {
                    await checkSession();
                }
            }
        } catch (error) {
            console.error('Session check failed:', error);
        }
    }

    // Refresh access token
    async function refreshAccessToken(settings) {
        try {
            const response = await fetch(`${settings.supabaseUrl}/auth/v1/token?grant_type=refresh_token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'apikey': settings.supabaseAnonKey,
                },
                body: JSON.stringify({ refresh_token: settings.refreshToken }),
            });

            if (response.ok) {
                const data = await response.json();
                await chrome.storage.sync.set({
                    accessToken: data.access_token,
                    refreshToken: data.refresh_token,
                });
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }
        return false;
    }

    // Show connected view
    async function showConnectedView(email, apiUrl, token) {
        statusDot.classList.add('connected');
        statusText.textContent = 'Connecté';
        statusEmail.textContent = email;
        viewLogin.classList.remove('active');
        viewConnected.classList.add('active');

        // Load stats
        try {
            const response = await fetch(`${apiUrl}/concours`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (response.ok) {
                const data = await response.json();
                concoursCount.textContent = data.total || 0;
                surveillanceStatus.textContent = '✓';
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    // Show message
    function showMessage(text, type) {
        const activeMessage = viewLogin.classList.contains('active') ? message : messageConnected;
        activeMessage.textContent = text;
        activeMessage.className = `message ${type}`;
        setTimeout(() => {
            activeMessage.className = 'message';
        }, 5000);
    }
});
