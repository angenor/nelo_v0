# ADR 001 — Le hors-connexion est différé, pas exclu

**Statut** : accepté · **Date** : 2026-08-21 · **Le plus structurant du corpus**

## Contexte

La connectivité dans les salles de classe est intermittente, lente et coûteuse. Un fonctionnement
hors connexion complet — cache d'écriture, file d'actions locale, réconciliation au retour du réseau —
est ce qui répond le mieux à cette réalité.

Il coûte aussi, à lui seul, plus que le reste du produit réuni :

- une classification de chaque entité selon sa tolérance à l'écriture concurrente ;
- une file d'actions persistante, avec ordre, rejeu et idempotence de bout en bout ;
- un arbitrage humain des **écritures orphelines** — une note saisie hors ligne sur une période que le
  conseil de classe a clôturée pendant ce temps ;
- une gestion de la dérive d'horloge des terminaux, qui fausse l'ordre des saisies ;
- la purge des caches contenant des données de mineurs sur un appareil partagé ;
- et le constat qu'**aucune plateforme ne garantit la synchronisation en arrière-plan** : la file se
  vide au retour au premier plan, partout.

## Décision

**Pas de mode hors connexion au MVP. La décision est réexaminable une fois le produit installé et la
couverture réseau réelle mesurée en salle de classe.**

**Différé n'est pas exclu.** Quatre fondations se posent maintenant, parce qu'elles ne se rattrapent
pas après coup :

| Fondation | Pourquoi maintenant |
|---|---|
| **Identifiant généré par le client** — UUID v7 sur toute création | Un identifiant attribué par le serveur interdit de créer hors ligne. Le changer plus tard, c'est migrer toutes les clés étrangères |
| **Idempotence avec mémorisation de la réponse** — 24 h | C'est le mécanisme du rejeu. Il sert déjà aujourd'hui, sur réseau lent |
| **Horodatage faisant autorité côté serveur, horodatage client conservé** | Sans les deux, la réconciliation future n'a aucune base pour arbitrer |
| **Journal d'événements immuable et permanent** (outbox) | Une file de messages purgée ne permet pas de rejouer un historique. Un grand livre, si |

## Conséquences

Ce que le MVP livre **à la place** du hors-connexion, et qui n'est pas un lot de consolation :

- **Budget de poids par écran** — l'appel est le plus léger du produit (porte P-10).
- **Écriture idempotente et reprise** — le formulaire est restitué tel quel au retour, l'envoi est
  rejoué. Aucune saisie perdue sur coupure.
- **Enregistrement au fil de l'eau** — par petits lots, pas en un envoi de fin de séance. Perdre le
  réseau à la dernière ligne ne coûte jamais quarante saisies.
- **États explicites** — l'utilisateur voit en permanence si sa saisie est sur le serveur ou en
  attente. *C'est là que se perd la confiance.*
- **Procédure papier de secours** — toutes les listes critiques sont imprimables à l'avance, et la
  procédure est documentée **dans la formation**, pas découverte le jour où le réseau tombe.

**Le prix accepté** : un établissement sans réseau utilisable en classe fera l'appel sur papier, puis
la saisie différée au bureau. C'est un compromis acceptable, mais **il doit être identifié avant la
vente**, pas après — c'est la première des questions à poser aux pilotes.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Hors-connexion complet dès le MVP | Coûte plus que le reste du produit réuni, et n'est pas ce qui fait acheter |
| Cache de lecture seule | Utile, mais ne résout pas le cas qui compte : la saisie |
| Serveur local dans l'établissement | Électricité intermittente, sécurité physique, maintenance à distance impossible |
