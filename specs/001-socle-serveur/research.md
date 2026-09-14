# Recherche — T0a, le socle serveur

**Phase 0 du plan** · 2026-09-10 · Chaque décision cite ce dont elle dérive. Rien n'est tranché
ici qui contredise [docs/01-stack.md](../../docs/01-stack.md), [docs/02-domaine.md](../../docs/02-domaine.md),
[docs/03-api.md](../../docs/03-api.md) ou la [constitution](../../.specify/memory/constitution.md) ;
ce qui manquait au corpus est proposé comme diff explicite en fin de fichier, jamais appliqué en
silence — à une exception près, nommée en R-20.

## R-01 — Python 3.14

- **Décision** : Python 3.14, la dernière version stable, épinglée par `requires-python = "==3.14.*"`
  et `.python-version`.
- **Motif** : la règle de version de [01-stack.md § 1](../../docs/01-stack.md) est « la dernière
  version stable de chaque brique, sauf conflit constaté ». Aucun conflit : les roues `cp314` existent
  pour `asyncpg` 0.31.0 et `pydantic-core` 2.49.0 (vérifié sur PyPI le 2026-09-10). Et 3.14 apporte
  `uuid.uuid7()` en bibliothèque standard — l'identifiant de requête de
  [03-api.md § 1.3](../../docs/03-api.md) se valide sans dépendance tierce.
- **Écartées** : 3.13 (stable, mais plus « dernière ») ; 3.15 (alpha).

## R-02 — Versions épinglées exactement

Relevées le 2026-09-10 ; l'implémentation réépingle si une version stable plus récente est parue
d'ici là, et `uv.lock` fige le tout ([01-stack.md § 1](../../docs/01-stack.md), porte P-02).

| Brique | Version | Licence | Rôle |
|---|---|---|---|
| `fastapi` | 0.141.1 | MIT | API, OpenAPI généré |
| `pydantic` | 2.13.5 | MIT | frontière de validation |
| `pydantic-settings` | 2.15.0 | MIT | configuration par variables d'environnement |
| `uvicorn` | 0.52.4 | BSD-3 | serveur ASGI (`fastapi dev` s'appuie dessus) |
| `sqlalchemy` | 2.0.52 | MIT | **Core** seulement |
| `asyncpg` | 0.31.0 | Apache-2.0 | pilote PostgreSQL |
| `alembic` | 1.19.2 | MIT | migrations, un dossier par module |
| `valkey` | 6.1.1 | MIT | client Valkey (fork officiel de redis-py par valkey-io) |
| `pytest` | 9.1.1 | MIT | tests |
| `pytest-asyncio` | 1.4.0 | Apache-2.0 | tests asynchrones |
| `httpx` | 0.28.1 | BSD-3 | client de test ASGI |
| `coverage` | 7.16.0 | Apache-2.0 | support de la porte P-12 (voir R-11) |
| `ruff` | 0.16.6 | MIT | style, analyse, règle S608 |
| `import-linter` | 2.15 (`grimp` 3.17) | BSD-2 | portes P-04 et P-11 (voir R-04) |
| `pip-licenses` | 5.5.5 | MIT | porte P-07 côté Python |
| `hatchling` | 1.32.0 | MIT | backend de build de la racine |
| `openapi-typescript` (npm) | 7.13.0 | MIT | client typé (voir R-10) |
| image `postgres` | `18.6-alpine` | PostgreSQL | [01-stack.md § 1](../../docs/01-stack.md) : PostgreSQL 18 |
| image `valkey/valkey` | `9.1.2-alpine` | BSD-3 | magasin éphémère |
| image `dxflrs/garage` | `v2.4.1` | AGPL-3.0 **côté serveur, non redistribué** | stockage d'objets |

> **Garage est sous AGPL.** Il n'est ni lié, ni embarqué, ni redistribué : c'est un service que le
> produit appelle par l'API S3, comme PostgreSQL. La porte P-07 contrôle les **dépendances** des
> lockfiles ([01-stack.md § 9](../../docs/01-stack.md)), pas les images de la composition. Le choix
> de Garage est celui du corpus ; ce plan le note pour que personne ne s'en étonne à la revue.

Toutes les dépendances Python et npm sont sous MIT, Apache-2.0 ou BSD : conformes au régime
autorisé de [01-stack.md § 9](../../docs/01-stack.md).

## R-03 — Disposition de l'espace de travail : racine installable, paquets déclaratifs

- **Décision** : un seul projet `uv` installable, à la racine, qui déclare `packages = ["modules",
  "api"]` pour son backend de build. `modules/`, `modules/socle/`, `modules/metier/`,
  `modules/segments/` sont des paquets d'espace de noms (PEP 420, sans `__init__.py`) ; chaque paquet
  feuille garde son `__init__.py` **à l'emplacement littéral du corpus** —
  `modules/metier/protection/__init__.py`, `modules/socle/tenants/__init__.py`. **Chaque paquet est en
  plus un membre de l'espace de travail `uv`**, avec son propre `pyproject.toml` marqué
  `[tool.uv] package = false` : il n'est pas installé, mais il **déclare ses dépendances internes**, et
  `uv.lock` le connaît.
- **Motif** : c'est ce qui donne une réalité mécanique au **premier verrou** de la porte P-11 —
  « aucun paquet ne déclare `protection` dans ses dépendances »
  ([01-stack.md § 7.4](../../docs/01-stack.md), FR-006, scénario 4 de US4). Sans `pyproject.toml` par
  paquet, ce verrou n'aurait rien à inspecter, et la porte échouerait à sa propre règle « une porte
  qui n'a rien inspecté n'a rien prouvé » (FR-043). Le test de graphe (R-04) vérifie de surcroît que
  **toute arête d'import est déclarée** dans le `pyproject.toml` du paquet importateur : la
  déclaration cesse d'être décorative.
- **Vérifié** : les deux dispositions ont été montées dans un bac à sable avec `uv` 0.10.12. Celle où
  chaque paquet est *installable* (`packages = ["."]`) ne met sur `sys.path` que le dossier du paquet
  lui-même ; `import modules.socle.tenants` ne tenait que grâce au répertoire courant et casse depuis
  tout autre répertoire. La disposition retenue importe depuis n'importe où : le `.pth` de
  l'installation éditable pointe la racine.
- **Conséquence sur les commandes** : le serveur se lance depuis la racine,
  `uv run fastapi dev api/main.py`. [01-stack.md § 3](../../docs/01-stack.md) écrit
  `cd api && uv run fastapi dev` : diff proposé en fin de fichier.
- **Écartées** : un projet unique sans membres (verrou 1 vide) ; des paquets installables en `src/`
  (les chemins `modules/metier/protection/__init__.py` du corpus deviendraient
  `modules/metier/protection/src/protection/__init__.py`, et le nom d'import perdrait sa famille).

## R-04 — Le graphe d'imports : import-linter, plus un test de chaînes

- **Décision** : `import-linter` porte deux contrats dans le `pyproject.toml` racine : un contrat
  **layers** pour la hiérarchie de [01-stack.md § 2.4](../../docs/01-stack.md) —
  `api` › `modules.segments` › `modules.metier` › `modules.socle` › `{modules.shared, modules.domaine}`
  (les deux derniers indépendants, aucun import sortant) — et un contrat **forbidden** :
  aucun module hors de `modules.metier.protection` n'importe `modules.metier.protection`. Un test
  `pytest` appelle l'API de `grimp` pour **annoncer le nombre de modules inspectés et échouer s'il
  est nul** (FR-008), pour vérifier que chaque arête est déclarée (R-03), et pour la troisième
  forme d'import : **le chemin écrit en chaîne**. Ce dernier point est un parcours AST de tous les
  fichiers `.py` hors `modules/metier/protection/` — toute constante de chaîne contenant
  `modules.metier.protection` ou `metier/protection` échoue, y compris dans un `importlib.import_module`
  ou un `__import__`.
- **Motif** : `grimp` construit le graphe depuis l'AST complet, **imports au fond des fonctions
  compris** — c'est la deuxième forme exigée par FR-005. Il ne voit pas les chaînes : d'où le test
  complémentaire, dont le cas limite « `protection` s'importe lui-même » est la seule exception, et
  la porte le sait (edge case de la spec).
- **Le troisième verrou** — la surface de `modules/metier/protection/__init__.py` — est un test qui
  importe le module et vérifie que `__all__` ne contient que l'interface de service : aucun nom de
  table, aucun objet `Table` SQLAlchemy, aucune fonction d'accès aux données, aucune session.
- **Écartées** : un `grep` seul (ne distingue pas un import différé d'un commentaire) ; `pydeps`
  (visualise, ne contraint pas).

## R-05 — Les en-têtes se lisent en middleware, l'enveloppe remplace le gestionnaire de validation

- **Décision** : deux middlewares ASGI **purs** (pas `BaseHTTPMiddleware`) : le premier lit
  `X-Nelo-Etablissement` et résout le tenant (R-16) ; le second lit `X-Nelo-Requete` sur `POST`,
  `PUT`, `PATCH`, `DELETE`, met le corps en mémoire pour l'empreinte, et porte l'idempotence (R-06).
  Le gestionnaire de `RequestValidationError` de FastAPI est **remplacé** pour rendre l'enveloppe de
  [03-api.md § 1.6](../../docs/03-api.md) avec `code = VAL_SCHEMA_INVALIDE`, `champ` = le premier
  chemin fautif, `details.champs` = la liste `{chemin, motif}` de **tous** les champs fautifs. Un
  gestionnaire d'exception non prévue rend `500 API_ERREUR_INTERNE` sans aucun détail technique.
- **Motif** : [03-api.md § 1.2 et § 1.3](../../docs/03-api.md) sont explicites et opposables :
  déclarer l'un de ces en-têtes en dépendance `Header(...)` ferait sortir le refus en `422` au lieu du
  `400` du contrat. `BaseHTTPMiddleware` ne permet pas de relire le corps ni de capturer la réponse
  proprement ; un middleware ASGI le fait.
- **Le `/openapi.json` doit tout de même annoncer ces en-têtes** pour que le client typé les porte :
  ils sont ajoutés à la spécification générée par un crochet `openapi()` personnalisé, pas par des
  dépendances de route. Le refus `422 VAL_SCHEMA_INVALIDE` y figure comme réponse déclarée de toute
  route avec corps (FR-029).

## R-06 — L'idempotence vit dans Valkey, bornée au tenant

- **Décision** : clé `idem:{tenant_id}:{X-Nelo-Requete}`, valeur JSON `{empreinte, statut, corps,
  en_cours}`, TTL 24 h ([03-api.md § 1.3](../../docs/03-api.md), [ADR 007](../../docs/adr/007-valkey-pour-l-ephemere.md)).
  Séquence : `SET NX` d'un marqueur `en_cours` avec la même TTL — s'il existe déjà **en cours**,
  `409 REQUETE_EN_COURS` ; s'il existe **terminé** avec la même empreinte, la réponse mémorisée est
  rendue telle quelle, statut et corps ; avec une autre empreinte, `409 REQUETE_REJOUEE_DIFFEREMMENT`.
  L'empreinte est un SHA-256 de `méthode + chemin + corps brut`. Un `X-Nelo-Requete` absent →
  `400 REQUETE_CLE_MANQUANTE` ; présent mais pas un UUID v7 → `400 REQUETE_CLE_INVALIDE`.
- **Le relais d'unicité en base** ([02-domaine.md R11](../../docs/02-domaine.md)) : `PUT /parametres/{cle}`
  est un `UPSERT` sur une clé naturelle `(tenant_id, cle, portee, portee_id)` — l'écriture est
  **idempotente par nature**, une réexécution après perte de Valkey pose la même valeur. Le module
  doré ne porte donc pas de colonne `cle_idempotence`. **Le patron le dit explicitement** dans son
  code : une table de *faits* (une présence, une note, un encaissement) porte cette colonne et sa
  contrainte d'unicité `(tenant_id, cle_idempotence)` ; les tranches qui en créent une la copient de
  là, pas du module doré.
- **Ce qui est perdu si Valkey est vidé** : un rejeu réexécute et rend la même réponse (même valeur,
  un **second** événement outbox). C'est le prix nommé par l'ADR 007 — « dégrade en réexécution,
  jamais en corruption » — et le consommateur d'événements sait qu'un événement peut arriver deux
  fois (FR-026).

## R-07 — L'isolation : politique unique, variable par transaction, deux fonctions nommées

- **Décision** : deux rôles PostgreSQL, `nelo_proprietaire` (propriétaire des schémas, exécute les
  migrations) et `nelo_app` (le seul rôle de l'application, `NOSUPERUSER NOBYPASSRLS`). Chaque table
  porte `ENABLE ROW LEVEL SECURITY` **et** `FORCE ROW LEVEL SECURITY`, avec une politique
  `tenant_id = current_setting('app.current_tenant', true)::uuid` pour `SELECT`, `INSERT`, `UPDATE`,
  `DELETE`. Le second argument `true` fait que la variable absente vaut `NULL` : la comparaison est
  fausse, **aucune ligne n'est visible et aucune écriture ne passe** — jamais « toutes » (FR-017).
  La variable est posée par `SELECT set_config('app.current_tenant', :tenant, true)` — `SET LOCAL`
  n'accepte pas de paramètre lié — dans **l'unique point d'entrée** `transaction(tenant_id)` de
  `modules/shared/bd.py`, qui ouvre la transaction, pose la variable, la rend, et la referme ; aucun
  autre code n'ouvre de transaction ([ADR 005](../../docs/adr/005-isolation-des-tenants-par-rls-et-double-barriere.md)).
- **La table `tenant`** a pour politique `id = current_setting(...)::uuid`. **La table
  `parametre_catalogue`**, référentiel commun à tous les tenants, a pour politique de lecture
  `current_setting('app.current_tenant', true) IS NOT NULL` — visible dans toute transaction
  tenantée, invisible sans variable — et **aucune politique d'écriture** pour `nelo_app` : elle est
  alimentée par les migrations, sous le rôle propriétaire.
- **Deux besoins ne peuvent pas passer par une transaction tenantée** : résoudre le tenant depuis un
  identifiant d'établissement avant d'avoir un tenant (R-16), et donner au travailleur la liste des
  tenants dont il doit consommer les événements (R-09). Ils sont servis par **deux fonctions
  `SECURITY DEFINER`** appartenant à `nelo_proprietaire`, qui ne renvoient que des identifiants :
  `tenants.tenant_de_etablissement(uuid) → uuid` et `tenants.tenants_pour_travailleur() → setof uuid`.
  **Un test énumère les fonctions `SECURITY DEFINER` du schéma et échoue s'il en trouve une autre** :
  le trou est nommé, borné, et ne s'élargit pas sans qu'un test le dise.
- **Le test d'isolation** (FR-018) : deux tenants, un pool à **une seule connexion** pour forcer sa
  réutilisation, A lit, B lit sur la même connexion, aucune ligne ne traverse ; une transaction sans
  variable voit zéro ligne sur chaque table du schéma ; une ressource de B demandée par A répond
  `404 TEN_RESSOURCE_INTROUVABLE`.
- **Écartées** : un rôle `BYPASSRLS` pour le travailleur (contourne aussi `FORCE`) ; une variable
  « contexte travailleur » lisible par toute requête (un gestionnaire pourrait la poser par erreur).

## R-08 — Alembic : un dossier par module, réversible, comparé

- **Décision** : `migrations/tenants/` avec son `alembic.ini`, son `env.py` et ses `versions/`. La
  table de version est `tenants.alembic_version` — **dans le schéma du module**, pour qu'aucun
  module ne partage la sienne. La première migration crée le schéma `tenants`, ses tables, ses
  politiques, ses deux fonctions, et **insère le catalogue** (R-20). La porte P-01 recrée la base,
  applique `upgrade head`, puis `downgrade base`, puis `upgrade head` à nouveau — la réversibilité
  est exercée, pas déclarée (FR-045). Elle lit ensuite `pg_class` pour vérifier `relrowsecurity` **et**
  `relforcerowsecurity` sur chaque table, `pg_policies` pour la présence d'au moins une politique par
  table, et `pg_constraint` pour qu'aucune clé étrangère ne sorte du schéma de son module.
- **La comparaison au schéma attendu** (FR-044) : les tables sont déclarées une fois en SQLAlchemy
  Core (`modules/socle/tenants/tables.py`) ; la porte P-12 exécute
  `alembic.autogenerate.compare_metadata()` entre cette déclaration et la base migrée et échoue au
  premier écart — colonne absente, type divergent, contrainte manquante.

## R-09 — La table d'événements et le travailleur

- **Décision** : `tenants.evenement_outbox`, **dans le schéma du module** — la constitution (XI)
  interdit qu'une transaction traverse deux modules, donc l'événement s'écrit dans le schéma de la
  transaction qui change l'état ; chaque module aura la sienne. Le travailleur est une tâche
  `asyncio` démarrée dans le `lifespan` de FastAPI, **dans le processus du serveur** (FR-026). Sa
  boucle : lister les tenants (fonction R-07), et pour chacun, dans une transaction tenantée,
  prendre jusqu'à *n* événements `en_attente` par `SELECT … ORDER BY ecrit_le, id FOR UPDATE SKIP
  LOCKED`, les passer à `pris`, appeler le consommateur, marquer `traite` ou `en_echec` (avec
  `tentatives + 1` et `derniere_erreur`) ; un `en_echec` repasse `en_attente` à la boucle suivante.
  L'ordre par tenant est celui de l'écriture (FR-027) ; la livraison est **au moins une fois**.
- **Ce que T0a ne fait pas** : pas de recul exponentiel, pas de plafond de tentatives, pas
  d'ordonnancement par Valkey ([ADR 007](../../docs/adr/007-valkey-pour-l-ephemere.md) l'autorise,
  rien ne l'exige avec un seul processus et un seul travailleur). Un intervalle de scrutation
  configurable suffit ; la première tranche qui a un vrai consommateur — T4a — reprend ce point.
- **Le consommateur de T0a** est un journal : il écrit l'événement dans le journal applicatif.
  C'est assez pour prouver « consommé et marqué traité » et « en échec puis repris » (le test
  injecte un consommateur qui lève).

## R-10 — Le client typé : `openapi-typescript`, épinglé et hors ligne

- **Décision** : un `package.json` et un `pnpm-lock.yaml` **à la racine**, avec `openapi-typescript`
  7.13.0 en dépendance de développement ; `pnpm-workspace.yaml` liste `web` que T0b créera. Le
  serveur écrit sa spécification dans `contrat/openapi.json` (une commande `uv run python -m
  api.contrat`) ; `pnpm exec openapi-typescript contrat/openapi.json -o contrat/client.d.ts` en dérive
  les types. **Les deux fichiers sont commités** ; la porte P-03 régénère les deux et exige un
  `git diff --exit-code` vide.
- **Motif** : FR-002 exige qu'aucun service distant ne soit requis **pour vérifier** ; un `pnpm dlx`
  téléchargerait à chaque vérification. Un lockfile npm à la racine donne aussi à P-02 son
  « second fichier de verrouillage » **dès T0a**, sans attendre `web/` — l'edge case de la spec
  reste vrai : chaque espace de travail présent a le sien.
- **Pourquoi `contrat/` et pas `web/`** : `web/` naît avec T0b et son initialisation Nuxt ; y
  déposer deux fichiers avant serait un conflit annoncé. La roadmap nomme le contrat « le point de
  jonction entre les deux tranches » ([04-roadmap.md § T0](../../docs/04-roadmap.md)) : il a sa
  place. Diff proposé sur [01-stack.md § 2.3](../../docs/01-stack.md) en fin de fichier.
- **Écartées** : `@hey-api/openapi-ts` (génère aussi un client d'appel ; T0b choisira son client
  de requêtes, T0a ne doit livrer que les types) ; un générateur Python vers TypeScript (aucun
  n'est mature).

## R-11 — La porte P-12 : couverture par fonction, pas par ligne

- **Décision** : toute fonction d'accès aux données vit dans un fichier `acces.py` de son paquet.
  La suite `pytest` tourne sous `coverage` ; un script de porte lit le rapport JSON, parcourt l'AST
  de chaque `acces.py`, et **échoue en nommant** toute fonction dont aucune ligne du corps n'a été
  exécutée. Il annonce le nombre de fonctions inspectées et échoue à zéro (FR-043).
  « Aucune requête par concaténation » est tenu par la règle `ruff` **S608** (SQL construit par
  formatage) et par un test qui refuse tout `text()` dont l'argument n'est pas une constante.
- **Motif** : un seuil de couverture se baisse ; une liste nominative de fonctions non exercées ne
  se négocie pas (FR-044, [01-stack.md § 7.5](../../docs/01-stack.md)).
- **Écartées** : un décorateur d'enregistrement à l'exécution (une fonction oubliée du décorateur
  échappe à la porte) ; un seuil `--cov-fail-under` (précisément ce que la porte refuse d'être).

## R-12 — La porte P-07 : deux vérificateurs, une liste blanche

- **Décision** : `pip-licenses` sur l'environnement `uv` et `pnpm licenses list --json` sur le
  lockfile npm, comparés à la liste autorisée de [01-stack.md § 9](../../docs/01-stack.md) — MIT,
  Apache-2.0, BSD-2/3, ISC, Zlib, Unicode, MPL-2.0, OFL-1.1. Toute licence hors liste, ou
  **inconnue**, échoue en nommant la dépendance. Le script annonce le nombre de paquets inspectés.

## R-13 — Les tests négatifs : une copie de travail `git`, jamais le dépôt

- **Décision** : `scripts/tests-negatifs.sh` crée un `git worktree` temporaire par porte, y applique
  une mutation (un script par porte, sous `scripts/portes/negatifs/`), y lance **la porte seule**,
  exige un code de sortie non nul **et** la présence du nom de la porte dans la sortie, puis retire
  la copie. En fin de suite, `git status --porcelain` du dépôt d'origine est comparé à sa valeur
  d'entrée : toute différence est un échec (edge case « test négatif qui laisse une trace »).
- **Les sept mutations** — celles de la spec et de [01-stack.md § 7](../../docs/01-stack.md) :
  P-01 retirer une politique ; P-02 déclarer une dépendance en intervalle ; P-03 modifier
  `contrat/client.d.ts` à la main ; P-04 faire importer un paquet de `metier/` par
  `socle/tenants` ; P-07 ajouter une dépendance GPL au lockfile de la copie ; P-11 un import
  différé de `protection` au fond d'une fonction ; P-12 renommer une colonne dans une migration
  sans toucher la requête.
- **Écartée** : muter le dépôt puis restaurer (un test interrompu laisse une trace).

## R-14 — Les trois abstractions vivent chez leur futur propriétaire

- **Décision** : `modules/socle/communication/passerelle_sms.py`,
  `modules/metier/finance/agregateur_paiement.py`, `modules/socle/assistance/service_inference.py` —
  chacune un `Protocol`, sa simulation, son énumération de modes, et une exception commune
  `DependanceIndisponible` dans `modules/shared/erreurs.py`. Les paquets `communication` et `finance`
  sont créés avec ce seul fichier et leur `pyproject.toml` ; ils figurent déjà dans la cible de
  [01-stack.md § 2.3](../../docs/01-stack.md).
- **Motif** : quand T4a et T8b remplacent la simulation, c'est dans le paquet où l'interface est
  déjà ; « ce sera un remplacement, pas une découverte » (US6). Un paquet `integrations` transverse
  aurait été un nom hors de la cible.
- **La signature est celle d'un fournisseur réel** (FR-038) : `envoyer(...)` rend immédiatement une
  référence ; l'accusé arrive **plus tard**, par `attendre_accuse(reference, delai_max)` qui rend
  `None` à l'échéance — jamais de blocage au-delà d'un délai borné. Les modes viennent de la
  configuration (`pydantic-settings`) : `SUCCES`, `ACCUSE_EN_RETARD`, `ACCUSE_EN_DOUBLE`,
  `JAMAIS_RECU`, `INDISPONIBLE`, plus un délai. `INDISPONIBLE` lève `DependanceIndisponible`, que
  l'API traduit en `503` (R-19).
- **Le test du `503`** : aucune route de T0a ne dépend de ces abstractions. Le gestionnaire
  d'exception est testé sur une route **déclarée par le test lui-même**, sur une application de test.
  Le contrat vérifié est celui du gestionnaire, pas d'une route fictive livrée.

## R-15 — L'assistance : un paquet, six capacités, un réglage

- **Décision** : `modules/socle/assistance/` expose `Capacite` (C1 à C6, avec leurs libellés-clés
  de [02-domaine.md § 13.2](../../docs/02-domaine.md)), `EtatCapacite` (`NON_LIVREE`, `SUSPENDUE`,
  `DISPONIBLE`), `etat_des_capacites(tenant_id, etablissement_id)` et `appeler(capacite, …)`. En
  T0a, `appeler` lève `CapaciteNonLivree` pour les six — refus explicite, testé (FR-032). La
  suspension se lit par la **valeur effective** de `assistance.suspendue` à la portée de
  l'établissement, obtenue d'un **lecteur de paramètres injecté** à la construction du paquet — pas
  d'import de `tenants` depuis `assistance` (FR-007). Suspendue, `etat_des_capacites` rend
  `SUSPENDUE` pour les six et `appeler` lève `AssistanceSuspendue` avant tout.
- **Le reparcours** (FR-035) : la dernière étape de `scripts/verifier.sh` pose `assistance.suspendue
  = true` au tenant de test par `PUT /parametres/assistance.suspendue` et relance la suite du module
  doré ; le résultat doit être identique.

## R-16 — Le tenant provisoire et le point d'insertion de capacité

- **Décision** : le middleware d'établissement lit `X-Nelo-Etablissement`. Absent →
  `400 TEN_ETABLISSEMENT_REQUIS` ; présent mais pas un UUID → `400 TEN_ETABLISSEMENT_REQUIS`
  (même règle que `X-Nelo-Annee` malformé dans la table de [03-api.md § 1.2](../../docs/03-api.md)) ;
  UUID inconnu → `404 TEN_RESSOURCE_INTROUVABLE` (aucune affectation de compte n'existe avant T1a,
  donc le `403 TEN_ETABLISSEMENT_NON_AUTORISE` n'a pas encore d'objet). La résolution passe par
  `tenants.tenant_de_etablissement` (R-07). Le module s'appelle `api/tenant_provisoire.py`, et sa
  docstring nomme T1a comme sa fin de vie (FR-015).
- **Le point d'insertion** : `api/capacites.py` expose `exiger_capacite(code)` — en T0a, elle
  journalise le code exigé et laisse passer ; la route `PUT` l'appelle avec
  `tenant.parametre.definir`. Un test vérifie que **la route l'appelle** : le point de passage
  existe, il n'est pas contournable, T1b le remplit. La sonde `/sante` est la seule route qui ne
  traverse ni l'un ni l'autre.

## R-17 — Les portées que le module doré accepte

- **Décision** : la résolution `tenant → établissement → site → cycle` est écrite pour les quatre
  portées dans une seule fonction (FR-011), testée sur `TENANT` et `ETABLISSEMENT`, les seules dont
  l'entité existe en T0a. `GET /parametres` résout **à la portée de l'établissement de l'en-tête**.
  `PUT` accepte `TENANT` et `ETABLISSEMENT` ; `SITE` et `CYCLE` répondent `422 TEN_PORTEE_INVALIDE`
  avec `details.portees_disponibles = ["TENANT", "ETABLISSEMENT"]` tant que leurs tables n'existent
  pas ; une portée plus basse que `portee_la_plus_basse` de la clé, ou un `portee_id` hors du tenant,
  répondent le même code avec `details.portee_la_plus_basse` ou `details.motif`.
- **Motif** : offrir un paramètre de requête `site_id` sans table `site` serait une généricité
  prématurée (FR-010) ; la tranche qui crée les sites étend la route et le contrat ensemble.

## R-18 — L'ordre de `scripts/verifier.sh`

- **Décision** : `ruff check` et `ruff format --check` d'abord (ce n'est pas une porte numérotée,
  c'est « tout ce qui doit passer »), puis **P-02, P-07, P-04, P-11, P-01, P-12, P-03**, puis le
  reparcours sous suspension (R-15). Chaque étape est un script `scripts/portes/p-XX.sh` qui écrit
  `PORTE P-XX : <ce qu'elle a inspecté>` en succès et `PORTE P-XX ÉCHOUÉE : <motif>` en échec ;
  `verifier.sh` s'arrête au premier code non nul (`set -euo pipefail`).
- **Motif** : du moins coûteux au plus coûteux — les lectures de fichiers avant la base recréée,
  la base avant les tests, les tests avant la régénération du client qui exige le serveur. La
  planche de diagrammes avait proposé cet ordre en le disant ouvert ; le voici fixé. Budget :
  moins de trois minutes (SC-010) ; la base PostgreSQL tourne déjà dans la composition, seule la
  **base logique** est recréée (`DROP DATABASE … ; CREATE DATABASE …`), pas le conteneur.

## R-19 — Le code du `503`

- **Décision** : `API_DEPENDANCE_INDISPONIBLE`, sous le préfixe `API_` que
  [03-api.md § 1.7](../../docs/03-api.md) réserve à « ce qui n'appartient à aucun module » ;
  `details.dependance` nomme l'abstraction (`PASSERELLE_SMS`, `AGREGATEUR_PAIEMENT`,
  `SERVICE_INFERENCE`). Diff proposé sur § 1.8 en fin de fichier. Les tranches propriétaires
  pourront préférer un code de domaine ; le socle a besoin d'un code générique pour son
  gestionnaire.

## R-20 — Q28 : `assistance.suspendue`, appliqué à titre provisoire

- **Décision** : la ligne `| assistance.suspendue | ÉTABLISSEMENT | false |` **a été ajoutée** à
  [02-domaine.md § 17](../../docs/02-domaine.md) au début de ce plan, telle que la spec la
  proposait dans ses hypothèses.
- **Motif** : la constitution exige que le plan **dérive** du catalogue ; tant que la ligne n'y
  était pas, il n'avait rien à dériver, et la question bloquait tout le reste pour une décision
  qui ne change qu'une ligne du modèle et une ligne du seed. La spec a écrit que « la spécification
  ne dépend que de l'existence d'un tel réglage » ; c'est vrai du plan aussi.
- **Confirmée le 2026-09-14** : clé, portée et défaut restent ceux de la spec. Q28 est close dans
  `progress.md`. Si elle devait bouger un jour, le changement tient en trois endroits — cette ligne
  de § 17, la ligne du seed dans `data-model.md`, l'exemple de `quickstart.md`.

## R-21 — La sonde `/sante`

- **Décision** : `GET /api/v1/sante` répond `200 {"etat": "OK"}` sans toucher ni la base ni
  Valkey ; elle ne traverse ni le middleware d'établissement ni celui d'idempotence (`GET`).
- **Motif** : « elle ne porte aucune donnée » (spec, hypothèses) ; la vérification s'en sert pour
  savoir que le serveur est levé avant de régénérer le contrat (P-03). Une sonde qui interroge la
  base dit autre chose — la tranche de supervision décidera.

## R-22 — La branche

- **Constat** : `setup-plan.sh` annonce la branche `001-socle-serveur`, mais le dépôt était sur
  `main`, `specs/` n'était pas suivi par git, et aucune branche de ce nom n'existait. La spec a été
  écrite sur `main`.
- **Décision de l'utilisateur, 2026-09-14** : une branche par tranche. `001-socle-serveur` est
  créée depuis `main` ; la constitution, les amendements du corpus, la spec et le plan y sont
  commités. La fusion dans `main` clôt la tranche, après `scripts/verifier.sh`.

## Diffs sur les documents projet

**Arbitrés et appliqués le 2026-09-14**, tels que proposés ci-dessous, avec R-20 et le
`TEN_VALEUR_INVALIDE` de [data-model.md](data-model.md). Le texte des diffs est conservé pour la
traçabilité ; les documents projet font foi.

**[docs/01-stack.md § 2.3](../../docs/01-stack.md)** — le point de jonction des deux tranches :

```diff
 ├── CLAUDE.md · compose.yml · docs/ · .specify/ · specs/ · scripts/
+├── pyproject.toml · uv.lock · package.json · pnpm-lock.yaml   # espaces de travail, à la racine
+├── contrat/                  # openapi.json écrit par le serveur, client.d.ts dérivé — commités, régénérés par P-03
 ├── web/                      # Nuxt 4 — app/ : components/ composables/ core/ pages/ assets/
```

**[docs/01-stack.md § 3](../../docs/01-stack.md)** — la commande de lancement :

```diff
-cd api && uv run fastapi dev  # l'API sur :8000, OpenAPI sur /openapi.json
+uv run fastapi dev api/main.py  # depuis la racine — l'API sur :8000, OpenAPI sur /openapi.json
```

**[docs/01-stack.md § 2.5](../../docs/01-stack.md)**, point 2 — où vit l'outbox :

```diff
-2. **Toute transition d'état métier écrit un événement outbox dans la même transaction SQL.**
+2. **Toute transition d'état métier écrit un événement outbox dans la même transaction SQL** —
+   dans la table `evenement_outbox` **du schéma du module**, puisqu'aucune transaction ne traverse
+   deux modules ; le travailleur consomme chaque table, par tenant, dans l'ordre d'écriture.
```

**[docs/03-api.md § 1.8](../../docs/03-api.md)** — le code du `503` :

```diff
-| `503` | Dépendance externe indisponible (agrégateur de paiement, passerelle SMS, service d'inférence) |
+| `503` | Dépendance externe indisponible — `API_DEPENDANCE_INDISPONIBLE`, `details.dependance` nomme l'abstraction (agrégateur de paiement, passerelle SMS, service d'inférence) |
```

**[docs/02-domaine.md § 1.2](../../docs/02-domaine.md)** — la table d'événements du schéma
`tenants` (chaque module aura la sienne ; la première apparaît ici) :

```diff
 | **`parametre_valeur`** | `cle`, `portee` (`TENANT` \| `ETABLISSEMENT` \| `SITE` \| `CYCLE`), `portee_id`, `valeur` |
+| **`evenement_outbox`** | `type`, `charge`, `ecrit_le`, `etat` (`en_attente` \| `pris` \| `traite` \| `en_echec`), `tentatives` — l'outbox du module, consommée par tenant dans l'ordre d'écriture |
```
