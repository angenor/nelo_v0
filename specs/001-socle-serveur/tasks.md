# Tâches : Le socle serveur (T0a)

**Entrée** : les documents de conception de `specs/001-socle-serveur/` — [plan.md](plan.md),
[spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md).

**Tests** : la spécification les exige — l'isolation entre deux tenants est « prouvée par un test
automatisé » (US2), chaque porte a son test négatif (US5), toute fonction d'accès aux données non
exercée fait échouer la vérification (P-12). Les tâches de test sont donc livrées **avant**
l'implémentation de chaque story, et doivent échouer avant qu'elle n'existe.

**Organisation** : par user story, dans l'ordre de priorité de la spec. Une contrainte du plan
traverse toutes les phases : **les portes se construisent avec ce qu'elles vérifient**, et
`scripts/verifier.sh` reste vert à chaque commit — il s'allonge d'une porte à la fois.

## Format : `[ID] [P?] [Story] Description`

- **[P]** : parallélisable — fichiers différents, aucune dépendance sur une tâche inachevée
- **[Story]** : la user story servie (US1 … US7)
- Chaque description porte son chemin exact, relatif à la racine du dépôt

## Conventions de chemins

Celles de [plan.md](plan.md) « Structure du projet » : `api/`, `modules/{domaine,shared,socle,
metier,segments}/`, `migrations/tenants/`, `scripts/portes/`, `tests/`, `contrat/`. Tout est en
français, accents compris dans les commentaires et les messages ; les identifiants SQL et Python
restent sans accent.

---

## Phase 1 : Mise en place (infrastructure partagée)

**But** : le dépôt a sa forme cible, ses espaces de travail verrouillés, sa composition, et une
commande de vérification qui passe — vide de portes, mais déjà là.

- [X] T001 Créer l'arborescence des paquets aux chemins littéraux du corpus : `modules/domaine/__init__.py`, `modules/shared/__init__.py`, `modules/socle/tenants/__init__.py`, `modules/socle/assistance/__init__.py`, `modules/socle/communication/__init__.py`, `modules/metier/protection/__init__.py`, `modules/metier/finance/__init__.py`, `modules/segments/.gitkeep`, `api/__init__.py`, `api/routes/__init__.py`, `migrations/tenants/versions/.gitkeep`, `scripts/portes/negatifs/.gitkeep`, `tests/__init__.py`, `contrat/.gitkeep` — **aucun** `__init__.py` dans `modules/`, `modules/socle/`, `modules/metier/`, `modules/segments/` (espaces de noms PEP 420)
- [X] T002 Écrire `pyproject.toml` à la racine : projet `nelo`, `requires-python = "==3.14.*"`, dépendances épinglées exactement selon [research.md R-02](research.md) (`fastapi==0.141.1`, `pydantic==2.13.5`, `pydantic-settings==2.15.0`, `uvicorn==0.52.4`, `sqlalchemy==2.0.52`, `asyncpg==0.31.0`, `alembic==1.19.2`, `valkey==6.1.1`), groupe `dev` (`pytest==9.1.1`, `pytest-asyncio==1.4.0`, `httpx==0.28.1`, `coverage==7.16.0`, `ruff==0.16.6`, `import-linter==2.15`, `pip-licenses==5.5.5`), `[build-system]` hatchling avec `packages = ["modules", "api"]`, `[tool.uv.workspace] members` = les huit paquets, `[tool.uv.sources]` workspace, `[tool.ruff]` (cible py314, règles `E F I B S608 UP`, format), `[tool.pytest.ini_options]` (`asyncio_mode = "auto"`, `testpaths = ["tests"]`), `[tool.coverage.run]` (`source = ["modules", "api"]`) ; écrire `.python-version` = `3.14`
- [X] T003 [P] Écrire un `pyproject.toml` **déclaratif** par paquet, chacun avec `[tool.uv] package = false` et ses dépendances internes : `modules/shared/pyproject.toml` (`nelo-shared`, aucune), `modules/domaine/pyproject.toml` (`nelo-domaine`, aucune), `modules/socle/tenants/pyproject.toml` (`nelo-socle-tenants` → shared, domaine), `modules/socle/assistance/pyproject.toml` (`nelo-socle-assistance` → shared), `modules/socle/communication/pyproject.toml` (`nelo-socle-communication` → shared), `modules/metier/protection/pyproject.toml` (`nelo-metier-protection` → shared, domaine), `modules/metier/finance/pyproject.toml` (`nelo-metier-finance` → shared), `api/pyproject.toml` (`nelo-api` → socle-tenants, socle-assistance, shared) — **aucun ne déclare `nelo-metier-protection`**
- [X] T004 Exécuter `uv lock` puis `uv sync` à la racine, vérifier que `uv.lock` liste les neuf projets et que `uv run python -c "import api, modules.socle.tenants"` passe **depuis un autre répertoire** ; commiter `uv.lock`
- [X] T005 [P] Écrire `package.json` à la racine (`private: true`, `packageManager: "pnpm@10.26.2"`, `devDependencies: { "openapi-typescript": "7.13.0" }`, script `contrat:client` = `openapi-typescript contrat/openapi.json -o contrat/client.d.ts`) et `pnpm-workspace.yaml` (`packages: ["web"]`) ; exécuter `pnpm install` ; commiter `pnpm-lock.yaml`
- [X] T006 [P] Écrire `compose.yml` : trois services et pas un de plus — `postgres` (`postgres:18.6-alpine`, `POSTGRES_USER=nelo_proprietaire`, `POSTGRES_DB=nelo`, healthcheck `pg_isready`, port 5432), `valkey` (`valkey/valkey:9.1.2-alpine`, port 6379), `garage` (`dxflrs/garage:v2.4.1`, `garage.toml` mono-nœud monté, ports 3900/3903) ; écrire `garage.toml` minimal ; vérifier `docker compose config --services` rend exactement trois lignes
- [X] T007 [P] Écrire `.env.exemple` avec les variables `NELO_` lues par la configuration : `NELO_BD_URL` (rôle `nelo_app`), `NELO_BD_URL_PROPRIETAIRE` (rôle `nelo_proprietaire`, migrations), `NELO_VALKEY_URL`, `NELO_TRAVAILLEUR_INTERVALLE_MS=500`, `NELO_SIMULATION_SMS_MODE=SUCCES`, `NELO_SIMULATION_PAIEMENT_MODE=SUCCES`, `NELO_SIMULATION_INFERENCE_MODE=SUCCES`, `NELO_SIMULATION_DELAI_MS=100`
- [X] T008 [P] Mettre à jour `.gitignore` : retirer la section « Rust » et le commentaire « sidecar IA » devenus faux, ajouter `.coverage`, `coverage.json`, `.pytest_cache/`, `.ruff_cache/`, `.venv/` déjà présent ; **ne pas** ignorer `contrat/`
- [X] T009 Écrire `scripts/verifier.sh` (`set -euo pipefail`) : une fonction `porte` qui lance `scripts/portes/p-XX.sh`, affiche `PORTE P-XX : …` en succès et `PORTE P-XX ÉCHOUÉE : <motif>` en échec, et sort au premier rouge ; pour l'instant une seule étape, `uv run ruff check .` et `uv run ruff format --check .` ; chronomètre total affiché en fin ; `chmod +x`
- [X] T010 [P] Écrire `scripts/bd-vierge.sh` : attend `postgres` (healthcheck), `DROP DATABASE IF EXISTS "$NELO_BD_NOM"` et `CREATE DATABASE` (défaut `nelo`, surchargeable pour les tests négatifs), crée le rôle `nelo_app` (`LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB`) s'il n'existe pas, applique `uv run alembic -c migrations/tenants/alembic.ini upgrade head` sous `nelo_proprietaire`, option `--avec-jeu-d-essai` qui appelle `uv run python -m scripts.jeu_essai` ; `chmod +x`

---

## Phase 2 : Fondations (prérequis bloquants)

**But** : le point d'entrée transactionnel, l'enveloppe d'erreur, le schéma `tenants` migré avec
ses politiques, les deux middlewares et le squelette de l'application. Sans cela, aucune story ne
peut être testée.

**⚠️ CRITIQUE** : aucune story ne commence avant la fin de cette phase.

- [X] T011 Écrire `modules/shared/erreurs.py` : `EnveloppeErreur` (Pydantic : `code`, `message`, `champ`, `details`, `requete_id` — [03-api.md § 1.6](../../docs/03-api.md)), `ErreurMetier(Exception)` (`code`, `statut=422`, `champ`, `details`), `DependanceIndisponible(Exception)` (`dependance` ∈ `PASSERELLE_SMS | AGREGATEUR_PAIEMENT | SERVICE_INFERENCE`)
- [X] T012 [P] Écrire `modules/shared/simulation.py` : `ModeSimulation(StrEnum)` = `SUCCES`, `ACCUSE_EN_RETARD`, `ACCUSE_EN_DOUBLE`, `JAMAIS_RECU`, `INDISPONIBLE`
- [X] T013 [P] Écrire `modules/shared/evenement.py` : `Evenement` (dataclass gelée : `type: str`, `charge: dict`)
- [X] T014 Écrire `modules/shared/bd.py` : moteur `create_async_engine` (asyncpg, `NELO_BD_URL`, taille de pool configurable), et **l'unique point d'entrée** `transaction(tenant_id: UUID)` — gestionnaire de contexte asynchrone qui ouvre `engine.begin()`, exécute `SELECT set_config('app.current_tenant', :tenant, true)` avec la valeur liée, rend la connexion, referme ; docstring : « aucun autre code n'ouvre de transaction » ([research.md R-07](research.md))
- [X] T015 Écrire `modules/shared/__init__.py` : `__all__` = `transaction`, `EnveloppeErreur`, `ErreurMetier`, `DependanceIndisponible`, `ModeSimulation`, `Evenement` — rien d'autre
- [X] T016 Écrire `modules/socle/tenants/tables.py` : `MetaData(schema="tenants")` et les cinq `Table` de [data-model.md](data-model.md) — `tenant`, `etablissement`, `parametre_catalogue`, `parametre_valeur`, `evenement_outbox` — colonnes, types, `CHECK`, unicité `(tenant_id, cle, portee, portee_id)`, index `(tenant_id, etat, ecrit_le, id)`, FK internes au schéma seulement
- [X] T017 [P] Écrire `modules/socle/tenants/catalogue_seed.py` : la liste des dix-sept entrées de [data-model.md](data-model.md) « Le catalogue seedé » (`cle`, `portee_la_plus_basse`, `type`, `valeur_defaut`, `origine_defaut`, `description_cle`), dont `assistance.suspendue | ETABLISSEMENT | BOOLEEN | false | LITTERALE`
- [X] T018 Écrire `migrations/tenants/alembic.ini` (`script_location = migrations/tenants`, `version_table_schema = tenants`) et `migrations/tenants/env.py` (asynchrone, `target_metadata` = `tables.metadata`, URL `NELO_BD_URL_PROPRIETAIRE`, `include_schemas` limité à `tenants`)
- [X] T019 Écrire `migrations/tenants/versions/0001_socle_tenants.py` — `upgrade` : `CREATE SCHEMA tenants`, les cinq tables depuis `tables.py`, `ENABLE` **et** `FORCE ROW LEVEL SECURITY` sur chacune, les politiques de [data-model.md](data-model.md) (expression `tenant_id = current_setting('app.current_tenant', true)::uuid` ; `id = …` sur `tenant` ; `SELECT` seul avec `current_setting(...) IS NOT NULL` sur `parametre_catalogue` ; pas de `DELETE` sur `evenement_outbox`), `GRANT USAGE ON SCHEMA` et `GRANT SELECT, INSERT, UPDATE` à `nelo_app` (SELECT seul sur le catalogue), les deux fonctions `SECURITY DEFINER STABLE` `tenants.tenant_de_etablissement(uuid) → uuid` et `tenants.tenants_pour_travailleur() → setof uuid` avec `REVOKE ALL FROM PUBLIC` puis `GRANT EXECUTE TO nelo_app`, et l'`INSERT` du catalogue depuis `catalogue_seed.py` ; `downgrade` : l'inverse jusqu'à `DROP SCHEMA tenants` — **réversible et exercé**
- [X] T020 Écrire `api/configuration.py` : `Configuration(BaseSettings)` préfixe `NELO_`, champs de `.env.exemple` (T007) avec leurs défauts, `ModeSimulation` typé pour les trois modes, `timedelta` pour les délais
- [X] T021 Écrire `api/erreurs.py` : gestionnaire de `RequestValidationError` → `422` enveloppe `VAL_SCHEMA_INVALIDE`, `champ` = premier chemin, `details.champs = [{chemin, motif}]` pour **tous** les champs ; `ErreurMetier` → son `statut` et son enveloppe ; `DependanceIndisponible` → `503 API_DEPENDANCE_INDISPONIBLE`, `details.dependance` ; toute autre exception → `500 API_ERREUR_INTERNE`, `message` fixe sans détail technique, trace dans le journal seulement ; `requete_id` lu de `request.state` (ou `None`)
- [X] T022 Écrire `api/tenant_provisoire.py` : middleware ASGI pur (pas `BaseHTTPMiddleware`) — laisse passer `/api/v1/sante`, `/openapi.json`, `/docs` ; lit `X-Nelo-Etablissement` ; absent ou pas un UUID → `400 TEN_ETABLISSEMENT_REQUIS` ; résout par `tenants.tenant_de_etablissement` ; inconnu → `404 TEN_RESSOURCE_INTROUVABLE` ; dépose `tenant_id` et `etablissement_id` dans `scope["state"]` ; l'enveloppe reprend la valeur brute de `X-Nelo-Requete` si présente ; docstring : **PROVISOIRE jusqu'à T1a** ([research.md R-16](research.md))
- [X] T023 Écrire `api/idempotence.py` — **première partie** : middleware ASGI pur, sur `POST PUT PATCH DELETE` seulement ; `X-Nelo-Requete` absent → `400 REQUETE_CLE_MANQUANTE` ; présent mais pas un UUID **v7** (`uuid.UUID(...).version == 7`) → `400 REQUETE_CLE_INVALIDE` ; dépose `requete_id` dans `scope["state"]` ; la mémorisation Valkey arrive en T057 — laisser le point d'accroche explicite
- [X] T024 Écrire `api/capacites.py` : `exiger_capacite(code: str)` — journalise `capacite exigée : <code>` et laisse passer ; docstring : **point d'insertion vide jusqu'à T1b**, jamais retiré
- [X] T025 Écrire `api/main.py` : `creer_application()` — `FastAPI(title="Nelo — API", version="1", root_path="/api/v1")`, middlewares dans l'ordre **tenant provisoire (extérieur) puis idempotence (intérieur)**, gestionnaires de T021, `lifespan` avec un point d'accroche pour le travailleur (T060), `app.state` pour le client Valkey et la configuration ; `app = creer_application()`
- [X] T026 Écrire `modules/socle/tenants/acces.py` — **première partie** : `inserer_tenant`, `inserer_etablissement`, `appeler_tenant_de_etablissement`, `appeler_tenants_pour_travailleur` (SQLAlchemy Core, valeurs liées, aucune concaténation) ; et `modules/socle/tenants/service.py` — **première partie** : `creer_tenant(...)`, `creer_etablissement(tenant_id, ...)`, `tenant_de_etablissement(etablissement_id)` (UUID v7 générés par `uuid.uuid7()`) ; `modules/socle/tenants/__init__.py` exporte ces trois fonctions
- [X] T027 [P] Écrire `scripts/jeu_essai.py` : crée les tenants A (`pays_code="CI"` en **donnée**, `fuseau_horaire="Africa/Abidjan"`) et B avec un établissement chacun via `tenants.creer_tenant` / `creer_etablissement`, imprime `ETAB_A=… ETAB_B=…` en forme `export`
- [X] T028 Écrire `tests/conftest.py` : fixture de session `base_migree` (base logique de test `nelo_test` recréée par la logique de `bd-vierge.sh`, `upgrade head`), fixture `tenants_ab` (A, B, leurs établissements), fixture `client` (`httpx.AsyncClient` sur `ASGITransport(app)`), fixture `valkey` (client vidé avant chaque test), option `--pool-un` / fixture `moteur_pool_un` (taille de pool 1) pour l'isolation, fixture `requete_id` (`uuid.uuid7()`), marqueur `suspension` lu de `NELO_TEST_SUSPENSION` (T090)

**Point de contrôle** : `docker compose up -d && scripts/bd-vierge.sh --avec-jeu-d-essai && uv run fastapi dev api/main.py` démarre ; `scripts/verifier.sh` est vert (ruff seul) ; `uv run pytest` collecte sans erreur.

---

## Phase 3 : User Story 1 — Le module doré répond, et son contrat se régénère sans écart (Priorité : P1) 🎯 MVP

**But** : `GET /parametres` et `PUT /parametres/{cle}` répondent selon le contrat, le refus de
schéma précède toute règle, les deux refus métier ont leur code, l'événement s'écrit dans la
transaction, `/sante` répond sans en-tête, et le contrat généré ne diffère en rien du commité.

**Test indépendant** : sur base vierge, démarrer, lire les paramètres d'un tenant, poser une
valeur, la relire, régénérer le client, constater un diff vide — [quickstart.md](quickstart.md)
« Lire et poser » et « Régénérer le contrat ».

### Tests pour la User Story 1

> Écrits d'abord ; ils **doivent échouer** avant T036.

- [X] T029 [P] [US1] Écrire `tests/module_dore/test_sante.py` : `GET /api/v1/sante` sans aucun en-tête → `200 {"etat":"OK"}` ; ne touche ni la base ni Valkey (base arrêtée dans le test par un moteur factice)
- [X] T030 [P] [US1] Écrire `tests/module_dore/test_lecture.py` : `GET /parametres` avec `X-Nelo-Etablissement` → dix-sept entrées, `source=DEFAUT` pour les défauts littéraux, `NON_DEFINIE` pour `sms.plafond_mensuel` et les clés `COUNTRY_PACK`, `portee_resolue` nulle sans valeur posée ; une valeur posée au `TENANT` puis une autre à l'`ETABLISSEMENT` : la surcharge locale gagne, la portée résolue le dit (FR-011, surcharges partielles) ; sans en-tête → `400 TEN_ETABLISSEMENT_REQUIS` ; UUID inconnu → `404 TEN_RESSOURCE_INTROUVABLE`
- [X] T031 [P] [US1] Écrire `tests/module_dore/test_ecriture.py` : `PUT /parametres/assistance.suspendue` avec `X-Nelo-Requete` et corps `{portee: ETABLISSEMENT, portee_id, valeur: true}` → `200 ParametrePose` ; la relecture reflète la valeur ; **exactement un** événement `tenants.parametre.pose` dans `tenants.evenement_outbox` avec la charge attendue ; un second `PUT` sur la même clé et portée met à jour sans doublon (clé naturelle)
- [X] T032 [P] [US1] Écrire `tests/module_dore/test_refus_schema.py` : corps `{portee: "NULLE_PART", valeur: true}` (deux champs fautifs : `portee` invalide, `portee_id` manquant) → `422`, `code=VAL_SCHEMA_INVALIDE`, `details.champs` cite **les deux** chemins, `requete_id` reprend l'en-tête, `champ` = le premier ; le corps est refusé **avant** toute règle : aucune lecture du catalogue (espion sur `acces.lire_catalogue`)
- [X] T033 [P] [US1] Écrire `tests/module_dore/test_refus_metier.py` : clé `inconnue.cle` → `422 TEN_PARAMETRE_INCONNU` avec `details.cles_connues` ; `securite.duree_session_minutes` (portée la plus basse `TENANT`) posée à `ETABLISSEMENT` → `422 TEN_PORTEE_INVALIDE`, `details.portee_la_plus_basse` ; portée `SITE` → `422 TEN_PORTEE_INVALIDE`, `details.portees_disponibles == ["TENANT","ETABLISSEMENT"]` ; `portee=TENANT` avec `portee_id` ≠ tenant courant → `422 TEN_PORTEE_INVALIDE`, `details.motif=HORS_TENANT` ; `valeur: "oui"` sur un `BOOLEEN` → `422 TEN_VALEUR_INVALIDE`, `champ=valeur`, `details.type_attendu=BOOLEEN` ; dans chaque cas le statut est celui du refus de schéma et **le code diffère**
- [X] T034 [P] [US1] Écrire `tests/module_dore/test_point_insertion.py` : un espion sur `api.capacites.exiger_capacite` constate qu'elle est appelée avec `tenant.parametre.definir` par la route `PUT`, et jamais par `GET /sante`
- [X] T035 [P] [US1] Écrire `tests/portes/test_contrat_attendu.py` : charge `specs/001-socle-serveur/contracts/openapi-attendu.yaml` et `contrat/openapi.json` ; pour chaque chemin et méthode attendus, les codes de réponse déclarés sont présents, les en-têtes `X-Nelo-Etablissement` et `X-Nelo-Requete` sont des paramètres **requis**, les schémas `EnveloppeErreur`, `ReponseParametres`, `CorpsPoserParametre`, `ParametrePose`, `ReponseSante` existent avec leurs champs requis ; le `422` de `PUT` référence `EnveloppeErreur`

### Implémentation de la User Story 1

- [X] T036 [US1] Écrire `modules/socle/tenants/schemas.py` : `Portee(StrEnum)`, `TypeParametre(StrEnum)`, `ParametreEffectif`, `ReponseParametres`, `CorpsPoserParametre` (`extra="forbid"`, `valeur: bool | int | str | None`), `ParametrePose`, `ReponseSante` — conformes à [contracts/openapi-attendu.yaml](contracts/openapi-attendu.yaml) ; `DECIMAL` voyage en chaîne
- [X] T037 [US1] Compléter `modules/socle/tenants/acces.py` : `lire_catalogue(conn)`, `lire_valeurs_posees(conn, tenant_id, cles)`, `lire_etablissement(conn, etablissement_id)` (rend `None` si invisible), `upsert_valeur(conn, ...)` (`INSERT … ON CONFLICT (tenant_id, cle, portee, portee_id) DO UPDATE`, `RETURNING`), `inserer_evenement(conn, tenant_id, evenement)` — Core, valeurs liées
- [X] T038 [US1] Compléter `modules/socle/tenants/service.py` : `valeur_effective(...)` — **un seul trait** de résolution `CYCLE → SITE → ETABLISSEMENT → TENANT → défaut → NON_DEFINIE`, rendant la portée résolue ; `lire_parametres_effectifs(tenant_id, etablissement_id)` ; `poser_parametre(tenant_id, cle, portee, portee_id, valeur)` — règles 1 à 5 de [data-model.md](data-model.md) dans l'ordre (catalogue, portée la plus basse, portées disponibles, hors tenant / établissement invisible → `404`, type de valeur), puis dans **la même** `transaction(tenant_id)` : `upsert_valeur` **et** `inserer_evenement(Evenement("tenants.parametre.pose", {...}))` ; aucune classe de base, aucun dépôt générique (FR-010)
- [X] T039 [US1] Compléter `modules/socle/tenants/__init__.py` : `__all__` = exactement la liste de [contracts/interfaces-python.md](contracts/interfaces-python.md) — ni `tables`, ni `acces`, ni le moteur
- [X] T040 [P] [US1] Écrire `api/routes/sante.py` : `GET /sante` → `ReponseSante(etat="OK")`, sans dépendance, sans accès à la base
- [X] T041 [US1] Écrire `api/routes/parametres.py` : `GET /parametres` (lit `tenant_id`, `etablissement_id` de `request.state`, appelle `tenants.lire_parametres_effectifs`) et `PUT /parametres/{cle}` (appelle `exiger_capacite("tenant.parametre.definir")` puis `tenants.poser_parametre`) ; `responses=` déclare `400`, `404`, `409`, `422`, `500` avec `EnveloppeErreur` et la description de [contracts/openapi-attendu.yaml](contracts/openapi-attendu.yaml) ; inclure les routeurs dans `api/main.py` ; **aucune règle métier dans le gestionnaire**
- [X] T042 [US1] Écrire `api/contrat.py` : `openapi()` personnalisé qui ajoute `X-Nelo-Etablissement` (toutes routes sauf `/sante`) et `X-Nelo-Requete` (écritures) en paramètres d'en-tête **requis** avec leurs descriptions, et le `422 VAL_SCHEMA_INVALIDE` sur toute route avec corps ; `python -m api.contrat` écrit `contrat/openapi.json` **stable** (`json.dumps(sort_keys=True, indent=2, ensure_ascii=False)` + saut de ligne final)
- [X] T043 [US1] Écrire `scripts/portes/p-03.sh` : `uv run python -m api.contrat`, `pnpm exec openapi-typescript contrat/openapi.json -o contrat/client.d.ts`, puis `git diff --exit-code -- contrat/` ; succès `PORTE P-03 : 2 fichiers régénérés, 0 ligne d'écart` ; échec avec les premières lignes du diff ; ajouter P-03 à `scripts/verifier.sh` (dernière étape)
- [X] T044 [US1] Générer et commiter `contrat/openapi.json` et `contrat/client.d.ts` ; vérifier que `scripts/portes/p-03.sh` passe deux fois de suite (génération déterministe)
- [X] T045 [P] [US1] Écrire `scripts/portes/negatifs/p-03.sh` : ajoute une ligne `// modifié à la main` à `contrat/client.d.ts` dans la copie de travail (la porte doit échouer sur l'écart)

**Point de contrôle** : US1 est fonctionnelle et testable seule ; `scripts/verifier.sh` = ruff + P-03, vert ; SC-002 (zéro ligne d'écart) et SC-007 (le refus de schéma est dans la spécification générée) tenus.

---

## Phase 4 : User Story 2 — Deux tenants ne se voient jamais (Priorité : P2)

**But** : la RLS est activée et forcée sur chaque table, la variable est posée par transaction,
le rôle applicatif est distinct du propriétaire, et un test le prouve — y compris sur une
connexion réutilisée. P-01 le vérifie mécaniquement.

**Test indépendant** : `uv run pytest tests/isolation -q` (quatre verts) et
`scripts/portes/p-01.sh` ; casser une politique fait échouer la porte en nommant la table.

### Tests pour la User Story 2

- [X] T046 [P] [US2] Écrire `tests/isolation/test_deux_tenants.py` : A et B portent chacun des valeurs ; `GET /parametres` de A ne montre aucune valeur de B (source, portée) ; `PUT` de A avec `portee=ETABLISSEMENT` et `portee_id=ETAB_B` → `404 TEN_RESSOURCE_INTROUVABLE`, **jamais `403`** ; sur **chaque** table du schéma (énumérées depuis `information_schema.tables`), un `SELECT count(*)` dans `transaction(A)` ne compte que les lignes de A
- [X] T047 [P] [US2] Écrire `tests/isolation/test_sans_variable.py` : une transaction ouverte par `engine.begin()` **sans** `set_config` voit **zéro** ligne sur chaque table du schéma — pas « toutes » — et tout `INSERT` est refusé (`new row violates row-level security policy`) ; y compris `parametre_catalogue` (invisible sans variable)
- [X] T048 [P] [US2] Écrire `tests/isolation/test_pool_reutilise.py` : avec `moteur_pool_un`, une transaction de A puis une transaction de B sur **la même** connexion (assertion sur `pg_backend_pid()` identique) : B ne voit rien de A, et `current_setting('app.current_tenant', true)` est vide entre les deux
- [X] T049 [P] [US2] Écrire `tests/isolation/test_role_applicatif.py` : `current_user == 'nelo_app'` dans une transaction applicative ; `pg_roles.rolbypassrls` est faux pour `nelo_app` ; chaque table du schéma appartient à `nelo_proprietaire` et porte `relrowsecurity` **et** `relforcerowsecurity`
- [X] T050 [P] [US2] Écrire `tests/portes/test_security_definer.py` : énumère `pg_proc.prosecdef = true` dans les schémas de modules (`tenants` en T0a) ; l'ensemble est **exactement** `{tenant_de_etablissement, tenants_pour_travailleur}` ; chacune appartient à `nelo_proprietaire`, `PUBLIC` n'a pas `EXECUTE`

### Implémentation de la User Story 2

- [X] T051 [US2] Écrire `scripts/portes/p-01.sh` et `scripts/portes/p01_schema.py` : recrée la base logique (`bd-vierge.sh` sans jeu d'essai), `upgrade head` → `downgrade base` → `upgrade head` (réversibilité exercée), vérifie qu'à chaque schéma de module présent en base correspond un dossier `migrations/<module>/`, puis lit `pg_class` (`relrowsecurity` **et** `relforcerowsecurity` sur chaque table des schémas de modules), `pg_policies` (au moins une politique par table), `pg_constraint` (aucune FK dont la table référencée est dans un autre schéma) ; succès `PORTE P-01 : N tables, N politiques, 0 clé étrangère traversante` ; échec **nomme la table** ; ajouter P-01 à `verifier.sh` avant P-03
- [X] T052 [P] [US2] Écrire `scripts/portes/negatifs/p-01.sh` : dans la copie, commente la ligne `FORCE ROW LEVEL SECURITY` de `parametre_valeur` dans `migrations/tenants/versions/0001_socle_tenants.py` (la porte doit échouer en nommant `tenants.parametre_valeur`)

**Point de contrôle** : US1 et US2 tiennent ; SC-004 (zéro ligne d'un autre tenant, sur chaque table, connexion réutilisée comprise) prouvé ; `verifier.sh` = ruff, P-01, P-03.

---

## Phase 5 : User Story 3 — Aucune saisie ne se perd : rejeu et événements (Priorité : P2)

**But** : la réponse d'une écriture est mémorisée 24 h dans Valkey, bornée au tenant ; un rejeu
identique rend la même réponse sans réexécuter ; un rejeu divergent est refusé ; le travailleur du
même processus consomme les événements, dans l'ordre par tenant, sans jamais en perdre.

**Test indépendant** : `uv run pytest tests/idempotence tests/outbox -q` — dépend de US1 (le
module doré est le support de l'écriture rejouée).

### Tests pour la User Story 3

- [ ] T053 [P] [US3] Écrire `tests/idempotence/test_rejeu.py` : `PUT` avec `R` puis rejeu identique → statut et corps **identiques octet pour octet**, une seule valeur, **un seul** événement (espion sur `poser_parametre` : un appel) ; rejeu avec `R` et un corps différent → `409 REQUETE_REJOUEE_DIFFEREMMENT` ; la clé `idem:{tenant}:{R}` porte un TTL ≤ 24 h ; **borné au tenant** : B rejoue `R` de A avec son propre corps → exécuté normalement, pas de `409` ; un rejeu identique après effacement de la clé (expiration simulée) est une requête nouvelle → `200`, second événement (edge case « rejeu après expiration »)
- [ ] T054 [P] [US3] Écrire `tests/idempotence/test_en_tete.py` : `PUT` sans `X-Nelo-Requete` → `400 REQUETE_CLE_MANQUANTE`, `requete_id` nul ; avec un UUID v4 → `400 REQUETE_CLE_INVALIDE` ; avec `"abc"` → `400 REQUETE_CLE_INVALIDE` ; `GET` sans en-tête → pas de refus ; l'enveloppe est complète
- [ ] T055 [P] [US3] Écrire `tests/outbox/test_transaction.py` : un `upsert_valeur` remplacé par une fonction qui lève **après** `inserer_evenement` ; la requête répond `500 API_ERREUR_INTERNE` sans détail, et `tenants.evenement_outbox` ne porte **aucun** événement (le `ROLLBACK` a tout emporté) — US3-4
- [ ] T056 [P] [US3] Écrire `tests/outbox/test_travailleur.py` : un événement écrit puis un tour de boucle → `traite`, `traite_le` posé, le consommateur journal l'a reçu ; un consommateur qui lève → `en_echec`, `tentatives=1`, `derniere_erreur` renseignée, puis `en_attente` au tour suivant, puis `traite` quand le consommateur réussit — **jamais perdu, livré deux fois** ; trois événements de A et deux de B → chaque tenant les reçoit dans l'ordre `ecrit_le, id` ; un événement `pris` depuis plus longtemps que le délai d'orphelin est repris ; le travailleur arrêté accumule, relancé consomme tout

### Implémentation de la User Story 3

- [ ] T057 [US3] Compléter `api/idempotence.py` — **seconde partie** : client Valkey (`valkey.asyncio`), clé `idem:{tenant_id}:{requete_id}` ; empreinte SHA-256 de `méthode + chemin + corps brut` ; `SET NX` d'un marqueur `{en_cours: true, empreinte}` avec TTL 24 h — existe `en_cours` → `409 REQUETE_EN_COURS` ; existe terminé et même empreinte → rejoue la réponse mémorisée (statut, en-têtes de contenu, corps) sans appeler l'application ; empreinte différente → `409 REQUETE_REJOUEE_DIFFEREMMENT` ; sinon laisse passer, capture la réponse ASGI (`http.response.start` / `body`), la mémorise `{empreinte, statut, corps b64, en_cours: false}` avec TTL 24 h ; le corps est relu par l'application via un `receive` rejoué ([research.md R-06](research.md))
- [ ] T058 [US3] Compléter `modules/socle/tenants/acces.py` : `prendre_evenements(conn, tenant_id, n)` (`WHERE etat='en_attente' ORDER BY ecrit_le, id LIMIT n FOR UPDATE SKIP LOCKED` puis `UPDATE … SET etat='pris', pris_le=now()`), `marquer_traite(conn, id)`, `marquer_echec(conn, id, erreur)` (`tentatives+1`, `derniere_erreur`), `reprendre_pris_orphelins(conn, tenant_id, delai)` et `reprendre_en_echec(conn, tenant_id)` (→ `en_attente`) ; et dans `service.py` : `consommer_lot(tenant_id, consommateur, n)` qui enchaîne prise, appel, marquage dans une `transaction(tenant_id)` par événement traité
- [ ] T059 [US3] Écrire `api/travailleur.py` : `Travailleur(configuration, consommateur)` — boucle `asyncio` : `tenants_pour_travailleur()`, pour chaque tenant `reprendre_pris_orphelins`, `reprendre_en_echec`, `consommer_lot` ; `attendre(intervalle)` ; `demarrer()` / `arreter()` propres (annulation attendue) ; consommateur par défaut = journal applicatif (`logging`) ; un tour exposé comme `un_tour()` pour les tests ; **aucune file de messages, aucun autre processus**
- [ ] T060 [US3] Compléter `api/main.py` : le `lifespan` construit le client Valkey, démarre le `Travailleur` au démarrage et l'arrête proprement à l'extinction ; le journal annonce « travailleur d'événements démarré »

**Point de contrôle** : SC-005 (rejeu identique octet pour octet, exactement une valeur et un événement ; rejeu divergent refusé à chaque fois) prouvé ; le `409 REQUETE_EN_COURS` est couvert.

---

## Phase 6 : User Story 4 — Les frontières de paquets tiennent, et un import interdit est arrêté (Priorité : P2)

**But** : la hiérarchie `domaine`, `shared`, `socle`, `metier`, `segments`, `api` est un test ;
`protection` est tenu par trois verrous ; un import différé ou un chemin en chaîne est arrêté ; la
porte annonce ce qu'elle a inspecté et échoue à zéro.

**Test indépendant** : introduire chaque import interdit dans une copie de travail et constater
l'échec nommant l'arête ; `scripts/portes/p-04.sh && scripts/portes/p-11.sh`.

### Tests pour la User Story 4

- [ ] T061 [P] [US4] Écrire `tests/frontieres/test_graphe.py` : construit le graphe avec `grimp.build_graph("api", "modules")` ; **affiche et vérifie** `nombre de modules inspectés > 0` (échec explicite si nul, FR-008) ; le contrat *layers* tient (`api` › `modules.segments` › `modules.metier` › `modules.socle` › `{modules.shared, modules.domaine}` indépendants et sans import sortant hors bibliothèque standard et tiers) ; aucune arête vers `modules.metier.protection` hors de lui-même — imports **au fond des fonctions** compris ; pour chaque arête `paquet_a → paquet_b` entre membres de l'espace de travail, `paquet_a/pyproject.toml` déclare `nelo-<paquet_b>` (la déclaration cesse d'être décorative)
- [ ] T062 [P] [US4] Écrire `tests/frontieres/test_chaines.py` : parcourt en AST tout `.py` de `api/`, `modules/`, `migrations/`, `scripts/`, `tests/` hors `modules/metier/protection/` et hors ce test lui-même ; toute constante de chaîne contenant `modules.metier.protection` ou `metier/protection` échoue en nommant le fichier et la ligne (couvre `importlib.import_module`, `__import__`, chemins écrits)
- [ ] T063 [P] [US4] Écrire `tests/frontieres/test_surface_protection.py` : importe `modules.metier.protection` ; `__all__ == ["ServiceProtection"]` ; aucun attribut public du module n'est une `sqlalchemy.Table`, un `MetaData`, un `Engine`/`AsyncEngine`, ni une fonction dont le nom commence par `lire_`, `inserer_`, `upsert_`, `prendre_`, `marquer_` ; le module n'importe pas `modules.shared.bd`
- [ ] T064 [P] [US4] Écrire `tests/frontieres/test_declarations.py` : lit chaque `pyproject.toml` de l'espace de travail ; aucun ne déclare `nelo-metier-protection` en dépendance, sauf `modules/metier/protection/pyproject.toml` lui-même (son propre nom) ; le `pyproject.toml` racine ne le liste que dans `members`

### Implémentation de la User Story 4

- [ ] T065 [US4] Écrire `modules/metier/protection/__init__.py` : `ServiceProtection(Protocol)` sans opération, docstring « cloisonné — troisième verrou de P-11 », `__all__ = ["ServiceProtection"]` ; `modules/domaine/__init__.py` reste vide avec sa docstring « aucune E/S, aucun pays »
- [ ] T066 [US4] Ajouter à `pyproject.toml` racine `[tool.importlinter]` (`root_packages = ["api", "modules"]`) et deux contrats : `[[tool.importlinter.contracts]]` type `layers` (couches dans l'ordre, `modules.shared | modules.domaine` en couche indépendante), et type `forbidden` (`source_modules` = `api`, `modules.socle`, `modules.metier`, `modules.segments`, `modules.shared`, `modules.domaine` ; `forbidden_modules = ["modules.metier.protection"]` ; `ignore_imports` = les imports internes de `modules.metier.protection`)
- [ ] T067 [US4] Écrire `scripts/portes/p-04.sh` (`uv run lint-imports --contract hierarchie` + `uv run pytest tests/frontieres/test_graphe.py -q`) et `scripts/portes/p-11.sh` (`uv run lint-imports --contract protection` + `uv run pytest tests/frontieres/test_chaines.py tests/frontieres/test_surface_protection.py tests/frontieres/test_declarations.py -q`) ; succès `PORTE P-04 : N modules inspectés, 0 arête interdite` et `PORTE P-11 : 3 verrous, N modules, 0 chaîne suspecte` ; échec **nomme l'arête, le verrou ou le fichier** ; ajouter P-04 puis P-11 à `verifier.sh` avant P-01
- [ ] T068 [P] [US4] Écrire `scripts/portes/negatifs/p-04.sh` (ajoute `from modules.metier.finance import agregateur_paiement` en tête de `modules/socle/tenants/service.py`) et `scripts/portes/negatifs/p-11.sh` (ajoute, **au fond d'une fonction** de `api/routes/parametres.py`, `from modules.metier import protection` — la porte doit échouer sur l'import différé)

**Point de contrôle** : US4 tient ; les cinq scénarios d'acceptation (import module, import différé, chaîne, surface, déclaration, compte non nul) sont couverts ; `verifier.sh` = ruff, P-04, P-11, P-01, P-03.

---

## Phase 7 : User Story 5 — Une seule commande vérifie tout, et chaque porte prouve qu'elle mord (Priorité : P2)

**But** : `scripts/verifier.sh` enchaîne les sept portes dans l'ordre fixé, sort en échec au
premier rouge en nommant la porte et le motif, tient sous trois minutes ; chacune des sept portes
a son test négatif exécutable, en isolation, qui laisse le dépôt intact.

**Test indépendant** : `scripts/verifier.sh` vert sur le dépôt conforme, puis
`scripts/tests-negatifs.sh` : sept échecs attendus, sept obtenus, `git status` identique.

### Implémentation de la User Story 5

- [ ] T069 [P] [US5] Écrire `scripts/portes/p-02.sh` et `scripts/portes/p02_verrouillage.py` : lit `pyproject.toml` racine et de chaque membre, échoue sur tout spécificateur qui n'est pas `==` exact (`>=`, `~=`, `<`, `*`, absent) en **nommant la dépendance** ; `uv lock --check` ; pour chaque espace de travail présent — racine `pnpm` (`package.json`), `web/` s'il existe — son lockfile existe et `pnpm install --frozen-lockfile --offline` passe ; succès `PORTE P-02 : N dépendances épinglées, M lockfiles` ; ajouter P-02 en tête de chaîne après ruff
- [ ] T070 [P] [US5] Écrire `scripts/portes/p-07.sh` et `scripts/portes/p07_licences.py` : `uv run pip-licenses --format=json --with-license-file=false` et `pnpm licenses list --json --long`, normalise (`MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `Zlib`, `Unicode-3.0`/`Unicode-DFS-2016`, `MPL-2.0`, `OFL-1.1`, `PSF-2.0` accepté pour la bibliothèque standard, expressions `A AND B` toutes autorisées) ; toute licence hors liste **ou inconnue** échoue en nommant le paquet ; succès `PORTE P-07 : N paquets Python, M paquets npm, 0 licence refusée` ; ajouter P-07 après P-02
- [ ] T071 [US5] Écrire `scripts/portes/p-12.sh` et `scripts/portes/p12_acces_exerces.py` : `uv run coverage run -m pytest -q` puis `coverage json -o coverage.json` ; parcourt en AST chaque `acces.py` sous `modules/`, et pour chaque fonction, vérifie qu'au moins une ligne de son corps est dans `executed_lines` ; **échoue en nommant** toute fonction non exercée, annonce `N fonctions d'accès inspectées`, échoue à zéro ; puis `alembic.autogenerate.compare_metadata(contexte, tables.metadata)` contre la base migrée → échec au premier écart nommé (colonne absente, type divergent, contrainte manquante) ; ajouter P-12 après P-01
- [ ] T072 [P] [US5] Écrire `tests/portes/test_sql_sans_concatenation.py` : vérifie que `S608` est active dans la configuration `ruff` ; parcourt en AST `modules/` et `api/` : tout appel `text(...)` a pour argument une constante de chaîne, jamais une f-string, un `+` ni un `.format`
- [ ] T073 [US5] Finaliser `scripts/verifier.sh` : chaîne complète **ruff → P-02 → P-07 → P-04 → P-11 → P-01 → P-12 → P-03** (le reparcours de T090 s'ajoutera en fin), arrêt au premier rouge, sortie finale `VÉRIFICATION : 7 portes vertes en <durée>` ; mesurer la durée sur le dépôt conforme et l'inscrire en commentaire de tête (cible < 3 min, SC-010)
- [ ] T074 [US5] Écrire `scripts/tests-negatifs.sh` : relève `git status --porcelain` ; pour chaque porte de `P-01 P-02 P-03 P-04 P-07 P-11 P-12` : `git worktree add` temporaire sur `HEAD`, `uv sync --offline` dans la copie, applique `scripts/portes/negatifs/p-XX.sh`, lance **la porte seule** avec `NELO_BD_NOM=nelo_negatif` pour ne pas toucher la base de travail, exige un code de sortie non nul **et** `PORTE P-XX` dans la sortie, `git worktree remove --force` ; à la fin compare `git status --porcelain` à la valeur d'entrée (différence = échec) ; bilan `7 portes cassées, 7 échecs obtenus, dépôt intact`
- [ ] T075 [P] [US5] Écrire `scripts/portes/negatifs/p-02.sh` (remplace `fastapi==0.141.1` par `fastapi>=0.141` dans `pyproject.toml` de la copie), `scripts/portes/negatifs/p-07.sh` (dépose dans le `site-packages` de la copie un `copyleft_test-0.0.0.dist-info/METADATA` avec `License: GPL-3.0-only` — une dépendance copyleft réellement installée), `scripts/portes/negatifs/p-12.sh` (renomme la colonne `valeur` en `valeur_json` dans `migrations/tenants/versions/0001_socle_tenants.py` de la copie **sans** toucher `tables.py` ni `acces.py`)

**Point de contrôle** : SC-003 — `verifier.sh` passe en une invocation ; sept portes sur sept échouent sous leur test négatif ; dépôt intact. SC-006 — retirer une fonction de `acces.py` du jeu de tests fait échouer P-12 en la nommant. SC-010 — durée sous trois minutes, chiffre noté.

---

## Phase 8 : User Story 6 — Les dépendances externes sont simulées, et savent échouer (Priorité : P3)

**But** : trois abstractions dessinées pour le fournisseur réel, chacune avec sa simulation
active par défaut et ses cinq modes déclenchés par la configuration ; « indisponible » répond
`503` avec l'enveloppe ; « jamais reçu » ne bloque pas.

**Test indépendant** : `uv run pytest tests/simulations -q` — ne dépend d'aucune autre story.

### Tests pour la User Story 6

- [ ] T076 [P] [US6] Écrire `tests/simulations/test_passerelle_sms.py` : paramétré sur les cinq `ModeSimulation` — `SUCCES` : accusé `REMIS` immédiat ; `ACCUSE_EN_RETARD` : `attendre_accuse` rend l'accusé après `delai` et pas avant ; `ACCUSE_EN_DOUBLE` : deux accusés pour la même référence ; `JAMAIS_RECU` : `attendre_accuse(reference, delai_max=200 ms)` rend `None` en ≤ 250 ms (chronométré) ; `INDISPONIBLE` : `envoyer` lève `DependanceIndisponible("PASSERELLE_SMS")`
- [ ] T077 [P] [US6] Écrire `tests/simulations/test_agregateur_paiement.py` : mêmes cinq modes sur `initier` / `attendre_confirmation` ; le montant est un `int` d'unité mineure et un `float` est refusé par la signature (test de type) ; `INDISPONIBLE` lève avec `AGREGATEUR_PAIEMENT`
- [ ] T078 [P] [US6] Écrire `tests/simulations/test_service_inference.py` : mêmes cinq modes sur `soumettre` / `attendre_resultat` ; `INDISPONIBLE` lève avec `SERVICE_INFERENCE`
- [ ] T079 [P] [US6] Écrire `tests/simulations/test_indisponible_503.py` : construit une application de test avec `creer_application()`, y déclare **dans le test** une route `GET /essai-dependance` qui appelle la passerelle en mode `INDISPONIBLE` ; la réponse est `503`, `code=API_DEPENDANCE_INDISPONIBLE`, `details.dependance=PASSERELLE_SMS`, enveloppe complète avec `requete_id`
- [ ] T080 [P] [US6] Écrire `tests/simulations/test_composition.py` : parse `compose.yml` ; exactement trois services `postgres`, `valkey`, `garage` ; aucun nom de service ni d'image ne contient `inference`, `ia`, `assistance`, `llm`

### Implémentation de la User Story 6

- [ ] T081 [P] [US6] Écrire `modules/socle/communication/passerelle_sms.py` : `PasserelleSms(Protocol)` (`envoyer(destinataire_e164, texte, reference) -> ReferenceEnvoi`, `attendre_accuse(reference, delai_max) -> AccuseSms | None`), docstrings face à l'opération du fournisseur réel (soumission, rapport de remise par webhook), `SimulationPasserelleSms(mode, delai)` implémentant les cinq modes avec `asyncio` (jamais de blocage au-delà de `delai_max`) ; `modules/socle/communication/__init__.py` exporte `PasserelleSms`, `SimulationPasserelleSms`
- [ ] T082 [P] [US6] Écrire `modules/metier/finance/agregateur_paiement.py` : `AgregateurPaiement(Protocol)` (`initier(montant_unite_mineure: int, devise: str, reference, payeur_e164) -> ReferencePaiement`, `attendre_confirmation(reference, delai_max) -> ConfirmationPaiement | None`), docstrings face au fournisseur (initiation mobile money, webhook de confirmation — « le webhook qui n'arrive jamais est le cas nominal »), `SimulationAgregateurPaiement(mode, delai)` ; `modules/metier/finance/__init__.py` exporte les deux
- [ ] T083 [P] [US6] Écrire `modules/socle/assistance/service_inference.py` : `ServiceInference(Protocol)` (`soumettre(requete) -> ReferenceInference`, `attendre_resultat(reference, delai_max) -> ResultatInference | None`), docstrings (fournisseur synchrone servi au premier appel, fournisseur par lot servi tel quel), `SimulationServiceInference(mode, delai)`
- [ ] T084 [US6] Compléter `api/main.py` : construit les trois simulations depuis `Configuration` (mode et délai de chacune) et les dépose dans `app.state` (`passerelle_sms`, `agregateur_paiement`, `service_inference`) ; aucune route de T0a ne les appelle — elles existent pour être remplacées

**Point de contrôle** : SC-009 — chaque simulation expose son mode de succès et ses quatre modes d'échec, tous déclenchables par configuration sans modifier le code ; US6-5 — le service d'inférence n'est pas dans la composition.

---

## Phase 9 : User Story 7 — L'assistance a sa place, et sa suspension est un test (Priorité : P3)

**But** : l'assistance est un paquet du socle, son interface connaît les six capacités, aucune
n'est livrée, l'appel est un refus explicite ; `assistance.suspendue` posé par la route d'écriture
la suspend à sa portée ; la vérification reparcourt le module doré sous suspension.

**Test indépendant** : `uv run pytest tests/assistance -q` — dépend de US1 (la suspension se pose
par `PUT /parametres`).

### Tests pour la User Story 7

- [ ] T085 [P] [US7] Écrire `tests/assistance/test_capacites_non_livrees.py` : `etat_des_capacites` rend `NON_LIVREE` pour **les six** `Capacite` ; `appeler` de chacune lève `CapaciteNonLivree` nommant la capacité — ni silence, ni simulation qui réussit
- [ ] T086 [P] [US7] Écrire `tests/assistance/test_suspension.py` : `PUT /parametres/assistance.suspendue` à `ETABLISSEMENT` de `ETAB_A` → `etat_des_capacites(A, ETAB_A)` rend `SUSPENDUE` ×6 et `appeler` lève `AssistanceSuspendue` **avant** `CapaciteNonLivree` ; un second établissement de A n'est pas suspendu ; posée au `TENANT`, les deux établissements le sont ; posée au tenant et remise à `false` sur un établissement, seul l'autre l'est (surcharge locale) ; l'état est une valeur exposée, jamais un libellé
- [ ] T087 [P] [US7] Écrire `tests/assistance/test_aucun_service.py` : `compose.yml` n'a aucun service d'assistance (déjà couvert par T080 — ici : l'espace de travail `uv` n'a aucun projet dont le nom contient `service` ou `serveur` hors `nelo-api`, et `modules/socle/assistance/` ne contient ni `Dockerfile` ni `main.py`)

### Implémentation de la User Story 7

- [ ] T088 [US7] Écrire `modules/socle/assistance/service.py` : `Capacite(StrEnum)` (les six, avec `description_cle` i18n), `EtatCapacite(StrEnum)`, `CapaciteNonLivree`, `AssistanceSuspendue`, `LecteurSuspension = Callable[[UUID, UUID], Awaitable[bool]]`, `Assistance(lecteur_suspension, inference)` avec `etat_des_capacites` et `appeler` ([contracts/interfaces-python.md](contracts/interfaces-python.md)) ; `modules/socle/assistance/__init__.py` exporte `Assistance`, `Capacite`, `EtatCapacite`, `CapaciteNonLivree`, `AssistanceSuspendue`, `ServiceInference`, `SimulationServiceInference` — **aucun import de `modules.socle.tenants`**
- [ ] T089 [US7] Compléter `api/main.py` : construit `Assistance` avec `lecteur_suspension` = fermeture sur `tenants.valeur_effective(tenant_id, "assistance.suspendue", Portee.ETABLISSEMENT, etablissement_id)` (valeur effective **booléenne**), et `service_inference` de `app.state` ; dépose dans `app.state.assistance` — l'injection se fait ici, jamais par import croisé
- [ ] T090 [US7] Écrire `scripts/portes/reparcours-suspension.sh` : lance `uv run pytest tests/module_dore -q -p no:cacheprovider` une fois normalement et une fois avec `NELO_TEST_SUSPENSION=1` (la fixture de `tests/conftest.py` pose alors `assistance.suspendue=true` au tenant de test par `PUT /parametres` avant la suite) ; compare le nombre de tests passés — **identique** ou échec ; sortie `REPARCOURS SOUS SUSPENSION : N tests, résultat identique` ; ajouter en **dernière** étape de `scripts/verifier.sh`

**Point de contrôle** : SC-008 — assistance suspendue, la suite du module doré passe à cent pour cent et l'interface répond « suspendue » à chaque capacité ; US7-4 — aucun service d'assistance nulle part.

---

## Phase 10 : Finition et transverse

**But** : le guide de démarrage est vrai, le corpus dit que le code existe, les chiffres des
critères de succès sont notés, la définition de terminé est relue.

- [ ] T091 Dérouler [quickstart.md](quickstart.md) de bout en bout sur un clone frais dans le bac à sable (`git clone` local, `docker compose up -d`, `uv sync`, `pnpm install --frozen-lockfile`, `scripts/bd-vierge.sh --avec-jeu-d-essai`, chaque `curl` et chaque `pytest`) ; chronométrer jusqu'à la première réponse du module doré (SC-001 < 5 min) ; corriger dans `specs/001-socle-serveur/quickstart.md` toute commande ou sortie attendue qui diverge
- [ ] T092 [P] Mettre à jour `docs/01-stack.md § 2.1` « Ce qui existe aujourd'hui » (l'arborescence réelle après T0a, plus « Rien d'autre. Aucun code ») et `README.md` (les cinq commandes de démarrage et les deux commandes de vérification)
- [ ] T093 [P] Mesurer et noter : durée de `scripts/verifier.sh` (SC-010), durée de `scripts/tests-negatifs.sh`, nombre de fonctions d'accès inspectées par P-12, nombre de modules inspectés par P-04 — dans l'entrée de session de `docs/progress.md`
- [ ] T094 Relire la définition de terminé de `docs/01-stack.md § 8.3` point par point contre la tranche (les points 6, 7, 8, 10 sont sans objet : aucun écran, aucun document) et cocher le résultat dans `docs/progress.md` ; mettre à jour la ligne « Code existant » et « Tranche en cours » de l'état courant ; « Prochaine » = T0b
- [ ] T095 `uv run ruff check . && uv run ruff format .` puis `scripts/verifier.sh` une dernière fois ; commiter sur `001-socle-serveur` ; **ne pas fusionner dans `main`** — la fusion est le geste de l'utilisateur, après relecture

---

## Dépendances et ordre d'exécution

### Dépendances entre phases

- **Mise en place (Phase 1)** : aucune dépendance — commence immédiatement
- **Fondations (Phase 2)** : dépend de la Phase 1 — **bloque toutes les stories**
- **Stories (Phases 3 à 9)** : dépendent toutes de la Phase 2
  - **US1** d'abord : c'est le critère de fin, et US3 comme US7 s'appuient sur son écriture
  - **US2**, **US4**, **US6** sont indépendantes entre elles et d'US1 (elles ne partagent que les fondations)
  - **US3** dépend d'US1 (rejeu d'une écriture du module doré)
  - **US5** dépend de la matière des autres portes : P-01 (US2), P-03 (US1), P-04 et P-11 (US4) doivent exister pour que la chaîne et les tests négatifs soient complets ; P-02, P-07, P-12 naissent en US5
  - **US7** dépend d'US1 (la suspension se pose par `PUT /parametres`) et d'US6 (l'abstraction d'inférence)
- **Finition (Phase 10)** : dépend de toutes les stories retenues

### Dépendances entre stories

| Story | Peut commencer après | Note |
|---|---|---|
| US1 | Phase 2 | aucune dépendance de story |
| US2 | Phase 2 | indépendante ; testable seule avec `tests/isolation` |
| US3 | US1 | rejoue `PUT /parametres` |
| US4 | Phase 2 | indépendante ; testable seule avec `tests/frontieres` |
| US5 | US1, US2, US4 | assemble les portes ; P-02, P-07, P-12 lui appartiennent |
| US6 | Phase 2 | indépendante ; testable seule avec `tests/simulations` |
| US7 | US1, US6 | reparcours en fin de `verifier.sh` |

### À l'intérieur d'une story

- Les tests s'écrivent d'abord et **échouent** avant l'implémentation
- `tables.py` / `schemas.py` avant `acces.py`, `acces.py` avant `service.py`, `service.py` avant la route
- Le script de porte s'écrit avec la matière qu'il vérifie, son test négatif avec lui
- `scripts/verifier.sh` reste vert à chaque commit — une porte s'ajoute quand elle passe

### Possibilités de parallélisme

- Phase 1 : T003, T005, T006, T007, T008, T010 ensemble après T001–T002
- Phase 2 : T012, T013 avec T011 ; T017 avec T016 ; T027 avec T026
- Chaque story : tous ses tests `[P]` ensemble, puis l'implémentation dans l'ordre
- Après la Phase 2 : **US1, US2, US4, US6 en parallèle** (fichiers disjoints) ; US3 et US7 attendent US1 ; US5 attend US1, US2, US4
- Phase 6 : T081, T082, T083 ensemble ; Phase 5 : T053–T056 ensemble

---

## Exemple de parallélisme : User Story 1

```bash
# Les sept tests d'US1, ensemble — ils doivent tous échouer :
Tâche : "tests/module_dore/test_sante.py"
Tâche : "tests/module_dore/test_lecture.py"
Tâche : "tests/module_dore/test_ecriture.py"
Tâche : "tests/module_dore/test_refus_schema.py"
Tâche : "tests/module_dore/test_refus_metier.py"
Tâche : "tests/module_dore/test_point_insertion.py"
Tâche : "tests/portes/test_contrat_attendu.py"

# Puis, en séquence : schemas.py → acces.py → service.py → __init__.py → routes → contrat.py → P-03
# En parallèle de la séquence : api/routes/sante.py, scripts/portes/negatifs/p-03.sh
```

## Exemple de parallélisme : après les fondations

```bash
# Quatre stories sur des fichiers disjoints :
US1 : modules/socle/tenants/*, api/routes/*, api/contrat.py, contrat/
US2 : tests/isolation/*, scripts/portes/p-01.sh
US4 : modules/metier/protection/*, tests/frontieres/*, scripts/portes/p-04.sh, p-11.sh, [tool.importlinter]
US6 : modules/socle/communication/*, modules/metier/finance/*, modules/socle/assistance/service_inference.py, tests/simulations/*
```

---

## Stratégie d'implémentation

### D'abord le MVP — User Story 1 seule

1. Phase 1 : mise en place
2. Phase 2 : fondations (**bloquant**)
3. Phase 3 : US1
4. **S'ARRÊTER et VALIDER** : le module doré répond, le client typé se régénère sans écart, `verifier.sh` = ruff + P-03 vert — c'est le critère de fin nommé par la roadmap

### Livraison incrémentale

1. Mise en place + fondations → le serveur démarre
2. US1 → le patron existe (MVP)
3. US2 → l'isolation est prouvée, P-01 dans la chaîne
4. US3 → rien ne se perd
5. US4 → les frontières tiennent, P-04 et P-11 dans la chaîne
6. US5 → la commande complète, les sept tests négatifs
7. US6 → les simulations
8. US7 → l'assistance, le reparcours en fin de chaîne
9. Finition → le corpus dit que le code existe

### Un développeur seul — l'ordre recommandé

Phase 1 → Phase 2 → US1 → US2 → US4 → US5 (avec P-02, P-07, P-12) → US3 → US6 → US7 → Finition.
Cet ordre met la chaîne de vérification complète en place le plus tôt possible, pour que les trois
dernières stories se construisent déjà sous les sept portes.

---

## Notes

- **95 tâches** — Phase 1 : 10 · Phase 2 : 18 · US1 : 17 · US2 : 7 · US3 : 8 · US4 : 8 · US5 : 7 · US6 : 9 · US7 : 6 · Finition : 5
- `[P]` = fichiers différents, aucune dépendance sur une tâche inachevée
- Chaque tâche de test doit **échouer** avant l'implémentation qu'elle précède
- Commiter après chaque tâche ou groupe logique, sur `001-socle-serveur`
- Ce qui n'est **pas** dans cette liste, et ne doit pas y entrer : une classe de base, un dépôt générique, une capacité d'assistance, une route hors des trois du contrat, une quatrième fonction `SECURITY DEFINER`, un service dans `compose.yml`, un serveur d'intégration continue
