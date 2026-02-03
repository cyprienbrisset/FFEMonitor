/**
 * Hoofs Chrome Extension - Content Script
 * Injecte des boutons "Surveiller avec Hoofs" à côté des boutons "Ajouter au comparateur"
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

        // Essayer depuis un attribut data-number ou data-show-number sur la page
        const elementWithData = document.querySelector('[data-number], [data-show-number]');
        if (elementWithData) {
            return elementWithData.getAttribute('data-number') || elementWithData.getAttribute('data-show-number');
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
                setButtonContent(button, '🐴', 'Surveiller avec Hoofs');
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
                showNotification(`Concours ${numero} ajouté à la surveillance`, 'success');
                setButtonContent(button, '✓', 'Surveillé', true);
                button.disabled = true;
            } else if (response.status === 409) {
                showNotification(`Concours ${numero} déjà surveillé`, 'info');
                setButtonContent(button, '✓', 'Déjà surveillé', true);
                button.disabled = true;
            } else if (response.status === 401) {
                showNotification('Session expirée - Reconnectez-vous via l\'extension', 'error');
                setButtonContent(button, '🐴', 'Surveiller avec Hoofs');
                button.disabled = false;
            } else {
                throw new Error(`Erreur ${response.status}`);
            }
        } catch (error) {
            console.error('[Hoofs] Erreur:', error);
            showNotification(`Erreur: ${error.message}`, 'error');
            setButtonContent(button, '🐴', 'Surveiller avec Hoofs');
            button.disabled = false;
        }
    }

    // Créer un bouton Hoofs
    function createHoofsButton(numero) {
        const btn = document.createElement('button');
        btn.className = 'hoofs-btn';
        btn.title = 'Surveiller ce concours avec Hoofs';
        btn.dataset.numero = numero;
        btn.type = 'button';

        setButtonContent(btn, '🐴', 'Surveiller avec Hoofs');

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

    // Injecter le bouton Hoofs sur une page de détail de concours
    async function injectHoofsButton() {
        // Vérifier si le bouton Hoofs existe déjà
        if (document.querySelector('.hoofs-btn')) {
            console.log('[Hoofs] Bouton déjà présent');
            return;
        }

        // Extraire le numéro de concours depuis l'URL
        const urlMatch = window.location.pathname.match(/\/concours\/(\d+)/);
        let numero = urlMatch ? urlMatch[1] : null;

        // Ou depuis les éléments de la page
        if (!numero) {
            const elementWithData = document.querySelector('[data-number], [data-show-number]');
            if (elementWithData) {
                numero = elementWithData.getAttribute('data-number') || elementWithData.getAttribute('data-show-number');
            }
        }

        if (!numero) {
            console.log('[Hoofs] Page détail: numéro de concours non trouvé dans URL ou attributs');
            return;
        }

        console.log(`[Hoofs] Page détail - Concours détecté: ${numero}`);

        // Chercher le bouton "Ajouter au comparateur" ou similaire
        let targetButton = null;
        const allButtons = document.querySelectorAll('button, a.btn, .btn');
        for (const btn of allButtons) {
            const text = btn.textContent.toLowerCase();
            if (text.includes('comparateur') || text.includes('comparer')) {
                targetButton = btn;
                break;
            }
        }

        // Créer le bouton Hoofs
        const hoofsBtn = createHoofsButton(numero);

        // Vérifier si déjà surveillé
        const isMonitored = await isConcoursMonitored(numero);
        if (isMonitored) {
            setButtonContent(hoofsBtn, '✓', 'Déjà surveillé', true);
            hoofsBtn.disabled = true;
        }

        // Insérer le bouton
        if (targetButton && targetButton.parentNode) {
            // Insérer après le bouton comparateur
            targetButton.parentNode.insertBefore(hoofsBtn, targetButton.nextSibling);
            console.log('[Hoofs] Bouton inséré après le bouton comparateur (page détail)');
        } else {
            // Fallback: créer un conteneur flottant
            const container = document.createElement('div');
            container.className = 'hoofs-floating-container';
            container.appendChild(hoofsBtn);
            document.body.appendChild(container);
            console.log('[Hoofs] Bouton inséré en position flottante (page détail)');
        }
    }

    // Récupérer les concours déjà surveillés
    async function getMonitoredConcours() {
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
        return monitored;
    }

    // Injecter à côté des boutons "Ajouter au comparateur"
    async function injectButtonsNextToComparator(monitored) {
        // Chercher tous les éléments avec data-show-number (le numéro de concours)
        // Format FFE: <button class="btn btn-ffec btn-grey comparator" data-action="add" data-show-number="479978">
        let comparatorButtons = document.querySelectorAll(
            'button.comparator[data-show-number], ' +
            'button[data-action="add"][data-show-number], ' +
            '.comparator[data-show-number], ' +
            '[data-action="add"][data-show-number]'
        );

        // Si rien trouvé, essayer une recherche plus large
        if (comparatorButtons.length === 0) {
            // Chercher tout élément avec data-show-number
            comparatorButtons = document.querySelectorAll('[data-show-number]');
            console.log(`[Hoofs] Recherche large: ${comparatorButtons.length} éléments avec data-show-number`);
        }

        // Fallback: chercher les boutons avec texte "comparateur"
        if (comparatorButtons.length === 0) {
            const allButtons = document.querySelectorAll('button, a.btn');
            const textButtons = [];
            allButtons.forEach(btn => {
                const text = btn.textContent?.toLowerCase() || '';
                if (text.includes('comparateur') || text.includes('ajouter')) {
                    // Chercher un numéro à proximité (parent ou frère)
                    const row = btn.closest('tr');
                    const numero = row?.getAttribute('data-number') || btn.getAttribute('data-show-number');
                    if (numero) {
                        btn.dataset.hoofsNumero = numero;
                        textButtons.push(btn);
                    }
                }
            });
            if (textButtons.length > 0) {
                comparatorButtons = textButtons;
                console.log(`[Hoofs] Trouvé ${textButtons.length} boutons par texte`);
            }
        }

        if (comparatorButtons.length === 0) {
            // Fallback: chercher tous les boutons .comparator et vérifier leur attribut
            const allComparators = document.querySelectorAll('.comparator, button.comparator');
            let foundWithNumber = 0;
            allComparators.forEach(btn => {
                if (btn.getAttribute('data-show-number')) foundWithNumber++;
            });
            console.log(`[Hoofs] Aucun bouton trouvé. .comparator: ${allComparators.length}, avec data-show-number: ${foundWithNumber}`);
            return 0;
        }

        console.log(`[Hoofs] ${comparatorButtons.length} boutons/éléments comparateur trouvés`);
        let injectedCount = 0;

        // Injecter un bouton après chaque bouton comparateur
        comparatorButtons.forEach(comparatorBtn => {
            // Skip si bouton Hoofs déjà présent à côté
            if (comparatorBtn.nextElementSibling && comparatorBtn.nextElementSibling.classList.contains('hoofs-btn')) {
                return;
            }
            // Skip si parent contient déjà un bouton Hoofs
            if (comparatorBtn.parentNode.querySelector('.hoofs-btn')) {
                return;
            }

            const numero = comparatorBtn.getAttribute('data-show-number') || comparatorBtn.dataset.hoofsNumero;
            if (!numero) return;

            const btn = createHoofsButton(numero);

            // Marquer comme déjà surveillé si nécessaire
            if (monitored.has(numero)) {
                setButtonContent(btn, '✓', 'Déjà surveillé', true);
                btn.disabled = true;
            }

            // Style pour s'aligner avec le bouton comparateur
            btn.style.marginLeft = '8px';

            // Insérer après le bouton comparateur
            comparatorBtn.parentNode.insertBefore(btn, comparatorBtn.nextSibling);
            console.log(`[Hoofs] Bouton ajouté à côté du comparateur pour concours ${numero}`);
            injectedCount++;
        });

        return injectedCount;
    }

    // Injecter dans les lignes de tableau (liste des concours)
    async function injectButtonsInTableRows(monitored) {
        // Chercher les lignes avec data-number
        const rows = document.querySelectorAll('tr[data-number]');

        if (rows.length === 0) {
            console.log('[Hoofs] Aucune ligne tr[data-number] trouvée');
            return 0;
        }

        console.log(`[Hoofs] ${rows.length} lignes tr[data-number] trouvées`);
        let injectedCount = 0;

        // Injecter un bouton dans chaque ligne
        rows.forEach(row => {
            // Skip si déjà traité
            if (row.querySelector('.hoofs-btn')) return;

            const numero = row.getAttribute('data-number');
            if (!numero) return;

            // Chercher le bouton comparateur dans cette ligne ou dans les lignes liées
            const relatedRows = document.querySelectorAll(`tr[data-number="${numero}"]`);
            let comparatorBtn = null;
            for (const r of relatedRows) {
                comparatorBtn = r.querySelector('button.comparator, .comparator, [data-action="add"]');
                if (comparatorBtn) break;
            }

            // Si on a trouvé un bouton comparateur, injecter à côté
            if (comparatorBtn && !comparatorBtn.parentNode.querySelector('.hoofs-btn')) {
                const btn = createHoofsButton(numero);
                if (monitored.has(numero)) {
                    setButtonContent(btn, '✓', 'Surveillé', true);
                    btn.disabled = true;
                }
                btn.style.marginLeft = '8px';
                comparatorBtn.parentNode.insertBefore(btn, comparatorBtn.nextSibling);
                console.log(`[Hoofs] Bouton ajouté à côté du comparateur (via row) pour ${numero}`);
                injectedCount++;
                return;
            }

            // Sinon, trouver la cellule des actions ou la dernière cellule
            let targetCell = null;
            const actionCell = row.querySelector('td:has(button), td:has(a.btn)');
            if (actionCell) {
                targetCell = actionCell;
            } else {
                targetCell = row.querySelector('td:last-child');
            }

            if (!targetCell) return;

            const btn = createHoofsButton(numero);

            // Marquer comme déjà ajouté si nécessaire
            if (monitored.has(numero)) {
                setButtonContent(btn, '✓', 'Surveillé', true);
                btn.disabled = true;
            } else {
                setButtonContent(btn, '🐴', 'Surveiller');
            }

            // Style compact pour le tableau
            btn.style.marginLeft = '5px';
            btn.style.fontSize = '11px';
            btn.style.padding = '4px 8px';

            targetCell.appendChild(btn);
            console.log(`[Hoofs] Bouton ajouté dans la cellule pour concours ${numero}`);
            injectedCount++;
        });

        return injectedCount;
    }

    // Fonction principale d'injection
    async function injectButtons() {
        const monitored = await getMonitoredConcours();

        // Essayer d'abord les boutons comparateur
        let count = await injectButtonsNextToComparator(monitored);

        // Ensuite les lignes de tableau
        count += await injectButtonsInTableRows(monitored);

        console.log(`[Hoofs] Total: ${count} boutons injectés`);
        return count > 0;
    }

    // Initialisation
    async function init() {
        console.log('[Hoofs] Initialisation sur:', window.location.href);

        // Debug: Afficher l'état initial de la page
        function debugPageState() {
            const trRows = document.querySelectorAll('tr[data-number]');
            const comparatorBtns = document.querySelectorAll('button.comparator[data-show-number]');
            const dataShowNumberEls = document.querySelectorAll('[data-show-number]');
            const allComparators = document.querySelectorAll('.comparator');
            const addBtns = document.querySelectorAll('[data-action="add"]');
            const btnWithShowNum = document.querySelectorAll('button[data-show-number]');

            // Chercher aussi dans les iframes
            const iframes = document.querySelectorAll('iframe');

            // Log détaillé
            console.log(`[Hoofs] DEBUG - URL: ${window.location.href}`);
            console.log(`[Hoofs] DEBUG - tr[data-number]: ${trRows.length}`);
            console.log(`[Hoofs] DEBUG - button.comparator[data-show-number]: ${comparatorBtns.length}`);
            console.log(`[Hoofs] DEBUG - [data-show-number]: ${dataShowNumberEls.length}`);
            console.log(`[Hoofs] DEBUG - .comparator: ${allComparators.length}`);
            console.log(`[Hoofs] DEBUG - [data-action="add"]: ${addBtns.length}`);
            console.log(`[Hoofs] DEBUG - button[data-show-number]: ${btnWithShowNum.length}`);
            console.log(`[Hoofs] DEBUG - iframes: ${iframes.length}`);

            // Log les premiers éléments trouvés pour debug
            if (comparatorBtns.length > 0) {
                const first = comparatorBtns[0];
                console.log(`[Hoofs] Premier bouton comparateur: numero=${first.getAttribute('data-show-number')}, visible=${first.offsetParent !== null}`);
            }
            if (allComparators.length > 0 && comparatorBtns.length === 0) {
                // Il y a des .comparator mais sans data-show-number
                allComparators.forEach((el, i) => {
                    if (i < 3) {
                        console.log(`[Hoofs] .comparator[${i}]: tag=${el.tagName}, classes=${el.className}, attrs=${Array.from(el.attributes).map(a => `${a.name}="${a.value}"`).join(', ')}`);
                    }
                });
            }
            if (dataShowNumberEls.length > 0 && comparatorBtns.length === 0) {
                dataShowNumberEls.forEach((el, i) => {
                    if (i < 3) {
                        console.log(`[Hoofs] [data-show-number][${i}]: tag=${el.tagName}, numero=${el.getAttribute('data-show-number')}, classes=${el.className}`);
                    }
                });
            }
            return { trRows: trRows.length, comparatorBtns: comparatorBtns.length, dataShowNumberEls: dataShowNumberEls.length };
        }

        // Attendre que la page soit complètement chargée
        await new Promise(resolve => setTimeout(resolve, 500));
        let state = debugPageState();

        // Essayer d'injecter les boutons
        let injected = await injectButtons();

        // Si rien trouvé, essayer la page détail
        if (!injected) {
            console.log('[Hoofs] Mode liste échoué, tentative mode page détail...');
            await injectHoofsButton();
        }

        // Observer les changements DOM pour les pages dynamiques (résultats de recherche, AJAX, etc.)
        let reinjectTimeout = null;
        const observer = new MutationObserver((mutations) => {
            let shouldReinject = false;

            for (const mutation of mutations) {
                if (mutation.addedNodes.length > 0) {
                    for (const node of mutation.addedNodes) {
                        if (node.nodeType === 1) {
                            // Détecter les nouvelles lignes de tableau
                            if (node.tagName === 'TR' && node.hasAttribute('data-number')) {
                                shouldReinject = true;
                                break;
                            }
                            if (node.querySelector && node.querySelector('tr[data-number]')) {
                                shouldReinject = true;
                                break;
                            }
                            // Détecter les nouveaux boutons comparateur
                            if (node.classList && node.classList.contains('comparator')) {
                                shouldReinject = true;
                                break;
                            }
                            if (node.querySelector && node.querySelector('[data-show-number]')) {
                                shouldReinject = true;
                                break;
                            }
                            // Détecter les tables
                            if (node.tagName === 'TABLE' || node.tagName === 'TBODY') {
                                shouldReinject = true;
                                break;
                            }
                            if (node.querySelector && (node.querySelector('table') || node.querySelector('tbody'))) {
                                shouldReinject = true;
                                break;
                            }
                        }
                    }
                }
                if (shouldReinject) break;
            }

            if (shouldReinject) {
                // Debounce pour éviter trop d'appels
                clearTimeout(reinjectTimeout);
                reinjectTimeout = setTimeout(async () => {
                    console.log('[Hoofs] Contenu dynamique détecté, réinjection...');
                    debugPageState();
                    await injectButtons();
                }, 300);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });

        // Réessayer plusieurs fois pour le contenu chargé dynamiquement
        const retryDelays = [1500, 3000, 5000, 8000];
        for (const delay of retryDelays) {
            if (injected) break;
            await new Promise(resolve => setTimeout(resolve, delay - (retryDelays[retryDelays.indexOf(delay) - 1] || 500)));
            console.log(`[Hoofs] Tentative après ${delay}ms...`);
            state = debugPageState();
            if (state.comparatorBtns > 0 || state.trRows > 0 || state.dataShowNumberEls > 0) {
                injected = await injectButtons();
                if (!injected) {
                    console.log('[Hoofs] injectButtons returned false, trying injectHoofsButton...');
                    await injectHoofsButton();
                }
            }
        }

        // Message final si rien n'a été injecté
        if (!injected) {
            console.log('[Hoofs] Aucun concours détecté sur cette page. Assurez-vous d\'être sur une page avec des résultats de recherche ou une page de détail de concours.');
        }
    }

    // Démarrer
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
