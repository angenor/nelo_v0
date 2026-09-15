# Démarrage rapide et validation — T0a, le socle serveur

Ce guide prouve la tranche de bout en bout, user story par user story. Il ne contient aucun
corps d'implémentation : les formes sont dans [contracts/](contracts/), le modèle dans
[data-model.md](data-model.md), les décisions dans [research.md](research.md).

## Prérequis sur le poste

| Outil | Version constatée le 2026-09-10 | Rôle |
|---|---|---|
| Docker Desktop, Compose v2 | 29.1.3 / v2.40.3 | les trois services |
| `uv` | 0.10.12 | Python 3.14, dépendances, `uv.lock` — `uv run fastapi dev` vient de `fastapi-cli`, épinglé en dépendance de développement |
| `pnpm` | 10.26.2 | `openapi-typescript`, `pnpm-lock.yaml` |
| `git` | — | les tests négatifs travaillent dans des `worktree` |

Aucun compte, aucune clé d'API, aucun service distant (FR-002). `psql` est utile pour regarder,
jamais requis : les scripts passent par `docker compose exec postgres psql`.

## Démarrer — US1, scénario 1

```bash
docker compose up -d                    # postgres, valkey, garage — trois services, pas un de plus
uv sync                                 # Python 3.14 + dépendances épinglées
pnpm install --frozen-lockfile          # openapi-typescript, épinglé
scripts/bd-vierge.sh                    # recrée la base logique, les deux rôles, applique migrations/tenants
uv run fastapi dev api/main.py          # :8000 — /api/v1/sante, /openapi.json
```

Attendu : `docker compose ps` liste exactement `postgres`, `valkey`, `garage` ; le serveur démarre
et son journal annonce le travailleur d'événements ; `curl -s localhost:8000/api/v1/sante` rend
`{"etat":"OK"}` sans en-tête (US1-7).

**Jeu de données de départ** : `scripts/bd-vierge.sh --avec-jeu-d-essai` crée deux tenants, A et B,
avec un établissement chacun, et imprime leurs identifiants en forme `export` — d'où
`eval "$(scripts/bd-vierge.sh --avec-jeu-d-essai | tail -1)"` pour avoir `ETAB_A` et `ETAB_B`.

**Ports déjà pris sur le poste** : copier `.env.exemple` en `.env` et changer ensemble les
`NELO_PORT_*` et les URL. La composition, la configuration et les scripts lisent tous `.env`.

Mesuré le 2026-09-15 sur un clone frais, services déjà téléchargés : **14 s** du `git clone` à la
première réponse du module doré (SC-001).

## Lire et poser — US1, scénarios 2 à 5

```bash
# Lecture : chaque clé du catalogue, valeur effective, portée résolue
curl -s localhost:8000/api/v1/parametres -H "X-Nelo-Etablissement: $ETAB_A" | jq .

# Écriture : poser assistance.suspendue à l'établissement — clé du catalogue, 02-domaine.md § 17
REQ=$(uv run python -c "import uuid; print(uuid.uuid7())")
curl -s -X PUT localhost:8000/api/v1/parametres/assistance.suspendue \
  -H "X-Nelo-Etablissement: $ETAB_A" -H "X-Nelo-Requete: $REQ" \
  -H "Content-Type: application/json" \
  -d "{\"portee\":\"ETABLISSEMENT\",\"portee_id\":\"$ETAB_A\",\"valeur\":true}" | jq .
```

Attendu : la lecture rend dix-sept entrées, `source` à `DEFAUT` pour les clés à défaut littéral,
`NON_DEFINIE` pour `sms.plafond_mensuel` et les clés du country pack ; l'écriture rend `200` avec
`ParametrePose` ; la relecture montre `assistance.suspendue` à `true`, `source: VALEUR`,
`portee_resolue: ETABLISSEMENT` ; la table `tenants.evenement_outbox` porte un événement
`tenants.parametre.pose` écrit **dans la même transaction** (le test le prouve en faisant échouer la
transaction : zéro événement, US3-4).

**Refus de schéma, deux champs** (US1-4) — corps `{"portee":"NULLE_PART","valeur":true}` avec une
**nouvelle** clé `X-Nelo-Requete` (réutiliser `$REQ` avec un autre corps rend
`409 REQUETE_REJOUEE_DIFFEREMMENT`, et c'est voulu) : `422`, `code: VAL_SCHEMA_INVALIDE`,
`details.champs` cite `portee` **et** `portee_id`, `requete_id` reprend la clé envoyée.

**Refus métier** (US1-5) — clé `inconnue.cle` : `422 TEN_PARAMETRE_INCONNU`, `details.cles_connues` ;
portée `SITE` : `422 TEN_PORTEE_INVALIDE`, `details.portees_disponibles`. Même statut que le
refus de schéma, **code différent** — c'est ce que le test vérifie.

## Régénérer le contrat — US1, scénario 6

```bash
scripts/portes/p-03.sh        # écrit contrat/openapi.json, dérive contrat/client.d.ts, git diff --exit-code
```

Attendu : « PORTE P-03 : 2 fichiers régénérés, 0 ligne d'écart ». `contrat/openapi.json` contient
la réponse `422` avec `EnveloppeErreur` sur `PUT /parametres/{cle}` (SC-007), et les deux en-têtes
de middleware comme paramètres requis.

## Deux tenants ne se voient jamais — US2

```bash
uv run pytest tests/isolation -q
```

Attendu, quatre tests verts : A ne voit aucune valeur de B ; une ressource de B demandée avec
l'en-tête de A répond `404 TEN_RESSOURCE_INTROUVABLE`, jamais `403` ; une transaction sans variable
voit **zéro** ligne sur **chaque** table du schéma et toute écriture est refusée ; A puis B sur la
**même connexion** du pool (pool limité à une connexion pour le test) : rien ne traverse.
`scripts/portes/p-01.sh` échoue en nommant la table si une politique manque (US2-5).

## Rejeu et événements — US3

```bash
uv run pytest tests/idempotence tests/outbox -q
```

Attendu : rejeu identique → réponse identique octet pour octet, **une** valeur, **un** événement
(SC-005) ; rejeu avec un autre corps → `409 REQUETE_REJOUEE_DIFFEREMMENT` ; sans en-tête →
`400 REQUETE_CLE_MANQUANTE` ; UUID v4 → `400 REQUETE_CLE_INVALIDE` ; un consommateur qui lève laisse
l'événement `en_echec` puis `en_attente`, jamais perdu ; le travailleur arrêté puis relancé consomme
dans l'ordre d'écriture par tenant.

## Les frontières tiennent — US4

```bash
scripts/portes/p-04.sh && scripts/portes/p-11.sh
```

Attendu : « PORTE P-04 : N modules inspectés, 0 arête interdite » et « PORTE P-11 : 3 verrous,
N modules, 0 chaîne suspecte ». Les mutations de `scripts/portes/negatifs/` font échouer chacune en
nommant l'arête, le verrou ou le fichier.

## Une seule commande — US5

```bash
scripts/verifier.sh          # ruff, P-02, P-07, P-04, P-11, P-01, P-12, P-03, reparcours sous suspension
                             # (P-01 travaille sur la base « nelo_verification », les tests sur « nelo_test »)
scripts/tests-negatifs.sh    # sept portes cassées une à une, sept échecs attendus, dépôt intact
```

Attendu : `verifier.sh` vert en moins de trois minutes (SC-010) ; `tests-negatifs.sh` annonce
« 7 portes cassées, 7 échecs obtenus, dépôt intact » et `git status --porcelain` est identique
avant et après (SC-003). Retirer une fonction de `acces.py` du jeu de tests fait échouer P-12 **en
la nommant** (SC-006).

## Les dépendances externes simulées — US6

```bash
uv run pytest tests/simulations -q        # les cinq modes de chaque abstraction, par paramétrage du test
```

En exécution, les modes viennent de la configuration — `NELO_SIMULATION_SMS_MODE`,
`NELO_SIMULATION_PAIEMENT_MODE`, `NELO_SIMULATION_INFERENCE_MODE`, et `NELO_SIMULATION_DELAI_MS`
commun aux trois — sans modifier le code.

Attendu : chaque abstraction, dans chacun des cinq modes, se comporte comme le tableau de
[contracts/interfaces-python.md](contracts/interfaces-python.md) ; en `JAMAIS_RECU` l'appelant rend
la main à `delai_max` ; en `INDISPONIBLE` une route de test qui en dépend répond
`503 API_DEPENDANCE_INDISPONIBLE` avec l'enveloppe. `grep -c inference compose.yml` rend `0`
(US6-5).

## L'assistance a sa place — US7

```bash
uv run pytest tests/assistance -q
```

Attendu : appeler l'une des six capacités lève `CapaciteNonLivree` ; suspension posée par
`PUT /parametres/assistance.suspendue`, `etat_des_capacites` rend `SUSPENDUE` pour les six et
`appeler` lève `AssistanceSuspendue` ; posée au tenant, elle vaut pour chaque établissement ; posée
à un établissement, elle ne vaut que là. La dernière étape de `scripts/verifier.sh` pose la
suspension et reparcourt la suite du module doré : même résultat (SC-008). `compose.yml` et
l'espace de travail ne contiennent aucun service d'assistance.

## Tout éteindre

```bash
docker compose down -v      # la base est éphémère et recréable à volonté
```
