# ADR 007 — Valkey pour l'éphémère, et rien d'autre

**Statut** : accepté · **Date** : 2026-08-21

## Contexte

Le produit a besoin d'un magasin rapide pour les sessions, la liste de révocation de jetons, la
limitation de débit, les verrous, et l'ordonnancement du worker outbox. Redis a changé de licence en
2024 ; **Valkey** en est le fork maintenu sous licence BSD, piloté par la Linux Foundation, et son
protocole est compatible.

## Décision

**Valkey**, et une règle d'usage stricte : **aucune donnée métier durable n'y vit jamais.**

Ce qui y est autorisé :

| Usage | Pourquoi c'est légitime |
|---|---|
| Sessions et liste de révocation | Reconstructible : au pire, tout le monde se reconnecte |
| Limitation de débit | Une fenêtre perdue n'a aucune conséquence |
| Verrous courts | Reconstructible par définition |
| Ordonnancement du worker outbox | **L'état durable est en Postgres** ; Valkey ne porte que l'ordre de passage |
| Mémorisation des réponses idempotentes (24 h) | Perdre la mémorisation dégrade le rejeu en réexécution, pas en corruption — l'écriture reste protégée par ses contraintes |
| Cache sémantique des réponses IA | Reconstructible, et c'est ce qui rend le coût d'inférence tenable |

**Le test** : si perdre Valkey entièrement fait perdre autre chose que du confort, c'est que quelque
chose de durable y a été rangé par erreur.

## Conséquences

- Une remise à zéro de Valkey est sans conséquence métier — propriété qu'on vérifie une fois.
- Licence BSD, sans ambiguïté pour un produit propriétaire vendu par abonnement.
- Les clients Redis existants fonctionnent : le protocole est compatible.

**Le prix accepté** : la mémorisation idempotente en Valkey signifie qu'après une perte, un rejeu
réexécute au lieu de renvoyer la réponse mémorisée. Les écritures concernées portent donc **aussi**
une contrainte d'unicité en base — la ceinture en plus des bretelles, sur le seul cas où la
distinction compte.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Redis | Licence RSAL/SSPL depuis 2024, ambiguë pour un éditeur commercial |
| Postgres seul, avec `SKIP LOCKED` | Tenable pour les files, mais la limitation de débit et les sessions y coûtent des écritures inutiles |
| Un service géré | Contredit [ADR 008](008-local-d-abord-vps-ensuite.md) : rien ne doit être requis pour développer |
