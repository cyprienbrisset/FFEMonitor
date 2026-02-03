/**
 * Hoofs Chrome Extension - Content Script
 * Injecte des boutons "Ajouter à Hoofs" à côté des boutons "Ajouter au comparateur"
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
        } else {
            button.classList.remove('hoofs-btn-added');
        }
    }

    // Extraire le numéro de concours depuis l'URL ou la page
    function getConcoursNumber() {
        // Essayer depuis l'URL: /concours/123456
        const urlMatch = window.location.pathname.match(/\/concours\/(\d+)/);
        if (urlMatch) {
            return urlMatch[1];
        }

        // Essayer depuis un attribut datanumber sur la page
        const elementWithData = document.querySelector('[datanumber]');
        if (elementWithData) {
            return elementWithData.getAttribute('datanumber');
        }

        // Essayer depuis le titre ou un élément contenant le numéro
        const pageText = document.body.innerText;
        const textMatch = pageText.match(/N°\s*(\d{9})/);
        if (textMatch) {
            return textMatch[1];
        }

        return null;
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
                setButtonContent(button, '🐴', 'Ajouter à Hoofs');
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
                setButtonContent(button, '✓', 'Ajouté à Hoofs', true);
                button.disabled = true;
            } else if (response.status === 409) {
                showNotification(`Concours ${numero} déjà surveillé`, 'info');
                setButtonContent(button, '✓', 'Déjà dans Hoofs', true);
                button.disabled = true;
            } else if (response.status === 401) {
                showNotification('Session expirée - Reconnectez-vous via l\'extension', 'error');
                setButtonContent(button, '🐴', 'Ajouter à Hoofs');
                button.disabled = false;
            } else {
                throw new Error(`Erreur ${response.status}`);
            }
        } catch (error) {
            console.error('[Hoofs] Erreur:', error);
            showNotification(`Erreur: ${error.message}`, 'error');
            setButtonContent(button, '🐴', 'Ajouter à Hoofs');
            button.disabled = false;
        }
    }

    // Créer un bouton Hoofs
    function createHoofsButton(numero) {
        const btn = document.createElement('button');
        btn.className = 'hoofs-btn';
        btn.title = 'Ajouter à la surveillance Hoofs';
        btn.dataset.numero = numero;
        btn.type = 'button';

        setButtonContent(btn, '🐴', 'Ajouter à Hoofs');

        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            addToHoofs(numero, btn);
        });

        return btn;
    }

    // Vérifier si un concours est déjà surveillé
    async function isConcoursMonitored(numero) {
        try {
            const settings = await chrome.storage.sync.get(['apiUrl', 'accessToken']);
            if (!settings.apiUrl || !settings.accessToken) return false;

            const response = await fetch(`${settings.apiUrl}/concours`, {
                headers: { 'Authorization': `Bearer ${settings.accessToken}` },
            });

            if (response.ok) {
                const data = await response.json();
                return data.concours.some(c => c.numero.toString() === numero.toString());
            }
        } catch (error) {
            console.error('[Hoofs] Erreur vérification:', error);
        }
        return false;
    }

    // Injecter le bouton Hoofs à côté du bouton comparateur
    async function injectHoofsButton() {
        // Chercher le bouton "Ajouter au comparateur" ou similaire
        const comparateurButtons = document.querySelectorAll('button, a.btn, .btn');
        let targetButton = null;

        for (const btn of comparateurButtons) {
            const text = btn.textContent.toLowerCase();
            if (text.includes('comparateur') || text.includes('comparer')) {
                targetButton = btn;
                break;
            }
        }

        // Si pas trouvé, chercher dans les actions de la page
        if (!targetButton) {
            const actionContainers = document.querySelectorAll('.actions, .btn-group, .buttons, [class*="action"], [class*="button"]');
            for (const container of actionContainers) {
                if (container.querySelector('button, a.btn')) {
                    targetButton = container.querySelector('button, a.btn');
                    break;
                }
            }
        }

        // Extraire le numéro de concours
        const numero = getConcoursNumber();

        if (!numero) {
            console.log('[Hoofs] Numéro de concours non trouvé');
            return;
        }

        console.log(`[Hoofs] Concours détecté: ${numero}`);

        // Vérifier si le bouton Hoofs existe déjà
        if (document.querySelector('.hoofs-btn')) {
            console.log('[Hoofs] Bouton déjà présent');
            return;
        }

        // Créer le bouton Hoofs
        const hoofsBtn = createHoofsButton(numero);

        // Vérifier si déjà surveillé
        const isMonitored = await isConcoursMonitored(numero);
        if (isMonitored) {
            setButtonContent(hoofsBtn, '✓', 'Déjà dans Hoofs', true);
            hoofsBtn.disabled = true;
        }

        // Insérer le bouton
        if (targetButton && targetButton.parentNode) {
            // Insérer après le bouton comparateur
            targetButton.parentNode.insertBefore(hoofsBtn, targetButton.nextSibling);
            console.log('[Hoofs] Bouton inséré après le bouton comparateur');
        } else {
            // Fallback: créer un conteneur flottant
            const container = document.createElement('div');
            container.className = 'hoofs-floating-container';
            container.appendChild(hoofsBtn);
            document.body.appendChild(container);
            console.log('[Hoofs] Bouton inséré en position flottante');
        }
    }

    // Injecter dans les lignes de tableau (liste des concours)
    async function injectButtonsInTable() {
        const rows = document.querySelectorAll('tr[datanumber]');

        if (rows.length === 0) {
            return false;
        }

        console.log(`[Hoofs] ${rows.length} concours trouvés dans le tableau`);

        // Récupérer la liste des concours déjà surveillés
        const settings = await chrome.storage.sync.get(['apiUrl', 'accessToken']);
        let monitored = new Set();

        if (settings.apiUrl && settings.accessToken) {
            try {
                const response = await fetch(`${settings.apiUrl}/concours`, {
                    headers: { 'Authorization': `Bearer ${settings.accessToken}` },
                });
                if (response.ok) {
                    const data = await response.json();
                    monitored = new Set(data.concours.map(c => c.numero.toString()));
                }
            } catch (e) {
                console.error('[Hoofs] Erreur récupération concours:', e);
            }
        }

        // Injecter un bouton dans chaque ligne
        rows.forEach(row => {
            // Skip si déjà traité
            if (row.querySelector('.hoofs-btn')) return;

            const numero = row.getAttribute('datanumber');
            if (!numero) return;

            // Trouver la cellule des actions ou la dernière cellule
            let targetCell = row.querySelector('td:last-child');
            const actionCell = row.querySelector('td.actions, td:has(button), td:has(a.btn)');
            if (actionCell) {
                targetCell = actionCell;
            }

            if (!targetCell) return;

            const btn = createHoofsButton(numero);

            // Marquer comme déjà ajouté si nécessaire
            if (monitored.has(numero)) {
                setButtonContent(btn, '✓', 'Hoofs', true);
                btn.disabled = true;
            } else {
                setButtonContent(btn, '🐴', 'Hoofs');
            }

            // Style compact pour le tableau
            btn.style.marginLeft = '5px';
            btn.style.fontSize = '11px';
            btn.style.padding = '4px 8px';

            targetCell.appendChild(btn);
        });

        return true;
    }

    // Initialisation
    async function init() {
        // Attendre que la page soit complètement chargée
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Essayer d'injecter dans le tableau (page liste)
        const injectedInTable = await injectButtonsInTable();

        // Si pas de tableau, essayer la page détail
        if (!injectedInTable) {
            await injectHoofsButton();
        }

        // Observer les changements DOM pour les pages dynamiques
        const observer = new MutationObserver((mutations) => {
            let shouldReinject = false;

            for (const mutation of mutations) {
                if (mutation.addedNodes.length > 0) {
                    for (const node of mutation.addedNodes) {
                        if (node.nodeType === 1) {
                            if (node.tagName === 'TR' && node.hasAttribute('datanumber')) {
                                shouldReinject = true;
                                break;
                            }
                            if (node.querySelector && node.querySelector('tr[datanumber]')) {
                                shouldReinject = true;
                                break;
                            }
                            // Détecter aussi les nouveaux boutons comparateur
                            if (node.textContent && node.textContent.toLowerCase().includes('comparateur')) {
                                shouldReinject = true;
                                break;
                            }
                        }
                    }
                }
                if (shouldReinject) break;
            }

            if (shouldReinject) {
                setTimeout(async () => {
                    const injected = await injectButtonsInTable();
                    if (!injected) {
                        await injectHoofsButton();
                    }
                }, 500);
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
