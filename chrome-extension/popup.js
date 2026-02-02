/**
 * FFE Monitor Chrome Extension - Popup Script
 */

document.addEventListener('DOMContentLoaded', async () => {
    const apiUrlInput = document.getElementById('apiUrl');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const saveBtn = document.getElementById('saveBtn');
    const testBtn = document.getElementById('testBtn');
    const message = document.getElementById('message');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const statsSection = document.getElementById('statsSection');
    const concoursCount = document.getElementById('concoursCount');
    const surveillanceStatus = document.getElementById('surveillanceStatus');

    // Load saved settings
    const settings = await chrome.storage.sync.get(['apiUrl', 'username', 'password', 'token']);

    if (settings.apiUrl) apiUrlInput.value = settings.apiUrl;
    if (settings.username) usernameInput.value = settings.username;
    if (settings.password) passwordInput.value = settings.password;

    // If we have a token, check connection
    if (settings.token && settings.apiUrl) {
        testBtn.style.display = 'block';
        await checkConnection(settings.apiUrl, settings.token);
    }

    // Save settings
    saveBtn.addEventListener('click', async () => {
        const apiUrl = apiUrlInput.value.trim().replace(/\/$/, ''); // Remove trailing slash
        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!apiUrl || !username || !password) {
            showMessage('Veuillez remplir tous les champs', 'error');
            return;
        }

        saveBtn.disabled = true;
        saveBtn.textContent = 'Connexion...';

        try {
            // Authenticate
            const token = await authenticate(apiUrl, username, password);

            if (token) {
                // Save everything
                await chrome.storage.sync.set({
                    apiUrl,
                    username,
                    password,
                    token
                });

                showMessage('Connecté avec succès !', 'success');
                testBtn.style.display = 'block';
                await checkConnection(apiUrl, token);
            }
        } catch (error) {
            showMessage(error.message, 'error');
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = 'Enregistrer & Connecter';
        }
    });

    // Test connection
    testBtn.addEventListener('click', async () => {
        const settings = await chrome.storage.sync.get(['apiUrl', 'token']);
        if (settings.apiUrl && settings.token) {
            testBtn.disabled = true;
            testBtn.textContent = 'Test...';
            await checkConnection(settings.apiUrl, settings.token);
            testBtn.disabled = false;
            testBtn.textContent = 'Tester la connexion';
        }
    });

    async function authenticate(apiUrl, username, password) {
        try {
            const response = await fetch(`${apiUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            if (response.ok) {
                const data = await response.json();
                return data.access_token;
            } else if (response.status === 401) {
                throw new Error('Identifiants incorrects');
            } else {
                throw new Error('Erreur de connexion au serveur');
            }
        } catch (error) {
            if (error.message.includes('Failed to fetch')) {
                throw new Error('Impossible de joindre le serveur FFE Monitor');
            }
            throw error;
        }
    }

    async function checkConnection(apiUrl, token) {
        try {
            // Check health
            const healthResponse = await fetch(`${apiUrl}/health`);
            if (!healthResponse.ok) throw new Error('Serveur non disponible');

            const health = await healthResponse.json();

            // Verify token
            const verifyResponse = await fetch(`${apiUrl}/auth/verify`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (verifyResponse.ok) {
                statusDot.classList.add('connected');
                statusText.textContent = 'Connecté';
                statsSection.style.display = 'flex';
                concoursCount.textContent = health.concours_count || 0;
                surveillanceStatus.textContent = health.surveillance_active ? '✓' : '✗';
            } else {
                // Token expired, try to re-authenticate
                const settings = await chrome.storage.sync.get(['apiUrl', 'username', 'password']);
                if (settings.username && settings.password) {
                    const newToken = await authenticate(settings.apiUrl, settings.username, settings.password);
                    if (newToken) {
                        await chrome.storage.sync.set({ token: newToken });
                        return checkConnection(apiUrl, newToken);
                    }
                }
                throw new Error('Session expirée');
            }
        } catch (error) {
            statusDot.classList.remove('connected');
            statusText.textContent = 'Non connecté';
            statsSection.style.display = 'none';
            console.error('Connection check failed:', error);
        }
    }

    function showMessage(text, type) {
        message.textContent = text;
        message.className = `message ${type}`;
        setTimeout(() => {
            message.className = 'message';
        }, 5000);
    }
});
