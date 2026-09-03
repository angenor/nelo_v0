# ADR 017 — FastAPI et Pydantic remplacent Rust et Actix

**Statut** : accepté · **Date** : 2026-08-21 · **Change la pile serveur, rien du domaine**

> **Renverse [ADR 004](004-rust-en-facade-python-au-sidecar.md)**, qui devient sans objet.
> **Amende [ADR 000](000-nuxt-et-rust-une-seule-application.md),
> [ADR 003](003-monolithe-modulaire-microservices-plus-tard.md),
> [ADR 006](006-le-contrat-openapi-fait-foi.md), [ADR 008](008-local-d-abord-vps-ensuite.md),
> [ADR 010](010-le-referentiel-d-evaluation-est-une-donnee-versionnee.md) et
> [ADR 012](012-le-cloisonnement-est-une-frontiere-de-compilation.md).** Chacun porte sa note en
> tête ; **aucun corps n'a été réécrit.**

## Contexte

[ADR 004](004-rust-en-facade-python-au-sidecar.md) tranchait une question locale : Rust en façade,
Python cantonné à un sidecar d'inférence, parce que la latence et l'empreinte mémoire comptent sur
des serveurs contraints et à prix de vente en francs CFA. Le raisonnement était juste, et il l'est
toujours pris isolément.

Ce qui a changé n'est pas la mesure, c'est le cadre. **Nelo n'est pas le seul produit du
portefeuille** : trois autres projets se construisent en parallèle, avec le même développeur seul, le
même Nuxt en façade, la même méthode Spec Kit. Trois d'entre eux ont déjà FastAPI côté serveur. Nelo
seul reste sur une seconde langue de serveur, une seconde chaîne de build, un second jeu d'habitudes
de test et de mise en production — **et un service de plus à opérer**, le sidecar.

Le coût d'un langage n'est pas dans son écriture. Il est dans le contexte qu'il faut porter pour y
revenir après trois semaines passées ailleurs.

## Décision

**FastAPI et Pydantic portent la totalité de la logique métier et de l'API.** SQLAlchemy **Core** et
`asyncpg` pour l'accès aux données — jamais l'ORM, le SQL reste écrit et non deviné. Alembic pour les
migrations, **un dossier par module**. `uv` pour l'environnement et le verrouillage, `ruff` pour le
style et l'analyse, `pytest` pour les tests.

**Le sidecar disparaît.** Les deux capacités IA du MVP — C1 rédaction assistée, C5 extraction
documentaire — deviennent `modules/socle/assistance/`, un paquet appelé comme les autres. Elles sont
dans le socle parce que plusieurs modules métier les appellent.

**La famille métier est renommée `modules/metier/`.** Elle s'appelait `modules/` et vit désormais
dans `modules/` ; `modules/modules/` n'est pas un chemin qu'on relit deux fois de la même façon.

Le reste ne bouge pas : Nuxt en façade, PostgreSQL, Valkey, Garage, l'outbox et son worker en
processus, le monolithe modulaire et son schéma par module, le design, le domaine, les tranches.

## Conséquences

- **Un service de moins à déployer, à superviser et à arrêter.** Le `compose.yml` passe de quatre
  services à trois : postgres, valkey, garage.
- **La propriété « le produit tourne sans IA » ne disparaît pas, elle change de forme.** Ce n'était
  pas « le sidecar est éteint », c'était « l'établissement n'a aucune fonctionnalité IA et le produit
  reste entier ». Un **réglage serveur** du catalogue de paramètres suspend l'assistance à sa portée ;
  suspendue, les appréciations se saisissent à la main, l'import se fait par correspondance manuelle
  de colonnes, et **l'affordance disparaît de l'écran** au lieu d'être grisée. **C'est toujours un
  test, pas une intention.**
- **Le `422` de Pydantic devient un code de première classe du contrat**, pas une fuite
  d'implémentation — [03-api.md § 1.8](../03-api.md).
- **Une porte naît** : **P-12**, toute requête SQL du produit s'exécute contre une base fraîchement
  migrée. Elle n'existait pas parce que la compilation la rendait inutile.
- **Deux portes changent de nature sans changer de numéro** : P-04 et P-11 étaient données par cargo,
  elles deviennent des tests de graphe d'imports, à écrire et à maintenir.
- La documentation parle de **paquets**, plus de crates. `Cargo.lock` devient `uv.lock`.

**Le prix accepté** — quatre pertes, et aucune n'est un détail :

1. **L'empreinte mémoire et la latence.** L'argument de l'ADR 004 était juste et ne disparaît pas :
   sérialisation Python, GIL, boucle asyncio, là où Actix répondait sous la milliseconde. Sur des
   serveurs contraints et avec un prix par élève en francs CFA, chaque Mo a un coût dans la marge.
   **On paie une machine plus grosse pour économiser un langage.**
2. **`sqlx` vérifiait les requêtes SQL à la compilation. Python n'a aucun équivalent.** Une colonne
   renommée par une migration ne casse plus rien avant l'appel, et l'appel peut n'arriver qu'en
   production. La compensation est la porte **P-12** — **plus tard et plus lent qu'une erreur de
   compilation**, et c'est exactement la nature de la perte.
3. **La hiérarchie de paquets était garantie par cargo.** Un crate du socle ne pouvait pas dépendre
   d'un module ; le graphe était vérifié par l'outil de build, gratuitement. **P-04 devient un test à
   écrire, à maintenir, et qu'on peut désactiver un jour de fatigue.**
4. **Le cloisonnement de `protection` perd sa garantie de compilation.** C'est la perte la plus
   sensible de ce projet, et elle porte sur des **signalements de protection de l'enfance**. Le
   compilateur *refusait* la dépendance ; en Python, un `import` traversant s'exécute parfaitement.
   Trois verrous la compensent — aucune déclaration de dépendance, un test de graphe d'imports qui
   voit aussi les imports différés, un `__init__.py` qui n'expose rien hors de l'interface de service
   ([ADR 012](012-le-cloisonnement-est-une-frontiere-de-compilation.md), porte **P-11**).
   **Trois verrous valent mieux qu'un, et ils restent plus faibles qu'un compilateur.** Un
   compilateur refusait ; un test signale. Écrire l'inverse serait se mentir.

**Ce qu'on gagne**, et qui a emporté la décision : **une seule langue de serveur pour les quatre
projets du portefeuille** · la validation Pydantic à l'exécution, face à des postes d'établissement
qui ne se mettent pas à jour · **la disparition du sidecar, donc d'un service à opérer** · un
écosystème plus court pour un développeur seul.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Garder Rust et le sidecar | Le raisonnement de l'ADR 004 tient, mais il ne pèse pas contre une seconde langue de serveur à maintenir seul sur quatre projets |
| Rust en façade, sans sidecar, l'inférence appelée directement | Ferme l'écosystème Python là où il est le plus utile, et garde le coût du polyglotte sans son bénéfice |
| FastAPI en façade **et** conserver un sidecar | Un service de plus pour une frontière qui n'existe plus : même langage, même processus, même déploiement |
| L'ORM SQLAlchemy plutôt que Core | Le SQL cesse d'être écrit pour être deviné, et la porte P-12 perd son objet |
| Repousser la bascule après le MVP | Une pile se change avant la première ligne de code ou trois ans plus tard. Le dépôt ne contient aujourd'hui aucun code : c'est le seul moment où la bascule est gratuite |
