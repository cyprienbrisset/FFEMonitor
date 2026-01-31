# EngageWatch — Guide Utilisateur

## Surveillance Automatique des Concours FFE

---

## Qu'est-ce qu'EngageWatch ?

**EngageWatch** est un outil de surveillance automatique qui vous alerte instantanément dès qu'un concours équestre FFE (Fédération Française d'Équitation) ouvre ses engagements.

### Le problème résolu

Les places aux concours FFE sont limitées et les engagements ouvrent à des moments variables. Sans surveillance constante, vous risquez de manquer l'ouverture et de ne pas pouvoir inscrire vos chevaux.

**EngageWatch surveille en continu les concours de votre choix** et vous envoie une notification immédiate par **Telegram** et/ou **Email** dès que le bouton "Engager" ou "Demande de participation" apparaît.

---

## Accéder à l'application

### Adresse de connexion

Ouvrez votre navigateur et rendez-vous à l'adresse :

```
http://[adresse-du-serveur]:8000
```

> L'adresse exacte vous sera communiquée par votre administrateur.

---

## Connexion

### Écran de connexion

À l'ouverture de l'application, vous arrivez sur l'écran de connexion :

1. **Identifiant** : Saisissez votre nom d'utilisateur
2. **Mot de passe** : Saisissez votre mot de passe
3. Cliquez sur **"Se connecter"**

![Écran de connexion](docs/login.png)

> Vos identifiants vous sont fournis par votre administrateur.

### Déconnexion

Pour vous déconnecter, cliquez sur le bouton **"Déconnexion"** en haut à droite de l'écran principal.

---

## Interface principale

Une fois connecté, vous accédez au tableau de bord composé de plusieurs sections :

### 1. État du Système

Cette section affiche l'état de fonctionnement de l'application :

| Indicateur | Signification |
|------------|---------------|
| 🟢 **Connexion FFE** : Connecté | L'application est connectée au site FFE |
| 🔴 **Connexion FFE** : Déconnecté | Problème de connexion au site FFE |
| 🟢 **Surveillance** : Active | La surveillance des concours fonctionne |
| 🔴 **Surveillance** : Inactive | La surveillance est arrêtée |

La **date de dernière mise à jour** indique quand les données ont été actualisées.

### 2. Nouveau Concours

Pour ajouter un concours à surveiller :

1. Saisissez le **numéro du concours** dans le champ
2. Cliquez sur **"Surveiller"**

> Le numéro du concours se trouve dans l'URL de la page FFE :
> `https://ffecompet.ffe.com/concours/123456` → le numéro est **123456**

### 3. Compteur

Affiche le **nombre total de concours** actuellement surveillés.

### 4. Liste des Concours

Affiche tous les concours que vous surveillez avec leurs informations :

| Information | Description |
|-------------|-------------|
| **Numéro** | Numéro du concours (cliquable pour accéder à la page FFE) |
| **Statut** | État actuel du concours |
| **Notification** | Si vous avez été notifié de l'ouverture |
| **Dernière vérification** | Date/heure de la dernière vérification |

#### États possibles d'un concours

| Statut | Signification |
|--------|---------------|
| **Fermé** | Les engagements ne sont pas encore ouverts |
| **Engagement** | Le bouton "Engager" est disponible (concours amateur) |
| **Demande** | Le bouton "Demande de participation" est disponible (concours international) |

### Retirer un concours

Pour arrêter la surveillance d'un concours, cliquez sur le bouton **×** à droite de la carte du concours.

---

## Notifications

### Comment ça fonctionne ?

Dès qu'un concours surveillé passe de l'état "Fermé" à "Engagement" ou "Demande", vous recevez une notification immédiate.

### Canaux de notification

#### Telegram (recommandé)

Vous recevez un message instantané sur Telegram avec :
- Le numéro du concours
- Le type d'ouverture (Engagement ou Demande)
- Un lien direct vers la page du concours

#### Email (optionnel)

Si configuré, vous recevez également un email avec les mêmes informations.

### Notification unique

**Chaque concours ne génère qu'une seule notification.** Une fois notifié, le concours passe en état "Notifié" et ne déclenchera plus d'alerte, même si vous le laissez dans la liste.

---

## Trouver le numéro d'un concours

### Méthode 1 : Depuis le calendrier FFE

1. Allez sur [ffecompet.ffe.com](https://ffecompet.ffe.com)
2. Recherchez votre concours dans le calendrier
3. Cliquez dessus pour ouvrir sa page
4. Le numéro est dans l'URL : `ffecompet.ffe.com/concours/**123456**`

### Méthode 2 : Depuis la page du concours

Le numéro apparaît généralement en haut de la page du concours sur le site FFE.

---

## Questions fréquentes

### À quelle fréquence les concours sont-ils vérifiés ?

Les concours sont vérifiés **toutes les 5 secondes** par défaut. Vous pouvez donc être notifié quelques secondes après l'ouverture réelle.

### Puis-je surveiller plusieurs concours ?

Oui, vous pouvez surveiller autant de concours que vous le souhaitez. L'application vérifie chaque concours de manière séquentielle.

### Que faire si je ne reçois pas de notifications ?

1. Vérifiez que la **Connexion FFE** est "Connecté" (indicateur vert)
2. Vérifiez que la **Surveillance** est "Active" (indicateur vert)
3. Vérifiez vos paramètres Telegram/Email auprès de votre administrateur

### Le concours est ouvert mais je n'ai pas été notifié ?

Si le concours était déjà ouvert quand vous l'avez ajouté, la notification a été envoyée immédiatement. Vérifiez vos messages Telegram ou emails.

### Puis-je m'engager directement depuis l'application ?

Non, EngageWatch est un outil de **surveillance uniquement**. Une fois notifié, vous devez vous rendre sur le site FFE pour procéder à l'engagement.

### L'application fonctionne-t-elle 24h/24 ?

Oui, tant que le serveur est en fonctionnement, l'application surveille les concours en continu, jour et nuit.

---

## Besoin d'aide ?

Contactez votre administrateur pour :
- Problèmes de connexion
- Configuration des notifications
- Questions techniques

---

<div align="center">

**EngageWatch** — *Ne manquez plus jamais l'ouverture d'un concours*

</div>
