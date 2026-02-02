# FFE Monitor - Extension Chrome

Extension Chrome pour ajouter rapidement des concours FFE à votre surveillance FFE Monitor directement depuis le site ffecompet.ffe.com.

## Installation

### Méthode 1 : Installation manuelle (développeur)

1. Ouvrez Chrome et allez dans `chrome://extensions/`
2. Activez le **Mode développeur** (en haut à droite)
3. Cliquez sur **Charger l'extension non empaquetée**
4. Sélectionnez le dossier `chrome-extension`

### Méthode 2 : Fichier CRX (à venir)

L'extension sera bientôt disponible en téléchargement direct.

## Configuration

1. Cliquez sur l'icône de l'extension (🐴) dans la barre d'outils Chrome
2. Entrez l'URL de votre serveur FFE Monitor (ex: `http://localhost:8000`)
3. Entrez vos identifiants FFE Monitor
4. Cliquez sur **Enregistrer & Connecter**

## Utilisation

### Sur la page d'un concours

Un bouton **🐴 Surveiller** apparaît automatiquement sur les pages de concours FFE. Cliquez dessus pour ajouter le concours à votre surveillance.

### Sur les listes de concours

L'extension ajoute un bouton à côté de chaque lien vers un concours.

### Bouton flottant

Un bouton flottant 🐴 apparaît en bas à droite de la page. Cliquez dessus pour :
- Entrer manuellement un numéro de concours
- Ajouter rapidement n'importe quel concours

## Fonctionnalités

- ✅ Ajout en un clic depuis les pages FFE Compet
- ✅ Détection automatique des numéros de concours
- ✅ Vérification si le concours est déjà surveillé
- ✅ Notifications de confirmation
- ✅ Bouton flottant pour saisie manuelle
- ✅ Reconnexion automatique si la session expire

## Permissions

L'extension requiert les permissions suivantes :
- **storage** : Pour sauvegarder vos identifiants localement
- **activeTab** : Pour injecter les boutons sur les pages FFE Compet
- **host_permissions** : Pour communiquer avec FFE Compet et votre serveur FFE Monitor

## Sécurité

- Vos identifiants sont stockés localement dans Chrome (chrome.storage.sync)
- Les communications avec votre serveur FFE Monitor utilisent des tokens JWT
- Aucune donnée n'est envoyée à des serveurs tiers

## Dépannage

### L'extension ne se connecte pas
- Vérifiez que FFE Monitor est en cours d'exécution
- Vérifiez l'URL du serveur (avec ou sans slash final)
- Vérifiez vos identifiants

### Les boutons n'apparaissent pas
- Actualisez la page (F5)
- Vérifiez que vous êtes bien sur ffecompet.ffe.com
- Ouvrez la console (F12) pour voir les logs `[FFE Monitor]`

## Développement

Structure du projet :
```
chrome-extension/
├── manifest.json      # Configuration de l'extension
├── popup.html         # Interface du popup
├── popup.js           # Logique du popup
├── content.js         # Script injecté sur les pages FFE
├── styles.css         # Styles des éléments injectés
└── icons/             # Icônes de l'extension
```

## Licence

MIT - Voir le fichier LICENSE du projet principal.
