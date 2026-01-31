# Backlog – Projet EngageWatch

## Vision produit

Permettre à un utilisateur non technique de surveiller l’ouverture des engagements de concours FFE spécifiques (par numéro) et de recevoir une notification immédiate dès que le concours s’ouvre à l’engagement ou à la demande de participation.

---

## Épics

* EPIC-01 : Fondation technique & infrastructure
* EPIC-02 : Authentification FFE automatisée
* EPIC-03 : Gestion des concours surveillés
* EPIC-04 : Moteur de surveillance des concours
* EPIC-05 : Notifications temps réel
* EPIC-06 : Interface utilisateur (Web local)
* EPIC-07 : Robustesse, sécurité et fiabilité
* EPIC-08 : Packaging, documentation et livraison

---

## EPIC-01 – Fondation technique & infrastructure

### US-01.1 – Initialisation du projet Python

**Description** : Créer la structure de base du projet.

* Dossiers backend / frontend / data
* Environnement virtuel
* Dépendances listées

**Critères d’acceptation**

* Le projet s’installe avec une seule commande
* Le serveur démarre sans erreur

---

### US-01.2 – Mise en place de FastAPI

**Description** : Initialiser l’API backend.

**Tâches**

* Créer l’application FastAPI
* Endpoint de santé `/health`

**Critères d’acceptation**

* Accès à [http://localhost:8000/health](http://localhost:8000/health)
* Réponse JSON `{"status": "ok"}`

---

### US-01.3 – Base de données SQLite

**Description** : Stocker les concours surveillés.

**Tâches**

* Initialiser SQLite
* Créer la table `concours`

**Schéma**

* id (int, PK)
* numero (int, unique)
* statut (text)
* notifie (bool)
* last_check (datetime)

---

## EPIC-02 – Authentification FFE automatisée

### US-02.1 – Connexion FFE via Playwright

**Description** : Simuler la connexion utilisateur au site FFE.

**Tâches**

* Lancer un navigateur Playwright
* Remplir formulaire de login
* Valider connexion

**Critères d’acceptation**

* L’utilisateur est reconnu comme connecté
* Accès aux pages concours authentifiées

---

### US-02.2 – Persistance de session

**Description** : Conserver la session FFE active.

**Tâches**

* Sauvegarder cookies
* Recharger cookies au démarrage

**Critères d’acceptation**

* Pas de reconnexion nécessaire tant que la session est valide

---

### US-02.3 – Reconnexion automatique

**Description** : Gérer l’expiration de session.

**Critères d’acceptation**

* Reconnexion transparente
* Aucun arrêt de la surveillance

---

## EPIC-03 – Gestion des concours surveillés

### US-03.1 – Ajouter un concours

**Description** : Ajouter un numéro de concours à surveiller.

**API**
POST /concours

**Critères d’acceptation**

* Le concours est stocké
* Pas de doublon possible

---

### US-03.2 – Lister les concours

**Description** : Afficher tous les concours surveillés.

**API**
GET /concours

---

### US-03.3 – Supprimer un concours

**Description** : Retirer un concours de la surveillance.

**API**
DELETE /concours/{numero}

---

## EPIC-04 – Moteur de surveillance des concours

### US-04.1 – Boucle de surveillance asynchrone

**Description** : Vérifier l’état des concours périodiquement.

**Contraintes**

* Intervalle cible : 5–10 secondes

---

### US-04.2 – Accès à la page concours

**Description** : Ouvrir directement la page d’un concours par numéro.

---

### US-04.3 – Détection de l’ouverture

**Description** : Identifier l’apparition des boutons.

**Règles métier**

* Bouton "Engager" → concours amateur ouvert
* Bouton "Demande de participation" → concours international ouvert

**Critères d’acceptation**

* Statut correctement identifié

---

### US-04.4 – Mise à jour du statut

**Description** : Mettre à jour le statut du concours en base.

---

## EPIC-05 – Notifications temps réel

### US-05.1 – Intégration Telegram

**Description** : Envoyer une notification via Telegram.

**Critères d’acceptation**

* Message reçu < 2 secondes après détection

---

### US-05.2 – Anti-doublon de notification

**Description** : Une seule notification par concours.

**Règle**

* Champ `notifie = true` après envoi

---

### US-05.3 – Format du message

**Contenu minimal**

* Numéro du concours
* Type d’ouverture
* Lien direct vers le concours

---

## EPIC-06 – Interface utilisateur (Web local)

### US-06.1 – Page principale

**Description** : Interface accessible sur navigateur.

**Éléments**

* Champ numéro de concours
* Bouton Ajouter
* Tableau des concours

---

### US-06.2 – Affichage des statuts

**Statuts possibles**

* Fermé
* Ouvert – Engagement
* Ouvert – Demande de participation

---

### US-06.3 – Rafraîchissement automatique

**Description** : Mise à jour de l’interface sans rechargement manuel.

---

## EPIC-07 – Robustesse, sécurité et fiabilité

### US-07.1 – Gestion des erreurs réseau

**Description** : Retry automatique en cas d’échec.

---

### US-07.2 – Logs applicatifs

**Description** : Journaliser les événements importants.

---

### US-07.3 – Limitation du polling

**Description** : Éviter surcharge et blocage FFE.

---

## EPIC-08 – Packaging, documentation et livraison

### US-08.1 – Script de lancement

**Description** : Démarrage en une commande.

---

### US-08.2 – README utilisateur

**Contenu**

* Installation
* Lancement
* Ajout d’un concours
* Réception des notifications

---

### US-08.3 – Documentation développeur

**Contenu**

* Architecture
* Choix techniques
* Points de vigilance

---

## Priorisation (MoSCoW)

### Must Have

* Authentification FFE
* Surveillance concours
* Notification unique
* Interface simple

### Should Have

* Reconnexion automatique
* Logs

### Could Have

* Autres canaux de notification
* Filtres avancés

### Won’t Have (v1)

* Engagement automatique
* Application mobile

---

## Définition of Done (DoD)

* Code fonctionnel sans intervention manuelle
* Interface utilisable par un non technique
* Notification envoyée à l’ouverture réelle
* Pas de doublons
* Application stable sur plusieurs heures
