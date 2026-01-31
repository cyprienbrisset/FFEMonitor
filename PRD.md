PRD – Outil de surveillance d’ouverture des concours FFE
1. Contexte & objectif
1.1 Contexte

Les concours équestres publiés sur https://ffecompet.ffe.com/concours
 ouvrent leurs engagements à des moments variables.
Les places étant limitées, la rapidité d’engagement est un facteur critique.

Le site FFE :

est accessible publiquement pour consulter les concours

nécessite une connexion utilisateur pour voir le statut réel d’ouverture

n’expose aucune API officielle

affiche l’ouverture via l’apparition de boutons spécifiques :

« Engager » (concours amateur)

« Demande de participation » (concours international)

1.2 Problème utilisateur

La cliente souhaite :

surveiller plusieurs concours précis

être alertée le plus rapidement possible dès leur ouverture

sans intervention technique

via une interface simple

2. Objectifs produit
2.1 Objectif principal

Permettre à un utilisateur non technique de :

saisir un ou plusieurs numéros de concours

lancer une surveillance automatique

recevoir une notification immédiate à l’ouverture des engagements

2.2 Objectifs secondaires

éviter les notifications multiples pour un même concours

afficher l’état courant de chaque concours

rester robuste face aux changements mineurs du site FFE

3. Périmètre fonctionnel
3.1 Inclus

Connexion automatisée à un compte FFE

Surveillance par numéro de concours

Détection des boutons d’ouverture

Notifications push

Interface utilisateur locale simple

3.2 Exclus

Engagement automatique

Contournement de sécurité FFE

Garantie de délai strict < 10 secondes

Application mobile native

4. Utilisateurs cibles
4.1 Utilisateur final

Cavaliers / gestionnaires d’écurie

Niveau technique : faible

Attente principale : rapidité & simplicité

4.2 Utilisateur technique

Développeur / intégrateur

Déploie et maintient l’outil

5. Parcours utilisateur (User Flow)

L’utilisateur lance l’application

Il se connecte une fois à son compte FFE

Il accède à une interface web locale

Il saisit un numéro de concours

Le concours apparaît dans la liste surveillée

L’application vérifie l’état du concours en continu

Lors de l’ouverture :

notification envoyée

statut mis à jour dans l’interface

6. Interface utilisateur (UI)
6.1 Accès

Application web locale : http://localhost:8000

6.2 Éléments UI requis

Champ texte : numéro du concours

Bouton : « Ajouter »

Tableau listant :

numéro du concours

statut (Fermé, Ouvert – Engagement, Ouvert – Demande)

état notification (envoyée / non envoyée)

6.3 Contraintes UX

Pas de jargon technique

Aucune configuration manuelle

Feedback visuel immédiat

7. Logique métier
7.1 Types de concours
Type	Indicateur d’ouverture
Amateur	Bouton Engager
International	Bouton Demande de participation
7.2 Règles de notification

Une notification unique par concours

Notification envoyée dès la première détection

Aucun renvoi même si le statut reste ouvert

7.3 Fréquence de vérification

Intervalle cible : 5 à 10 secondes

Ajustable côté code

Priorité à la rapidité sans surcharge excessive

8. Architecture technique
8.1 Stack imposée

Python 3.10+

Playwright (navigation automatisée)

FastAPI (backend + API)

SQLite (stockage local)

HTML / CSS / JS minimal (frontend)

8.2 Justification Playwright

Gestion complète du JavaScript

Support cookies et sessions

Simulation fidèle d’un navigateur réel

Meilleure tolérance aux protections anti-bot

9. Backend – Composants
9.1 Module Authentification

Connexion FFE via Playwright

Sauvegarde des cookies de session

Reconnexion automatique si session expirée

9.2 Module Surveillance

Boucle asynchrone

Navigation directe vers la page du concours

Détection DOM des boutons cibles

9.3 Module Notifications

Support Telegram (prioritaire)

Architecture extensible (email, webhook)

10. Modèle de données
10.1 Table concours
Champ	Type	Description
id	INTEGER	clé primaire
numero	INTEGER	numéro du concours
statut	TEXT	fermé / engagement / demande
notifie	BOOLEAN	notification envoyée
last_check	DATETIME	dernière vérification
11. API interne (FastAPI)
11.1 Ajouter un concours

POST /concours

{
  "numero": 123456
}

11.2 Liste des concours

GET /concours

11.3 Supprimer un concours

DELETE /concours/{numero}

12. Contraintes techniques

Pas d’accès API officiel FFE

Dépendance au DOM FFE

Risque de changement de labels ou structure HTML

Risque de blocage en cas de polling excessif

13. Sécurité & conformité

Identifiants FFE stockés localement

Aucun partage externe

Aucune automatisation d’engagement

Utilisation sous responsabilité de l’utilisateur

14. Performance & fiabilité
14.1 Objectifs

Latence de détection : 5–15 secondes

Notification < 2 secondes après détection

Surveillance simultanée : 5–20 concours

14.2 Gestion des erreurs

Retry automatique en cas d’erreur réseau

Journalisation des échecs

Reconnexion silencieuse

15. Évolutions futures (hors périmètre)

Filtres par région / discipline

Historique d’ouverture

Multi-comptes FFE

Déploiement serveur distant

Application mobile

16. Critères de succès

L’utilisateur reçoit une notification avant l’ouverture manuelle visible

L’interface est utilisable sans aide technique

Aucun doublon de notification

Stabilité sur plusieurs jours d’exécution

17. Livrables attendus

Code Python documenté

Interface web fonctionnelle

Script de lancement

README utilisateur non technique