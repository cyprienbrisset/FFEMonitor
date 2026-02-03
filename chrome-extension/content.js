/**
 * Hoofs Chrome Extension - Content Script
 * Injecte des boutons "Ajouter à Hoofs" dans les tableaux de concours FFE
 * Ne s'active que sur https://ffecompet.ffe.com/concours*
 */

(function() {
    'use strict';

    // Vérifier qu'on est bien sur la page des concours
    if (!window.location.href.startsWith('https://ffecompet.ffe.com/concours')) {
        return;
    }

    console.log('[Hoofs] Extension chargée sur la page concours');

    // Créer le conteneur de notifications
    const notificationContainer = document.createElement('div');
    notificationContainer.id = 'hoofs-notifications';
    document.body.appendChild(notificationContainer);

    // Afficher une notification
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `hoofs-notification hoofs-${type}`;

        const icon = document.createElement('span');
        icon.className = 'hoofs-notification-icon';
        icon.textContent = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';

        const text = document.createElement('span');
        text.className = 'hoofs-notification-text';
        text.textContent = message;

        notification.appendChild(icon);
        notification.appendChild(text);
        notificationContainer.appendChild(notification);

        // Animation d'entrée
        setTimeout(() => notification.classList.add('show'), 10);

        // Suppression après 4 secondes
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    }

    // Créer un spinner
    function createSpinner() {
        const spinner = document.createElement('span');
        spinner.className = 'hoofs-spinner';
        return spinner;
    }

    // Mettre à jour le contenu d'un bouton
    function setButtonContent(button, iconText, labelText, isAdded = false) {
        button.textContent = '';

        if (iconText) {
            const iconSpan = document.createElement('span');
            iconSpan.className = 'hoofs-btn-icon';
            iconSpan.textContent = iconText;
            button.appendChild(iconSpan);
        }

        if (labelText) {
            const textNode = document.createTextNode(' ' + labelText);
            button.appendChild(textNode);
        }

        if (isAdded) {
            button.classList.add('hoofs-btn-added');
        }
    }

    // Ajouter un concours à la surveillance
    async function addToHoofs(numero, button) {
        button.textContent = '';
        button.appendChild(createSpinner());
        button.disabled = true;

        try {
            const settings = await chrome.storage.sync.get(['apiUrl', 'accessToken']);

            if (!settings.apiUrl || !settings.accessToken) {
                showNotification('Connectez-vous via l\'extension Hoofs', 'error');
                setButtonContent(button, '+', 'Hoofs');
                button.disabled = false;
                return;
            }

            const response = await fetch(`${settings.apiUrl}/concours`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${settings.accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ numero: parseInt(numero) }),
            });

            if (response.status === 201 || response.status === 200) {
                showNotification(`Concours ${numero} ajouté à Hoofs`, 'success');
                setButtonContent(button, '✓', 'Ajouté', true);
                button.disabled = true;
            } else if (response.status === 409) {
                showNotification(`Concours ${numero} déjà surveillé`, 'info');
                setButtonContent(button, '✓', 'Ajouté', true);
                button.disabled = true;
            } else if (response.status === 401) {
                showNotification('Session expirée - Reconnectez-vous via l\'extension', 'error');
                setButtonContent(button, '+', 'Hoofs');
                button.disabled = false;
            } else {
                throw new Error(`Erreur ${response.status}`);
            }
        } catch (error) {
            console.error('[Hoofs] Erreur:', error);
            showNotification(`Erreur: ${error.message}`, 'error');
            setButtonContent(button, '+', 'Hoofs');
            button.disabled = false;
        }
    }

    // Créer un bouton Hoofs
    function createHoofsButton(numero) {
        const btn = document.createElement('button');
        btn.className = 'hoofs-btn';
        btn.title = 'Ajouter à Hoofs';
        btn.dataset.numero = numero;

        setButtonContent(btn, '+', 'Hoofs');

        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            addToHoofs(numero, btn);
        });

        return btn;
    }

    // Vérifier si un concours est déjà surveillé
    async function checkIfMonitored(numeros) {
        try {
            const settings = await chrome.storage.sync.get(['apiUrl', 'accessToken']);
            if (!settings.apiUrl || !settings.accessToken) return new Set();

            const response = await fetch(`${settings.apiUrl}/concours`, {
                headers: { 'Authorization': `Bearer ${settings.accessToken}` },
            });

            if (response.ok) {
                const data = await response.json();
                return new Set(data.concours.map(c => c.numero.toString()));
            }
        } catch (error) {
            console.error('[Hoofs] Erreur vérification:', error);
        }
        return new Set();
    }

    // Injecter les boutons dans les lignes de tableau
    async function injectButtons() {
        // Trouver tous les tr avec un attribut datanumber
        const rows = document.querySelectorAll('tr[datanumber]');

        if (rows.length === 0) {
            console.log('[Hoofs] Aucune ligne avec datanumber trouvée');
            return;
        }

        console.log(`[Hoofs] ${rows.length} concours trouvés`);

        // Récupérer la liste des concours déjà surveillés
        const numeros = Array.from(rows).map(row => row.getAttribute('datanumber'));
        const monitored = await checkIfMonitored(numeros);

        // Ajouter l'en-tête de colonne si nécessaire
        const headerRow = document.querySelector('thead tr, tr:first-child');
        if (headerRow && !headerRow.querySelector('.hoofs-header')) {
            const th = document.createElement('th');
            th.className = 'hoofs-header';
            th.textContent = 'Hoofs';
            th.style.cssText = 'text-align: center; min-width: 80px;';
            headerRow.appendChild(th);
        }

        // Injecter un bouton dans chaque ligne
        rows.forEach(row => {
            // Skip si déjà traité
            if (row.querySelector('.hoofs-td')) return;

            const numero = row.getAttribute('datanumber');
            if (!numero) return;

            const td = document.createElement('td');
            td.className = 'hoofs-td';
            td.style.cssText = 'text-align: center; vertical-align: middle;';

            const btn = createHoofsButton(numero);

            // Marquer comme déjà ajouté si nécessaire
            if (monitored.has(numero)) {
                setButtonContent(btn, '✓', 'Ajouté', true);
                btn.disabled = true;
            }

            td.appendChild(btn);
            row.appendChild(td);
        });
    }

    // Initialisation
    async function init() {
        // Attendre que la page soit complètement chargée
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Injecter les boutons
        await injectButtons();

        // Observer les changements DOM pour les pages dynamiques
        const observer = new MutationObserver((mutations) => {
            let shouldReinject = false;

            for (const mutation of mutations) {
                if (mutation.addedNodes.length > 0) {
                    for (const node of mutation.addedNodes) {
                        if (node.nodeType === 1) {
                            // Vérifier si c'est un nouveau tr avec datanumber
                            if (node.tagName === 'TR' && node.hasAttribute('datanumber')) {
                                shouldReinject = true;
                                break;
                            }
                            // Ou si ça contient des tr avec datanumber
                            if (node.querySelector && node.querySelector('tr[datanumber]')) {
                                shouldReinject = true;
                                break;
                            }
                        }
                    }
                }
                if (shouldReinject) break;
            }

            if (shouldReinject) {
                setTimeout(injectButtons, 500);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });
    }

    // Démarrer
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
