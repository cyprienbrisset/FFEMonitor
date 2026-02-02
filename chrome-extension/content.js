/**
 * FFE Monitor Chrome Extension - Content Script
 * Injects surveillance buttons on FFE Compet pages
 */

(function() {
    'use strict';

    // Check if we're on a relevant page
    const isConcoursListPage = window.location.href.includes('/concours') ||
                               window.location.href.includes('/recherche');
    const isConcoursDetailPage = /\/concours\/\d+/.test(window.location.href);

    if (!isConcoursListPage && !isConcoursDetailPage) return;

    console.log('[FFE Monitor] Extension chargée');

    // Create notification container
    const notificationContainer = document.createElement('div');
    notificationContainer.id = 'ffemonitor-notifications';
    document.body.appendChild(notificationContainer);

    // Show notification
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = 'ffemonitor-notification ffemonitor-' + type;

        const icon = document.createElement('span');
        icon.className = 'ffemonitor-notification-icon';
        icon.textContent = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';

        const text = document.createElement('span');
        text.className = 'ffemonitor-notification-text';
        text.textContent = message;

        notification.appendChild(icon);
        notification.appendChild(text);
        notificationContainer.appendChild(notification);

        // Animate in
        setTimeout(() => notification.classList.add('show'), 10);

        // Remove after 4 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    }

    // Add concours to surveillance
    async function addToSurveillance(numero, button) {
        const originalText = button.textContent;
        button.textContent = '';
        const spinner = document.createElement('span');
        spinner.className = 'ffemonitor-spinner';
        button.appendChild(spinner);
        button.disabled = true;

        try {
            const settings = await chrome.storage.sync.get(['apiUrl', 'token', 'username', 'password']);

            if (!settings.apiUrl || !settings.token) {
                showNotification('Configurez l\'extension dans le popup', 'error');
                return;
            }

            // Try to add the concours
            let response = await fetch(settings.apiUrl + '/concours', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + settings.token,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ numero: parseInt(numero) }),
            });

            // If unauthorized, try to re-authenticate
            if (response.status === 401) {
                const newToken = await reAuthenticate(settings);
                if (newToken) {
                    response = await fetch(settings.apiUrl + '/concours', {
                        method: 'POST',
                        headers: {
                            'Authorization': 'Bearer ' + newToken,
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ numero: parseInt(numero) }),
                    });
                } else {
                    showNotification('Session expirée - Reconnectez-vous via l\'extension', 'error');
                    return;
                }
            }

            if (response.status === 201) {
                showNotification('Concours ' + numero + ' ajouté à la surveillance', 'success');
                button.textContent = '✓ Surveillé';
                button.classList.add('ffemonitor-btn-added');
                button.disabled = true;
            } else if (response.status === 409) {
                showNotification('Concours ' + numero + ' déjà surveillé', 'info');
                button.textContent = '✓ Surveillé';
                button.classList.add('ffemonitor-btn-added');
                button.disabled = true;
            } else {
                throw new Error('Erreur ' + response.status);
            }
        } catch (error) {
            console.error('[FFE Monitor] Error:', error);
            showNotification('Erreur: ' + error.message, 'error');
            button.textContent = originalText;
            button.disabled = false;
        }
    }

    // Re-authenticate
    async function reAuthenticate(settings) {
        if (!settings.username || !settings.password) return null;

        try {
            const response = await fetch(settings.apiUrl + '/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: settings.username,
                    password: settings.password,
                }),
            });

            if (response.ok) {
                const data = await response.json();
                await chrome.storage.sync.set({ token: data.access_token });
                return data.access_token;
            }
        } catch (error) {
            console.error('[FFE Monitor] Re-auth failed:', error);
        }
        return null;
    }

    // Check if concours is already monitored
    async function isMonitored(numero) {
        try {
            const settings = await chrome.storage.sync.get(['apiUrl', 'token']);
            if (!settings.apiUrl || !settings.token) return false;

            const response = await fetch(settings.apiUrl + '/concours', {
                headers: { 'Authorization': 'Bearer ' + settings.token },
            });

            if (response.ok) {
                const data = await response.json();
                return data.concours.some(c => c.numero === parseInt(numero));
            }
        } catch (error) {
            console.error('[FFE Monitor] Check monitored failed:', error);
        }
        return false;
    }

    // Create surveillance button
    function createButton(numero) {
        const btn = document.createElement('button');
        btn.className = 'ffemonitor-btn';
        btn.textContent = '🐴 Surveiller';
        btn.title = 'Ajouter à FFE Monitor';
        btn.dataset.numero = numero;

        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            addToSurveillance(numero, btn);
        });

        return btn;
    }

    // Extract concours number from URL or element
    function extractConcoursNumber(element) {
        // Try from href
        const link = element.querySelector('a[href*="/concours/"]') ||
                     element.closest('a[href*="/concours/"]');
        if (link) {
            const match = link.href.match(/\/concours\/(\d+)/);
            if (match) return match[1];
        }

        // Try from data attribute
        if (element.dataset.concours) return element.dataset.concours;

        // Try from text content that looks like a number
        const text = element.textContent;
        const match = text.match(/\b(\d{9})\b/);
        if (match) return match[1];

        return null;
    }

    // Inject buttons into list pages
    async function injectListButtons() {
        // Wait a bit for the page to fully load
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Try different selectors for competition items
        const selectors = [
            '.resultat-concours',        // Search results
            '.concours-item',            // List items
            'tr[data-concours]',         // Table rows
            '.competition-card',         // Card layout
            '[class*="concours"]',       // Any element with concours in class
        ];

        let items = [];
        for (const selector of selectors) {
            items = document.querySelectorAll(selector);
            if (items.length > 0) break;
        }

        // Also look for links to concours pages
        if (items.length === 0) {
            const links = document.querySelectorAll('a[href*="/concours/"]');
            links.forEach(link => {
                const match = link.href.match(/\/concours\/(\d+)/);
                if (match && !link.closest('.ffemonitor-btn-container')) {
                    const numero = match[1];
                    const container = document.createElement('span');
                    container.className = 'ffemonitor-btn-container ffemonitor-inline';
                    container.appendChild(createButton(numero));

                    // Insert after the link
                    if (link.parentNode) {
                        link.parentNode.insertBefore(container, link.nextSibling);
                    }
                }
            });
            return;
        }

        items.forEach(async item => {
            // Skip if button already added
            if (item.querySelector('.ffemonitor-btn')) return;

            const numero = extractConcoursNumber(item);
            if (!numero) return;

            const btn = createButton(numero);
            const container = document.createElement('div');
            container.className = 'ffemonitor-btn-container';
            container.appendChild(btn);

            // Check if already monitored
            const monitored = await isMonitored(numero);
            if (monitored) {
                btn.textContent = '✓ Surveillé';
                btn.classList.add('ffemonitor-btn-added');
                btn.disabled = true;
            }

            // Try to find a good place to insert the button
            const actionArea = item.querySelector('.actions, .buttons, [class*="action"]');
            if (actionArea) {
                actionArea.appendChild(container);
            } else {
                item.appendChild(container);
            }
        });
    }

    // Inject button on detail page
    async function injectDetailButton() {
        const match = window.location.href.match(/\/concours\/(\d+)/);
        if (!match) return;

        const numero = match[1];

        // Wait for page to load
        await new Promise(resolve => setTimeout(resolve, 500));

        // Find a good place for the button (usually near the title or action buttons)
        const titleElement = document.querySelector('h1, .titre-concours, .concours-title, [class*="titre"]');
        const actionArea = document.querySelector('.actions, .buttons, .btn-group, [class*="action"]');

        const btn = createButton(numero);
        const container = document.createElement('div');
        container.className = 'ffemonitor-btn-container ffemonitor-detail';
        container.appendChild(btn);

        // Check if already monitored
        const monitored = await isMonitored(numero);
        if (monitored) {
            btn.textContent = '✓ Surveillé';
            btn.classList.add('ffemonitor-btn-added');
            btn.disabled = true;
        }

        if (actionArea) {
            actionArea.prepend(container);
        } else if (titleElement) {
            titleElement.parentNode.insertBefore(container, titleElement.nextSibling);
        } else {
            // Last resort: add at the top of the page
            const main = document.querySelector('main, .content, #content, body');
            if (main) {
                main.prepend(container);
            }
        }
    }

    // Create floating action button for quick add
    function createFloatingButton() {
        const fab = document.createElement('div');
        fab.className = 'ffemonitor-fab';

        const fabBtn = document.createElement('button');
        fabBtn.className = 'ffemonitor-fab-btn';
        fabBtn.title = 'Ajouter un concours à FFE Monitor';
        fabBtn.textContent = '🐴';

        const menu = document.createElement('div');
        menu.className = 'ffemonitor-fab-menu';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'ffemonitor-fab-input';
        input.placeholder = 'N° concours';
        input.maxLength = 9;

        const addBtn = document.createElement('button');
        addBtn.className = 'ffemonitor-fab-add';
        addBtn.textContent = 'Ajouter';

        menu.appendChild(input);
        menu.appendChild(addBtn);
        fab.appendChild(fabBtn);
        fab.appendChild(menu);

        fabBtn.addEventListener('click', () => {
            fab.classList.toggle('open');
            if (fab.classList.contains('open')) {
                input.focus();
            }
        });

        addBtn.addEventListener('click', () => {
            const numero = input.value.trim();
            if (numero && /^\d+$/.test(numero)) {
                addToSurveillance(numero, addBtn);
                input.value = '';
                setTimeout(() => fab.classList.remove('open'), 1000);
            }
        });

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                addBtn.click();
            }
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!fab.contains(e.target)) {
                fab.classList.remove('open');
            }
        });

        document.body.appendChild(fab);
    }

    // Initialize
    async function init() {
        const settings = await chrome.storage.sync.get(['apiUrl', 'token']);

        if (!settings.apiUrl || !settings.token) {
            console.log('[FFE Monitor] Extension non configurée');
            // Still show FAB for configuration reminder
        }

        // Inject appropriate buttons based on page type
        if (isConcoursDetailPage) {
            injectDetailButton();
        } else {
            injectListButtons();
        }

        // Always add the floating action button
        createFloatingButton();

        // Re-run injection when page content changes (for SPAs)
        const observer = new MutationObserver((mutations) => {
            let shouldReinject = false;
            for (const mutation of mutations) {
                if (mutation.addedNodes.length > 0) {
                    for (const node of mutation.addedNodes) {
                        if (node.nodeType === 1 && !node.classList?.contains('ffemonitor-btn-container')) {
                            shouldReinject = true;
                            break;
                        }
                    }
                }
                if (shouldReinject) break;
            }

            if (shouldReinject) {
                setTimeout(() => {
                    if (isConcoursDetailPage) {
                        injectDetailButton();
                    } else {
                        injectListButtons();
                    }
                }, 500);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });
    }

    // Start
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
