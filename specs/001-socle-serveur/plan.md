# Plan d'implémentation : Le socle serveur (T0a)

**Branche** : `001-socle-serveur` — créée depuis `main` le 2026-09-14 ; la spec et le plan y sont
commités (voir [research.md R-22](research.md)) | **Date** : 2026-09-10 | **Spec** : [spec.md](spec.md)

**Entrée** : la spécification de `specs/001-socle-serveur/spec.md`, la planche
[design/diagrammes.md](design/diagrammes.md), et le corpus qui fait foi —
[01-stack.md](../../docs/01-stack.md), [02-domaine.md](../../docs/02-domaine.md),
[03-api.md](../../docs/03-api.md), la [constitution](../../.specify/memory/constitution.md) v1.0.0.

## Résumé

Poser le socle serveur avant toute règle métier, et prouver qu'il tient par sept portes mécaniques
enchaînées en une commande. Concrètement : un espace de travail `uv` à la racine dont chaque paquet
déclare ses dépendances ; le module doré `modules/socle/tenants` — catalogue de paramètres sur
`GET /parametres` et `PUT /parametres/{cle}` — écrit à la main de bout en bout ; l'isolation par
Row Level Security forcée et variable de tenant posée par transaction ; l'idempotence en middleware
avec mémorisation dans Valkey ; une table d'événements par schéma de module et un travailleur dans
le processus ; le contrat OpenAPI généré et le client TypeScript qui en dérive ; trois abstractions
externes simulées qui savent échouer ; l'assistance comme paquet du socle, suspendue par une clé du
catalogue ; et `scripts/verifier.sh` avec le test négatif de chaque porte.

## Contexte technique

**Langage / version** : Python 3.14 (dernière stable, roues `cp314` vérifiées — [R-01](research.md)).

**Dépendances principales** : FastAPI 0.141.1, Pydantic 2.13.5, SQLAlchemy Core 2.0.52 + asyncpg
0.31.0, Alembic 1.19.2, client `valkey` 6.1.1 ; `uv` 0.10.12, `ruff` 0.16.6, `pytest` 9.1.1 ;
`import-linter` 2.15, `coverage` 7.16.0, `pip-licenses` 5.5.5 ; `openapi-typescript` 7.13.0 via
`pnpm` — toutes épinglées exactement, toutes sous licence autorisée ([R-02](research.md)).

**Stockage** : PostgreSQL 18 (`postgres:18.6-alpine`), un schéma `tenants` ; Valkey 9.1.2 pour la
seule mémorisation des réponses idempotentes ; Garage v2.4.1 présent dans la composition, **non
utilisé** par cette tranche (aucun fichier avant les documents).

**Tests** : `pytest` + `pytest-asyncio`, client `httpx` ASGI ; tests d'intégration contre la base
migrée par Alembic sur base vierge, jamais contre un schéma résiduel.

**Plateforme cible** : le poste du développeur, macOS ou Linux, Docker Compose ; le VPS ensuite
sans changement de code ([ADR 008](../../docs/adr/008-local-d-abord-vps-ensuite.md)).

**Type de projet** : service web — monolithe modulaire, un processus, un travailleur en tâche
`asyncio`. Aucune interface en T0a.

**Objectifs de performance** : aucun objectif de débit dans cette tranche ; **la commande de
vérification complète sous trois minutes** (SC-010), le module doré répondant en moins de cinq
minutes après le clonage (SC-001).

**Contraintes** : CP-01 à CP-06 de la spec ; aucun service distant ni clé d'API pour développer
**ni pour vérifier** ; trois services dans la composition ; français partout, accents compris.

**Échelle** : deux tenants de test, dix-sept clés de catalogue, trois routes, sept portes.

## Contrôle de constitution

*Porte : doit passer avant la phase 0 ; revérifiée après la phase 1.* Chaque principe cite comment
la tranche le respecte, ou pourquoi il ne s'applique pas encore — un écart tacite est un refus.

| Principe | Verdict | Comment la tranche le tient |
|---|---|---|
| **I** Le serveur est la seule autorité | Conforme | Aucun client en T0a. La double barrière existe déjà comme **point de passage** : `exiger_capacite("tenant.parametre.definir")` est appelée par la route d'écriture (un test le vérifie), et le périmètre est tenu par la RLS + le `404` sur une ressource hors tenant ([R-16](research.md)) |
| **II** Composition par capacités | Conforme | Aucun rôle, aucune énumération. L'état d'assistance est exposé par `etat_des_capacites` pour que l'interface puisse **ne pas afficher** — jamais griser ([R-15](research.md)) |
| **III** Cloisonnement = frontière d'import | Conforme | `modules/metier/protection` présent, vide, tenu par trois verrous : déclaration (`pyproject.toml` par paquet), graphe (`import-linter` + AST, imports différés et chaînes), surface (`__all__` de l'`__init__.py`). « Un compilateur refusait, un test signale » est écrit dans la porte P-11 ([R-03, R-04](research.md)) |
| **IV** Donnée de mineur | Sans objet, vérifié | Aucune table de cette tranche ne porte une donnée d'élève. `tenant` et `etablissement` sont des personnes morales |
| **V** Le pays vit dans le pack | Conforme | `pays_code`, `fuseau_horaire`, `country_pack_version` sont des **données** ; aucune littérale de pays dans `domaine/`, `socle/`, `metier/`. Le contrat *layers* interdit `socle → segments` et `metier → segments`. Le test d'agnosticité n'a pas encore de matière (T6a) |
| **VI** Référentiel versionné | Sans objet | Aucune évaluation |
| **VII** Toute entité pédagogique porte son année | Sans objet, vérifié | Aucune entité pédagogique ; `parametre_valeur` est une configuration, pas une donnée d'année |
| **VIII** Montants entiers, notes NUMERIC, intervalles | Conforme | Les deux taux du catalogue voyagent en **chaîne décimale** ; l'abstraction de paiement prend un **entier d'unité mineure** et une devise ([contracts/interfaces-python.md](contracts/interfaces-python.md)) |
| **IX** Aucune saisie ne se perd | Conforme | `X-Nelo-Requete` obligatoire en middleware, réponse mémorisée 24 h bornée au tenant, rejeu testé, identifiant UUID v7. Les identifiants de `tenant` et `etablissement` sont posés par le serveur **dans les seeds et les tests** seulement : aucune route de création n'existe en T0a ([R-06](research.md)) |
| **X** Outbox dans la même transaction | Conforme | `evenement_outbox` dans le schéma du module, `INSERT` dans la transaction de l'`UPSERT`, travailleur dans le processus, aucun bus ([R-09](research.md)) |
| **XI** Jamais de transaction inter-modules | Conforme | Un schéma, aucune FK sortante, `migrations/tenants/` avec sa table de version dans le schéma ; P-01 et P-04 mécaniques ([R-08](research.md)) |
| **XII** Double barrière d'isolation | Conforme, avec deux exceptions nommées | `ENABLE` + `FORCE` sur chaque table, rôle `nelo_app` distinct de `nelo_proprietaire`, `set_config(..., true)` dans l'unique point d'entrée, `404` jamais `403`. **Deux fonctions `SECURITY DEFINER`** ne renvoient que des identifiants, sont listées et testées ([R-07](research.md), suivi de complexité ci-dessous) |
| **XIII** Le SMS est un canal de premier rang | Conforme à sa mesure | Seule l'abstraction existe ; sa signature est celle d'un fournisseur réel avec accusé différé. Variantes, budget, fenêtres : T4a |
| **XIV** L'IA propose, un humain décide | Conforme | Aucune capacité livrée ; appel = refus explicite testé ; `assistance.suspendue` posé par la route d'écriture, et la vérification **reparcourt** le module doré sous suspension ([R-15](research.md)) |
| **XV** Le poids est une contrainte | Conforme à sa mesure | Aucun écran. Le catalogue ne porte que des `description_cle`, jamais un texte affiché ; P-06 et P-10 arrivent avec T0b |

**Périmètre** : le plan n'ouvre pas `docs/06-apres-mvp.md` ; aucune généralisation n'est justifiée
par une extension future. **Méthode** : le plan dérive de `02-domaine.md` et `03-api.md` ; ce qui
manquait est proposé comme diff explicite, listé en fin de ce fichier, et un seul est appliqué
(Q28, [R-20](research.md)). **Terminé** : rien ne l'est tant que `scripts/verifier.sh` ne passe pas
en une commande.

**Verdict de la porte** : passe. Aucune violation ; trois choix de complexité justifiés ci-dessous.

## Structure du projet

### Documentation (cette tranche)

```text
specs/001-socle-serveur/
├── spec.md                       # la spécification
├── design/
│   ├── prompt-diagrammes.md
│   └── diagrammes.md             # revue visuelle, forme B
├── plan.md                       # ce fichier
├── research.md                   # phase 0 — R-01 à R-22, diffs proposés
├── data-model.md                 # phase 1 — schéma tenants, Valkey, entités hors base
├── contracts/
│   ├── openapi-attendu.yaml      # ce que la génération doit produire pour les trois routes
│   └── interfaces-python.md      # ce que chaque paquet expose, et rien d'autre
├── quickstart.md                 # phase 1 — démarrer et prouver, user story par user story
└── tasks.md                      # phase 2 — /speckit-tasks, pas ce plan
```

### Code source (racine du dépôt)

```text
nelo_v0/
├── pyproject.toml                # projet racine installable : packages = ["modules", "api"] ; [tool.uv.workspace] ; contrats import-linter ; ruff ; pytest
├── uv.lock                       # premier fichier de verrouillage
├── .python-version               # 3.14
├── package.json · pnpm-lock.yaml · pnpm-workspace.yaml   # openapi-typescript épinglé ; second verrouillage ; `web` viendra avec T0b
├── compose.yml                   # postgres, valkey, garage — trois services
├── contrat/
│   ├── openapi.json              # écrit par `python -m api.contrat`
│   └── client.d.ts               # dérivé par openapi-typescript — les deux commités, régénérés par P-03
├── api/
│   ├── pyproject.toml            # membre déclaratif : dépend de nelo-socle-tenants, nelo-socle-assistance, nelo-shared…
│   ├── __init__.py · main.py · configuration.py
│   ├── idempotence.py            # middleware ASGI — X-Nelo-Requete, Valkey
│   ├── tenant_provisoire.py      # middleware ASGI — X-Nelo-Etablissement, PROVISOIRE jusqu'à T1a
│   ├── capacites.py              # exiger_capacite(code) — point d'insertion, vide jusqu'à T1b
│   ├── erreurs.py                # enveloppe, gestionnaires 422 / métier / 503 / 500
│   ├── travailleur.py            # la boucle de consommation de l'outbox
│   ├── contrat.py                # écrit contrat/openapi.json avec les en-têtes de middleware
│   └── routes/
│       ├── sante.py
│       └── parametres.py
├── modules/                      # espace de noms PEP 420 — pas d'__init__.py ici ni dans les familles
│   ├── domaine/                  # pyproject.toml + __init__.py vide — aucune E/S, aucun pays ; existe pour que la hiérarchie ait sa base
│   ├── shared/
│   │   ├── pyproject.toml · __init__.py
│   │   ├── bd.py                 # transaction(tenant_id) — l'unique point d'entrée
│   │   ├── erreurs.py            # EnveloppeErreur, ErreurMetier, DependanceIndisponible
│   │   ├── simulation.py         # ModeSimulation
│   │   └── evenement.py          # Evenement(type, charge)
│   ├── socle/
│   │   ├── tenants/              # LE MODULE DORÉ
│   │   │   ├── pyproject.toml · __init__.py      # l'interface de service, et rien d'autre
│   │   │   ├── tables.py         # déclaration Core des cinq tables — comparée au schéma migré par P-12
│   │   │   ├── acces.py          # toutes les fonctions d'accès aux données — toutes exercées ou P-12 échoue
│   │   │   ├── service.py        # catalogue, portées, résolution, événement
│   │   │   ├── schemas.py        # les modèles Pydantic du contrat
│   │   │   └── catalogue_seed.py # les dix-sept lignes de § 17, lues par la migration
│   │   ├── assistance/
│   │   │   ├── pyproject.toml · __init__.py
│   │   │   ├── service.py        # Assistance, Capacite, EtatCapacite
│   │   │   └── service_inference.py   # Protocol + simulation
│   │   └── communication/
│   │       ├── pyproject.toml · __init__.py
│   │       └── passerelle_sms.py      # Protocol + simulation
│   ├── metier/
│   │   ├── protection/
│   │   │   ├── pyproject.toml · __init__.py   # __all__ = ["ServiceProtection"] — CLOISONNÉ
│   │   └── finance/
│   │       ├── pyproject.toml · __init__.py
│   │       └── agregateur_paiement.py  # Protocol + simulation
│   └── segments/                 # vide, présent pour que la couche existe dans le contrat layers
├── migrations/
│   └── tenants/
│       ├── alembic.ini · env.py
│       └── versions/0001_socle_tenants.py   # schéma, cinq tables, politiques, deux fonctions, seed du catalogue — réversible
├── scripts/
│   ├── verifier.sh               # ruff → P-02 → P-07 → P-04 → P-11 → P-01 → P-12 → P-03 → reparcours sous suspension
│   ├── tests-negatifs.sh         # sept worktrees, sept mutations, sept échecs attendus, dépôt intact
│   ├── bd-vierge.sh              # recrée la base logique et les rôles, applique les migrations, jeu d'essai optionnel
│   └── portes/
│       ├── p-01.sh … p-12.sh     # une porte, un script, une sortie « PORTE P-XX : … »
│       ├── p12_acces_exerces.py  # coverage JSON + AST des acces.py
│       ├── p07_licences.py       # liste blanche de 01-stack § 9
│       └── negatifs/             # une mutation par porte
└── tests/
    ├── conftest.py               # base migrée sur base vierge, deux tenants, client httpx, pool à une connexion
    ├── module_dore/              # US1 — lecture, écriture, refus de schéma, refus métier, sonde
    ├── isolation/                # US2
    ├── idempotence/ · outbox/    # US3
    ├── frontieres/               # US4 — graphe, chaînes, surface, déclarations, compte de modules
    ├── simulations/              # US6 — cinq modes × trois abstractions, gestionnaire 503
    ├── assistance/               # US7
    └── portes/                   # les fonctions SECURITY DEFINER énumérées, le contrat attendu vs généré
```

**Décision de structure** : un seul projet Python installable à la racine, des paquets d'espace de
noms aux chemins littéraux du corpus, et un `pyproject.toml` **déclaratif** par paquet — c'est ce
qui donne au premier verrou de P-11 quelque chose à inspecter ([R-03](research.md)). Les trois
abstractions externes vivent chez leur futur propriétaire — `communication`, `finance`,
`assistance` — parce que leur remplacement en T4a et T8b doit être un remplacement, pas une
découverte ([R-14](research.md)). Le contrat généré vit dans `contrat/`, point de jonction nommé par
la roadmap entre T0a et T0b ([R-10](research.md)).

## Suivi de complexité

Aucune violation de la constitution. Trois choix dépassent le strict minimum et se justifient :

| Choix | Pourquoi il est nécessaire | Alternative plus simple, et pourquoi elle est écartée |
|---|---|---|
| **Deux fonctions `SECURITY DEFINER`** (`tenant_de_etablissement`, `tenants_pour_travailleur`) | Deux besoins ne peuvent pas passer par une transaction tenantée : résoudre le tenant depuis l'en-tête avant d'avoir un tenant ; donner au travailleur la liste des tenants. Elles ne renvoient que des identifiants et un test échoue si une troisième apparaît | Un rôle `BYPASSRLS` : contourne aussi `FORCE`, exactement le piège que P-01 ferme. Une variable « contexte travailleur » : un gestionnaire pourrait la poser par erreur, et l'oubli cesserait d'être un refus |
| **Les paquets `communication` et `finance` créés avec un seul fichier chacun** | Les abstractions SMS et paiement doivent exister derrière une interface dès T0a (FR-036) et vivre là où T4a et T8b les remplaceront | Un paquet `integrations` transverse : un nom hors de la cible de 01-stack § 2.3, et un déménagement au moment du remplacement |
| **Un espace de travail `pnpm` à la racine avant que `web/` existe** | P-03 doit régénérer le client typé **hors ligne** ; un `pnpm dlx` téléchargerait à chaque vérification (FR-002). Le lockfile donne aussi à P-02 son second fichier dès T0a | Générer les types côté Python : aucun générateur mature. Attendre T0b : le critère de fin de T0a — « un client typé régénéré sans écart » — ne serait pas atteint |

Et un choix qui n'est pas de la complexité mais qu'il faut voir : **Q28 appliquée à titre
provisoire** — `assistance.suspendue`, `ÉTABLISSEMENT`, `false` — parce que le plan devait dériver
d'un catalogue qui porte la clé ([R-20](research.md)). Changer la clé, la portée ou le défaut touche
trois lignes nommées.

## Phase 0 — Recherche

Produite : [research.md](research.md). Vingt-deux décisions, chacune avec son motif et ses
alternatives, dont les points que la spec laissait ouverts : la disposition de l'espace de travail
(vérifiée dans un bac à sable `uv`), le mécanisme des trois verrous, le support et la clé de la
mémorisation, la politique RLS et ses deux fonctions, l'emplacement de l'outbox, le lieu du client
typé, le mécanisme de P-12, l'isolation des tests négatifs, l'ordre des portes. Aucune
« NEEDS CLARIFICATION » ne subsiste.

## Phase 1 — Conception et contrats

Produits :

- [data-model.md](data-model.md) — les cinq tables du schéma `tenants` avec colonnes, contraintes,
  index et politiques ; le catalogue seedé ligne pour ligne depuis § 17 ; les transitions de
  l'outbox ; les deux fonctions du schéma ; ce qui vit dans Valkey ; les schémas Pydantic ; les
  entités hors base.
- [contracts/openapi-attendu.yaml](contracts/openapi-attendu.yaml) — les trois routes, leurs
  en-têtes de middleware, leurs codes et leurs schémas, tels que la génération doit les produire ; un
  test compare `contrat/openapi.json` à ce fichier.
- [contracts/interfaces-python.md](contracts/interfaces-python.md) — l'interface de service de
  chaque paquet, les trois abstractions face à leur fournisseur réel, la composition dans `api/`.
- [quickstart.md](quickstart.md) — les commandes et les résultats attendus, user story par user
  story, jusqu'aux deux commandes de vérification.

## Ce que le plan remet à `/speckit-tasks`

L'ordre des tâches suit l'ordre des user stories de la spec — US1 est le critère de fin, US2 et US3
les fondations — avec une contrainte : **les portes se construisent avec ce qu'elles vérifient**,
pas après. La première tâche pose `pyproject.toml`, la composition et `scripts/verifier.sh` vide ;
chaque tâche suivante ajoute une porte ou la matière d'une porte, et `verifier.sh` reste vert à
chaque commit. Les tests négatifs s'écrivent avec chaque porte, pas en fin de tranche.

## Diffs sur les documents projet — arbitrés et appliqués le 2026-09-14

Détaillés en fin de [research.md](research.md) et de [data-model.md](data-model.md). Les sept ont
été retenus tels que proposés, sur demande de l'utilisateur ; les documents projet font foi :

| Fichier | Quoi | Statut |
|---|---|---|
| `02-domaine.md § 17` | `assistance.suspendue` \| ÉTABLISSEMENT \| `false` | **Appliqué** — Q28 close |
| `01-stack.md § 2.3` | `contrat/` et les quatre fichiers d'espace de travail à la racine | **Appliqué** |
| `01-stack.md § 3` | `uv run fastapi dev api/main.py` depuis la racine | **Appliqué** |
| `01-stack.md § 2.5` | l'outbox est une table **du schéma de chaque module** | **Appliqué** |
| `03-api.md § 1.8` | `503` → `API_DEPENDANCE_INDISPONIBLE`, `details.dependance` | **Appliqué** |
| `03-api.md § 2.3` | `TEN_VALEUR_INVALIDE` (`422`) pour une valeur d'un mauvais type sur une clé connue | **Appliqué** |
| `02-domaine.md § 1.2` | la table `evenement_outbox` du schéma `tenants` | **Appliqué** |

Aucun n'ajoute de route : les trois routes de la tranche figurent déjà au contrat (FR-031).

## Revérification post-conception

Le contrôle de constitution a été relu après la phase 1 : le modèle ne porte aucune donnée
d'élève, aucune littérale de pays, aucune clé étrangère sortante, aucune table sans politique ;
chaque écriture porte sa clé d'idempotence et son événement ; aucune capacité d'assistance n'est
livrée ; `api/` ne porte aucune règle métier. **Verdict inchangé : passe.**

Les deux points laissés à l'utilisateur ont été tranchés le 2026-09-14 : Q28 est confirmée avec les
six autres diffs, et la tranche se construit sur la branche `001-socle-serveur`. Prochaine étape :
`/speckit-tasks`.
