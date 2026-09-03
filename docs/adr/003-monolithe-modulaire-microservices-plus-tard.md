# ADR 003 — Monolithe modulaire, microservices plus tard

**Statut** : accepté · **Date** : 2026-08-21

> **Amendé par [ADR 017](017-fastapi-et-pydantic-remplacent-rust-et-actix.md)** — la décision tient
> intégralement ; deux détails vieillissent. « Crate » se lit **paquet**, et la famille `modules/`
> s'appelle désormais `modules/metier/`. Surtout : **le test structurel de la hiérarchie n'est plus
> donné par cargo**, c'est un test de graphe d'imports à écrire et à maintenir (porte P-04).

## Contexte

Le catalogue décrit une plateforme large : scolarité, évaluation, vie scolaire, finance,
communication, protection de l'enfance. La tentation est de la découper en services dès le départ,
« pour être prêt ».

Elle est mauvaise pour trois raisons mesurables : complexité opérationnelle disproportionnée au
démarrage, latence réseau inutile quand tout tient sur un serveur, et surtout **impossibilité de
définir de bonnes frontières de service sans retour du terrain**. Un découpage prématuré fige des
frontières fausses.

## Décision

**Un monolithe modulaire.** Les frontières modulaires d'aujourd'hui sont les futures frontières de
services.

**La condition — et c'est la seule qui compte** : les modules ne partagent **jamais** de transaction
de base de données.

1. Un schéma Postgres par module.
2. Aucune requête ne joint deux schémas de modules différents ; les lectures inter-modules passent par
   un trait exposé. `finance` ne fait pas de `SELECT` dans `scolarite.eleve`.
3. Aucune transaction SQL ne couvre deux modules. Les opérations inter-modules sont des séquences avec
   compensation explicite.
4. Toute transition d'état métier écrit un événement outbox dans la même transaction SQL.

## Conséquences

- Un seul binaire, un seul VPS, un worker in-process qui consomme l'outbox. Aucune file de messages.
- L'extraction future d'un service est un changement de transport, pas une réécriture.
- Un test structurel vérifie la hiérarchie de dépendance des crates (porte P-04).
- Le module `protection` va plus loin : **aucun crate n'en dépend**
  ([ADR 012](012-le-cloisonnement-est-une-frontiere-de-compilation.md)).

**Le prix accepté** : la règle « pas de transaction partagée » interdit des jointures qui seraient
naturelles et rapides. Facturer une fratrie exige d'interroger `scolarite` par son interface avant
d'écrire dans `finance` — deux allers-retours là où une jointure suffirait. **C'est le coût de
l'extraction future, et il se paie tous les jours.** Il est payé sciemment.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Microservices dès le départ | Frontières figées avant le retour du terrain, complexité opérationnelle pour un développeur seul |
| Monolithe sans frontières internes | Rend l'extraction impossible, quelle que soit la propreté des traits |
| Bus de messages dès le MVP | Une table `outbox` et un worker suffisent et coûtent bien moins cher à opérer |
