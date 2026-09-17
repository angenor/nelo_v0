# 01 — Cadrage technique

*Structure du dépôt, commandes, hiérarchie des paquets, portes de vérification.*

---

## 1. Les choix, en une page

| Couche | Choix | Motif |
|---|---|---|
| **Interface** | **Nuxt 4**, mobile-first et responsive | Une seule base de code pour le back-office, le portail parent et le portail élève. La surface se compose à partir des capacités, pas des rôles |
| **Serveur** | **FastAPI + Pydantic** (Python), monolithe modulaire | **La validation est à l'exécution** : un poste d'établissement qui n'a pas été mis à jour depuis six mois se fait refuser par le schéma, pas par une vérification oubliée |
| **Base** | **PostgreSQL 18** | Un schéma par module, Row Level Security forcée pour l'isolation tenant |
| **Migrations** | **Alembic, un dossier par module** | Jamais de migration transverse : un module qui migre le schéma d'un autre a déjà cessé d'être extractible |
| **Éphémère** | **Valkey** | Sessions, verrous, limitation de débit, ordonnancement. Licence BSD sans ambiguïté |
| **Fichiers** | **Garage** (API S3) | Auto-hébergeable, faible empreinte, réplication géographique — cohérent avec un hébergement régional. Interface S3 standard, donc migration possible sans réécriture |
| **Accès données** | **SQLAlchemy Core + `asyncpg`** — jamais l'ORM | Pas d'ORM. Le SQL est écrit, pas deviné. Ce que la compilation vérifiait, la porte **P-12** le vérifie contre une base réelle |
| **Outillage Python** | **`uv`** (lockfile `uv.lock`), **`ruff`**, **`pytest`** | Un outil pour l'environnement et les dépendances, un pour le style et l'analyse, un pour les tests |
| **Style** | **Tailwind 4** + le thème du design system | Les jetons sont dans `docs/design/theme.css`, copié tel quel |
| **Contrat** | **OpenAPI**, généré par FastAPI depuis les schémas Pydantic, servi sur `/openapi.json` | Source de vérité à l'exécution ; le client TypeScript en est dérivé, jamais écrit à la main |
| **Bus** | **Aucun** — table `outbox` + worker in-process | En monolithe mono-processus, une table Postgres suffit et coûte bien moins cher à opérer |
| **Supervision** | **OpenTelemetry** | Instrumentation neutre : le choix du collecteur reste ouvert et changeable sans retoucher le code |
| **Environnement** | **Docker Compose en local**, VPS ensuite | Le passage en production est un changement de configuration, jamais une réécriture |
| **Méthode** | **GitHub Spec Kit** | Une tranche de la roadmap = un prompt `/speckit-specify` prêt à l'emploi |

**Règle de version** : la dernière version stable de chaque brique, sauf conflit constaté. Épinglée
exactement, jamais en intervalle, figée par lockfile commité.

### 1.1 Pourquoi FastAPI en façade, et ce que ça coûte

Le serveur porte la totalité de la logique métier et de l'API en **FastAPI**, avec **Pydantic** comme
frontière d'entrée et de sortie. Trois raisons, dont deux tiennent au produit et une au portefeuille :

| Raison | Ce qu'elle vaut ici |
|---|---|
| **La validation est à l'exécution** | Un type disparu à la compilation ne refuse rien ; un modèle Pydantic refuse la requête. Sur des postes d'établissement mis à jour rarement, c'est la différence entre une erreur propre et une donnée corrompue |
| **L'assistance cesse d'être un service** | C1 et C5 vivent dans `modules/socle/assistance/`, appelées comme n'importe quel autre paquet. **Un service de moins à déployer, à superviser et à arrêter** |
| **Une seule langue de serveur** | Les quatre projets du portefeuille partagent un jeu d'habitudes de test, de mise en production et de dépendances. Pour un développeur seul, c'est du temps qui ne se dépense pas deux fois |

**L'assistance reste désactivable, et c'est toujours un test** — non plus par l'arrêt d'un conteneur,
mais par un **réglage serveur** du catalogue de paramètres (§ 3).

> ⚠️ **Ce que l'argument Rust avait de juste ne disparaît pas.** L'empreinte mémoire est plus lourde et
> la latence par requête plus élevée qu'avec Actix, sur des serveurs contraints et à prix de vente en
> francs CFA. Trois autres pertes sont nommées — la vérification SQL à la compilation, la hiérarchie de
> paquets garantie par le compilateur, et le cloisonnement de `protection` — dans
> [ADR 017](adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md). Elles sont payées, pas ignorées.

### 1.2 La stratégie de rendu Nuxt

Le front-end est entièrement découplé ; le monolithe n'expose que des API. Reste à décider **quoi
rendre où**, et le critère est le poids et le temps de premier affichage :

| Surface | Rendu | Motif |
|---|---|---|
| **Site public** | Statique | Référencement, poids minimal, aucune donnée |
| **Portail parent, portail élève** | **Rendu serveur** | Premier affichage rapide sur connexion lente et appareil d'entrée de gamme. C'est la surface la plus exposée à la contrainte réseau |
| **Back-office** | **Rendu serveur par défaut** ; rendu client écran par écran, par règle de route, quand la mesure P-10 le permet | La coquille et les écrans de saisie en classe portent le budget le plus serré : à 400 kbit/s, 120 Ko font 2,4 s de transfert, et un rendu client ne peint rien avant de les avoir reçus. Un écran de poste à session longue peut passer en rendu client, écran par écran, sur mesure ([T0b, research R-06](../specs/002-socle-interface/research.md)) |

> **Tranchée le 2026-09-17 par le plan de T0b** (Q4 du journal). L'hypothèse d'origine classait le
> back-office en rendu client ; la mesure l'a contredite pour la coquille et l'écran d'appel, qui
> sont du back-office et portent le plafond le plus serré. Le critère reste le poids et le premier
> affichage : chaque écran peut changer de mode par règle de route, sur mesure, jamais par principe.

---

## 2. Le dépôt

### 2.1 Ce qui existe aujourd'hui

Le socle serveur de **T0a** ([specs/001-socle-serveur/](../specs/001-socle-serveur/)) :

```
nelo_v0/
├── CLAUDE.md · README.md · .gitignore · .env.exemple
├── pyproject.toml · uv.lock · .python-version       # espace de travail uv : racine installable, huit membres déclaratifs
├── package.json · pnpm-lock.yaml · pnpm-workspace.yaml   # openapi-typescript épinglé ; web/ viendra avec T0b
├── compose.yml · garage.toml # postgres, valkey, garage — trois services
├── contrat/                  # openapi.json et client.d.ts, régénérés par P-03
├── api/                      # composition : main, middlewares (établissement provisoire, idempotence),
│                             #   erreurs, capacités (point d'insertion), travailleur, contrat, routes/
├── modules/
│   ├── domaine/              # vide — la base de la hiérarchie
│   ├── shared/               # transaction(tenant_id), erreurs, modes de simulation, événement
│   ├── socle/
│   │   ├── tenants/          # LE MODULE DORÉ — catalogue de paramètres, outbox du schéma
│   │   ├── assistance/       # six capacités, aucune livrée ; service d'inférence simulé
│   │   └── communication/    # passerelle SMS simulée
│   ├── metier/
│   │   ├── finance/          # agrégateur de paiement simulé
│   │   └── protection/       # CLOISONNÉ — l'interface de service, rien d'autre
│   └── segments/             # vide
├── migrations/tenants/       # Alembic : le schéma tenants, réversible
├── scripts/                  # verifier.sh, tests-negatifs.sh, bd-vierge.sh, portes/
├── tests/                    # module doré, isolation, idempotence, outbox, frontières, simulations, assistance
├── .specify/ · .claude/skills/   # Spec Kit — voir 2.2
├── specs/                    # une spécification par tranche
└── docs/                     # ce corpus
```

**Aucune interface, aucune règle métier pédagogique.** Sept portes serveur tiennent — P-01, P-02,
P-03, P-04, P-07, P-11, P-12 — et chacune a son test négatif (`scripts/tests-negatifs.sh`).

### 2.2 Spec Kit — ce qui est posé

Le projet se développe avec **GitHub Spec Kit**, installé en **v0.16.5**.

Le CLI se met à jour hors du dépôt, avec `uv` :

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.16.5 --force
```

L'initialisation, faite une fois dans le dépôt existant :

```bash
specify init --here --force --non-interactive --script sh --integration claude
```

`--here` initialise dans le dossier courant, `--force` passe la confirmation puisqu'il n'est pas vide,
`--script sh` choisit les scripts bash, et `--integration claude` installe les skills pour Claude Code.

**Ce que l'initialisation a ajouté**, et rien de plus :

```
nelo_v0/
├── .specify/
│   ├── memory/constitution.md      # ← à écrire, voir 04-roadmap.md « Étape 0 »
│   ├── templates/                  # gabarits de spec, plan, tâches, liste de contrôle
│   ├── scripts/bash/               # création de branche, prérequis, contexte
│   ├── workflows/speckit/          # le cycle complet en une passe (workflow.yml)
│   ├── integration.json            # intégration retenue, séparateur d'invocation
│   └── init-options.json           # les options figées de l'init
├── .claude/skills/                 # speckit-constitution, speckit-specify,
│                                   #   speckit-plan, speckit-tasks, speckit-implement,
│                                   #   speckit-clarify, speckit-analyze, speckit-checklist,
│                                   #   speckit-converge, speckit-taskstoissues
└── specs/                          # une spécification par tranche, créée par speckit-specify
```

`specs/` n'existe pas encore : la première tranche spécifiée le crée.

> ⚠️ **Depuis la 0.16, Spec Kit livre des *skills*, plus des commandes.** Elles vivent dans
> `.claude/skills/`, pas dans `.claude/commands/`, et **le séparateur est un tiret** :
> `/speckit-specify`, jamais `/speckit.specify`.

> ⚠️ **La constitution arrive vide.** C'est le fichier que chaque `plan` vérifie : tant qu'il porte
> les jetons du gabarit, aucune tranche ne peut être contrôlée contre quoi que ce soit. **L'écrire
> est l'étape zéro** — le prompt est en tête de [04-roadmap.md](04-roadmap.md#étape-0--la-constitution).

**Ce que le dépôt ignore** : `.specify/.gitignore` écarte l'état par machine (`feature.json`), et le
`.gitignore` racine écarte `.claude/settings.local.json` et `.claude/.credentials.json`. Les skills et
les gabarits, eux, se commitent — c'est la méthode partagée.

### 2.3 La cible — le dépôt une fois toutes les tranches livrées

```
nelo_v0/
├── CLAUDE.md · compose.yml · docs/ · .specify/ · specs/ · scripts/
├── pyproject.toml · uv.lock · package.json · pnpm-lock.yaml   # les espaces de travail, à la racine
├── contrat/                  # openapi.json écrit par le serveur, client.d.ts dérivé — commités, régénérés par P-03
├── web/                      # Nuxt 4 — app/ : components/ composables/ core/ pages/ assets/
├── api/                      # FastAPI — composition des modules, routes fines
├── modules/
│   ├── domaine/              # types métier, INTERPRÉTEUR DE FORMULES — aucune E/S, aucun pays
│   ├── socle/
│   │   ├── tenants/  personnes/  habilitations/  annees/
│   │   ├── communication/  documents/  assistance/   # C1 rédaction, C5 extraction
│   │   └── pilotage/  editeur/
│   ├── metier/
│   │   ├── structure/  scolarite/  evaluation/
│   │   ├── vie_scolaire/  conseil/  finance/
│   │   └── protection/       # CLOISONNÉ — aucun paquet ne l'importe
│   ├── segments/             # spécialisations par segment d'établissement
│   │   └── primaire/         # le seul livré au MVP — ADR 018
│   └── shared/               # schémas Pydantic d'échange, bus d'événements, erreurs
└── migrations/<module>/      # Alembic, un dossier par module
```

**Pourquoi la famille métier s'appelle `metier/` et non `modules/`** : elle vit désormais **dans**
`modules/`. `modules/modules/` serait un chemin que personne ne relit deux fois de la même façon.

**Pourquoi `assistance` est dans le socle et non dans `metier/`** : les deux capacités du MVP servent
plusieurs modules — l'appréciation vient de `evaluation`, l'extraction de colonnes de l'import. Un
paquet que plusieurs modules appellent appartient au socle, sinon la hiérarchie s'inverse.

**Pourquoi `evaluation` est un module et l'interpréteur de formules est dans `domaine`** : le calcul
d'une moyenne est une opération pure, sans E/S, testable sur un jeu de formules et de notes en
mémoire. Le module `evaluation` lit, écrit et orchestre ; il n'arbitre aucun barème.

**Pourquoi `segments/` existe avant d'avoir plus d'un segment** : le préscolaire et le secondaire
général arrivent en V2, le technique et le supérieur en V3
([ADR 018](adr/018-le-mvp-commence-par-le-primaire.md)). S'ils s'ajoutent dans `metier/`, ils
spécialisent le noyau ; s'ils ont leur famille dès le départ, ils s'ajoutent. Le répertoire coûte zéro
ligne aujourd'hui.

### 2.4 La hiérarchie de dépendance des paquets — non négociable

| Famille | Peut importer |
|---|---|
| `domaine/` | **rien** |
| `shared/` | **rien** — schémas d'échange, bus d'événements, erreurs |
| `socle/` | `domaine/`, `shared/`, `socle/` |
| `metier/` | `domaine/`, `shared/`, `socle/`, `metier/` — **sauf `protection`** |
| `segments/` | `domaine/`, `shared/`, `socle/`, `metier/` |
| `api/` | tout — **et ne porte aucune règle métier** |

Trois corollaires, chacun avec son test structurel :

1. **Aucun paquet de `socle/` n'importe un paquet de `metier/`** (porte P-04). C'est ce qui garde le
   socle ouvert au préscolaire comme au supérieur. **En Rust, cargo le donnait gratuitement ; ici,
   c'est un test de graphe d'imports, à écrire et à maintenir.**
2. **Aucun paquet n'importe `modules/metier/protection/`** (porte P-11). Le cloisonnement n'est pas
   une convention d'accès : c'est une **frontière d'import, tenue par trois verrous** (§ 7.4). Un
   compilateur refusait, un test signale — **c'est plus faible, et c'est écrit.** Un module qui
   pourrait lire un signalement finirait par le lire.
3. **`domaine/` ne contient aucune littérale de pays** — ni `CI`, ni `XOF`, ni `20`, ni `trimestre`,
   ni `BEPC` (porte P-09).

**Corollaire de vocabulaire** : le socle ne connaît ni « classe », ni « bulletin », ni « trimestre ».
Il connaît `annee_scolaire`, `perimetre`, `capacite` et `envoi`. Les notions pédagogiques vivent dans
`metier/`.

### 2.5 Les frontières internes

« Monolithe modulaire » signifie exactement ceci :

1. **Un schéma Postgres par module.** Aucune requête ne joint deux schémas de modules différents, et
   **aucune clé étrangère ne traverse un schéma de module** (porte P-01). Les lectures inter-modules
   passent par l'interface publique du module propriétaire : `finance` ne fait pas de `SELECT` dans
   `scolarite.eleve`, il appelle l'interface du module `scolarite`.
2. **Toute transition d'état métier écrit un événement outbox dans la même transaction SQL** —
   dans la table `evenement_outbox` **du schéma du module**, puisqu'aucune transaction ne traverse
   deux modules ; le travailleur consomme chaque table, par tenant, dans l'ordre d'écriture.
3. **Aucune transaction SQL ne couvre deux modules.** Les opérations inter-modules sont des séquences
   avec compensation explicite.
4. **Chaque paquet expose son interface de service dans son `__init__.py`**, et rien d'autre n'en
   sort ; les dépendances sont injectées.

> **C'est la seule condition qui rend l'extraction future d'un service indolore.** Un module qui écrit
> dans le schéma d'un autre la rend impossible, quelle que soit la propreté des interfaces —
> [ADR 003](adr/003-monolithe-modulaire-microservices-plus-tard.md).

Aucun service n'est extrait. Aucune file de messages n'est introduite : l'outbox est consommé par un
worker in-process.

---

## 3. L'environnement local — tout tourne sur le poste

`compose.yml` décrit trois services et rien d'autre. **Aucun service tiers distant n'est requis pour
développer**, et c'est une propriété qu'on défend : une démonstration dans un établissement d'Abidjan
ne peut pas dépendre du réseau.

```
docker compose up -d          # postgres + valkey + garage
uv run fastapi dev api/main.py  # depuis la racine — l'API sur :8000, OpenAPI sur /openapi.json
pnpm --filter web dev         # l'application sur :3000, la page de style sur /style (développement seulement)
pnpm exec playwright install chromium webkit   # une fois, avec réseau : les deux moteurs de P-05 et P-10
```

| Service | Rôle en développement | En production |
|---|---|---|
| **postgres** | La base, éphémère et recréable à volonté | Même image, volume persistant, sauvegarde + PITR |
| **valkey** | Sessions, verrous, limitation de débit, ordonnancement de l'outbox | Identique |
| **garage** | Mono-nœud, `replication_mode = 1`, buckets créés au provisionnement | Même API S3, topologie différente |

**Le service d'inférence n'est pas un service du compose** : c'est une dépendance externe comme les
autres, derrière son interface, avec son implémentation simulée en mode par défaut.

**Les intégrations externes vivent derrière une interface, avec une implémentation simulée livrée en
même temps.** Agrégateur de paiement, passerelle SMS, WhatsApp Business, service d'inférence : la
simulation est le mode par défaut en local.

> ⚠️ **Une simulation doit savoir échouer aussi bien que réussir.** La passerelle SMS simulée doit
> pouvoir renvoyer un accusé en retard, en double, ou jamais — parce que c'est ce que fait la vraie.
> Un webhook de paiement qui n'arrive jamais est le cas nominal à concevoir, pas l'exception.

> ⚠️ **L'assistance désactivée est un test, pas une hypothèse.** Ce n'est plus un conteneur qu'on
> arrête, c'est un **paramètre du catalogue** posé à sa portée (`PUT /parametres/{clé}`) : suspendue,
> l'assistance laisse le produit **pleinement opérationnel** — les appréciations se saisissent à la
> main, l'import se fait par correspondance manuelle de colonnes — et **l'affordance n'apparaît pas à
> l'écran**, elle n'est pas grisée. La vérification pose le réglage et reparcourt les deux parcours
> concernés.

---

## 4. Le passage en production

Un VPS, la même image Docker, une configuration différente. Rien d'autre ne change.

| Sujet | Règle |
|---|---|
| **Hébergement** | **Régional à privilégier** — latence, et question de la localisation des données. Décision liée au conseil juridique local |
| **Migrations** | **Alembic, un dossier par module**, appliquées au démarrage, **réversibles**. Une migration appliquée n'est jamais modifiée |
| **Secrets** | Aucun secret dans le bundle applicatif. Le code servi au navigateur est lisible ; la règle ne se relâche jamais |
| **Clés d'agrégateur** | Coffre chiffré **par tenant**, dès la première tranche qui en manipule |
| **Sauvegardes** | Quotidiennes, chiffrées, externalisées + PITR. **Restauration réellement testée avant la bascule du pilote, puis chaque mois.** C'est le seul point où l'économie de moyens est interdite |
| **Export client** | Un export complet des données de l'établissement, dans un format ouvert, **disponible à tout moment** — c'est aussi l'argument de vente contre la peur de l'enfermement |
| **Observabilité** | OpenTelemetry : traces, métriques, journaux, corrélation par requête. Sonde `/sante` |
| **Pas de serveur dans l'école** | L'électricité et la sécurité physique rendent le on-premise ingérable à distance |

---

## 5. Sécurité — les fondamentaux

- **Row Level Security forcée** (`ENABLE` **et** `FORCE`) sur toutes les tables, avec un rôle
  applicatif distinct du propriétaire des tables.
- **`SET LOCAL app.current_tenant` posé dans chaque transaction**, jamais à l'ouverture de connexion.
  Avec un pool, c'est la différence entre l'isolation et la fuite.
- **Double barrière** : RLS **et** vérification applicative de la capacité et du périmètre. Aucune des
  deux n'est jamais la seule.
- **Aucune règle métier côté client.** Le client n'applique aucune formule de composition, ne convertit
  aucune note en mention, ne calcule aucun rang, aucun solde.
- **Chiffrement applicatif supplémentaire des catégories sensibles** — dossier médical, psychosocial,
  signalements, paie individuelle.
- **Journal d'audit inaltérable**, en insertion seule, sur les catégories sensibles au minimum.
- **Revue d'accès à chaque rentrée**, outillée par `/revue-acces`.
- **Test d'intrusion avant la mise en production d'un pilote payant.**

### 5.1 Session sur poste partagé

Les postes de l'administration sont partagés — secrétariat, salle des professeurs, économat. Trois
conséquences directes :

| Mécanisme | Ce qu'il garantit |
|---|---|
| **Jeton de rafraîchissement en cookie `HttpOnly`**, jamais en `localStorage` | Un jeton en stockage navigateur survit à la fermeture de session et se lit en JavaScript |
| **PIN pour les usages fréquents**, OTP par SMS pour l'ouverture | L'enseignant qui fait l'appel six fois par jour ne reçoit pas six SMS |
| **Révocation immédiate par liste consultée à chaque requête** | Le départ d'un enseignant coupe l'accès le jour même, pas à l'expiration du jeton |

> **Les comptes partagés sont interdits explicitement côté personnel** — le journal d'accès n'a aucun
> sens sinon. Ils sont tolérés côté famille, avec traçabilité : deux parents partageant un téléphone
> est le cas normal.

### 5.2 Données de mineurs

Le RGPD n'est pas le texte applicable. Pour la Côte d'Ivoire : loi n° 2013-450 du 19 juin 2013, avec
l'**ARTCI** comme autorité de contrôle, et le décret n° 2015-19 du 4 février 2015 pour les formalités
de déclaration et d'autorisation.

**Ce que le produit embarque**, sans attendre : registre des traitements exportable · base légale par
traitement · consentement horodaté du responsable légal · durée de conservation par catégorie, avec
purge automatique et archivage légal séparé · droits d'accès, rectification, opposition et
portabilité **outillés, pas manuels** · journal d'accès inaltérable · procédure et délai de
notification de violation.

> **L'utilisation de données d'élèves pour entraîner ou affiner un modèle est un traitement distinct**,
> qui exige sa propre base légale et son propre consentement. Aucune promesse du type « le système
> apprend de vos données » n'est faite tant que ce cadre n'est pas contractuellement établi.

---

## 6. Le contrat d'API

- Routes annotées, schémas Pydantic en entrée comme en sortie, **OpenAPI généré sur
  `/openapi.json`**, documentation interactive protégée hors développement.
- **Le client TypeScript est généré depuis la spec, jamais écrit à la main.** Un diff non commité fait
  échouer la vérification (porte P-03).
- **Le `422` de Pydantic est un citoyen de première classe du contrat**, pas une fuite
  d'implémentation — [03-api.md § 1.8](03-api.md#18-codes-http).
- Le contrat lui-même — conventions, enveloppe d'erreur, ressources — est dans
  [03-api.md](03-api.md), qui fait autorité au niveau projet.

---

## 7. La vérification — une seule commande

`scripts/verifier.sh` enchaîne tout ce qui doit passer et sort en échec au premier contrôle rouge.
Pas dix scripts qu'on lance de mémoire.

| Porte | Ce qu'elle vérifie |
|---|---|
| **P-01** | Les migrations Alembic s'appliquent sur une base vierge, **un dossier par module** ; chaque table porte `ENABLE` + `FORCE ROW LEVEL SECURITY` avec sa politique ; **aucune clé étrangère ne traverse un schéma de module** |
| **P-02** | Aucune dépendance en intervalle ; lockfiles commités — `uv.lock` et `pnpm-lock.yaml` |
| **P-03** | Le client TypeScript régénéré depuis OpenAPI ne produit aucun diff |
| **P-04** | **Aucun paquet de `socle/` n'importe un paquet de `metier/`** — test de graphe d'imports |
| **P-05** | L'application démarre et **chaque écran s'atteint**, en clair et en sombre, sur Chromium et sur WebKit |
| **P-06** | **Aucune littérale d'interface en dur** : chaîne visible, valeur de couleur hors du thème, appel direct d'une API de plateforme hors de l'interface unique, rôle ; et les clés `fr` et `en` existent toutes les deux. Cinq règles, un script, chaque échec nomme le fichier |
| **P-07** | Aucune dépendance sous licence copyleft fort (voir § 9) |
| **P-08** | **Les provisions d'extension tiennent** (voir § 7.1) |
| **P-09** | **Le pays ne fuit pas hors du country pack** (voir § 7.2) |
| **P-10** | **Le budget de poids par écran tient** (voir § 7.3) |
| **P-11** | **Le cloisonnement tient** (voir § 7.4) |
| **P-12** | **Toute requête SQL du produit s'exécute contre une base fraîchement migrée** (voir § 7.5) |

**Chaque porte a son test négatif** : on la casse volontairement une fois — retirer une politique,
ajouter une chaîne en dur — pour vérifier qu'elle échoue vraiment. *Une porte qui ne trouve jamais
rien est indistinguable d'une porte qui n'a rien à trouver.*

**Une porte s'ajoute quand une erreur réelle s'est produite**, ou quand son absence coûterait une
fuite entre clients — jamais parce qu'elle figurerait bien dans une liste. **P-12 est le troisième
motif, et le seul qu'on espère ne pas revoir** : une garantie mécanique a disparu, et une porte la
remplace. Trois portes relèvent désormais de ce motif — P-04, P-11 et P-12 — parce que le compilateur
Rust les tenait sans qu'on ait à les écrire
([ADR 017](adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md)).

### 7.1 P-08 — les provisions d'extension tiennent

Le modèle porte des colonnes et des référentiels qui ne servent à rien aujourd'hui et qui rendent les
extensions de [06-apres-mvp.md](06-apres-mvp.md) **additives plutôt que migratoires**. Elles ne coûtent
rien tant que personne ne les dégrade — et **personne ne les dégrade volontairement** : on écrit une
note en entier parce qu'un devoir se note sur 20 en nombres ronds, et on découvre trois ans plus tard
qu'il faut migrer toutes les notes du produit.

P-08 est mécanique. Elle ne demande aucun jugement :

| Contrôle | Ce qu'il empêche |
|---|---|
| Toute colonne de note et de coefficient est `NUMERIC` | Qu'une note de 14,25 devienne 14, et qu'une moyenne devienne indéfendable |
| Aucune colonne de montant n'est en virgule flottante | Des arrondis sur des sommes d'argent |
| Toute table pédagogique porte `annee_id` **`NOT NULL`** | Que les classes de N+1 écrasent celles de N, et qu'un bulletin archivé devienne faux |
| Toute occupation et toute absence est un intervalle `[début, fin)` | Qu'un appel par demi-journée et un appel par cours exigent deux modèles |
| Les colonnes de provision existent **et sont nullables** : `personne.email`, `eleve.nationalite`, `classe.site_id`, `evaluation.groupe_id`, `signalement.auteur_id`, `inscription.regime` | Que le multi-sites, le dédoublement, le signalement confidentiel ou l'internat deviennent des migrations |
| Chaque module déclaré non implémenté a **son test de refus explicite** | Qu'un module soit ignoré en silence au lieu d'être refusé |
| Chaque capacité IA non implémentée (C2, C3, C4, C6) a **son test de refus explicite** | Idem |
| Le paquet `editeur` ne référence ni `classe`, ni `note`, ni `bulletin` | Que la facturation soit calculée sur des bulletins, et qu'un centre de formation continue devienne infacturable |

**Son test négatif** : retirer une nullabilité, écrire une note en entier, ou faire lire une table de
notes au paquet `editeur`. La porte doit échouer dans les trois cas.

### 7.2 P-09 — le pays ne fuit pas hors du country pack

**C'est la porte qui décide de la viabilité de l'extension régionale.** Un `if pays == "CI"` ne se
retire pas : il se multiplie.

| Contrôle | Ce qu'il empêche |
|---|---|
| Aucune littérale `CI`, `XOF`, `BEPC`, `BAC`, `trimestre`, `SYSCOHADA`, `CNPS`, `ARTCI` dans `domaine/` ni `socle/` | Que la Côte d'Ivoire devienne une hypothèse du noyau |
| Aucune borne d'échelle de notation (`20`, `100`) en dur hors des tests | Que le passage au pourcentage anglophone soit une réécriture |
| Aucun découpage d'année (`3`, `2` périodes) en dur | Que les *three terms* exigent une migration |
| Le moteur de calcul est un **interpréteur**, pas une fonction par pays : aucune branche conditionnée par le pays dans `domaine/evaluation` | Que chaque nouveau pays devienne un déploiement |
| Le **test d'agnosticité** passe : un country pack fictif à échelle sur 10 et deux périodes fonctionne de bout en bout | Qu'une règle ivoirienne se soit glissée dans la logique sans qu'on le voie |

**Son test négatif** : ajouter `if pack.pays == "CI"` dans un paquet du socle. La porte doit échouer.

### 7.3 P-10 — le budget de poids par écran tient

Le poids n'est pas un détail de performance : **c'est l'indicateur d'adoption.** Un parent qui consomme
5 Mo pour consulter un bulletin n'y revient pas ; un enseignant dont l'écran d'appel met vingt secondes
à s'ouvrir retourne à sa feuille.

| Écran | Budget | Pourquoi ce chiffre |
|---|---|---|
| **Appel de séance** | **120 Ko** transférés, premier affichage utile < 2 s sur 3G lente | C'est l'écran qui décide de l'adoption |
| **Saisie de notes** | 200 Ko | Tablette, session longue, données paginées |
| **Portail parent** | 150 Ko par vue | Appareil d'entrée de gamme, forfait data compté |
| **Back-office** | 500 Ko au premier chargement | Session longue, coût amorti |

Le contrôle est mécanique : la vérification mesure le poids transféré de chaque écran budgété et
échoue au dépassement. **Un budget dépassé n'est pas une dette : c'est un refus de fusion.**

**Son test négatif** : ajouter une police ou une image de 300 Ko à l'écran d'appel.

### 7.4 P-11 — le cloisonnement tient

Le domaine où une erreur de conception a les conséquences les plus graves, humaines comme juridiques.
La porte n'a aucune tolérance.

**Et c'est ici que le changement de pile coûte le plus cher.** Le compilateur Rust *refusait* une
dépendance vers `protection` ; en Python, un `import` traversant s'exécute parfaitement. La garantie
devient une **frontière d'import** : **un compilateur refusait, un test signale.** C'est plus faible,
et c'est écrit plutôt que dissimulé. **Trois verrous** compensent, là où il n'en fallait qu'un :

| Verrou | Ce qu'il vérifie |
|---|---|
| **Déclaration** | Aucun paquet ne déclare `protection` dans ses dépendances |
| **Graphe d'imports** | Le test échoue si un `import` traversant vers `modules/metier/protection/` est introduit — **où qu'il soit**, y compris différé au fond d'une fonction |
| **Surface** | `modules/metier/protection/__init__.py` **n'expose rien** hors de son interface de service : ni entité, ni dépôt, ni session |

Et les contrôles qui, eux, ne dépendent d'aucun langage :

| Contrôle | Ce qu'il empêche |
|---|---|
| Toute capacité portant `cloisonnee = true` **échoue** si on tente de l'ajouter à un modèle de rôle | Qu'une capacité ajoutée à un rôle largement distribué ouvre le dossier psychosocial de tous les élèves |
| Toute route du bloc `PRO_` **écrit dans `journal_acces`**, y compris en lecture, y compris en cas de refus | Qu'un accès reste invisible |
| Aucune route de messagerie n'expose `DELETE` | Qu'un canal adulte-mineur devienne effaçable |
| Le test « le chef d'établissement ne lit pas un signalement le concernant » passe | La raison d'être de la couche |

**Son test négatif** : introduire un `import` vers `protection` — au niveau du module comme au fond
d'une fonction —, exporter un dépôt dans son `__init__.py`, ou ajouter une capacité cloisonnée dans un
modèle de rôle. La porte doit échouer dans les trois cas.

### 7.5 P-12 — toute requête SQL s'exécute contre une base fraîchement migrée

`sqlx` vérifiait chaque requête à la compilation, contre le schéma réel. **Python n'a aucun
équivalent** : une colonne renommée par une migration ne casse rien avant l'appel, et l'appel peut
n'arriver qu'en production, le jour de l'arrêté de caisse. P-12 est ce qui remplace la compilation.

| Contrôle | Ce qu'il empêche |
|---|---|
| **Toute fonction d'accès aux données est exercée au moins une fois** par la suite de tests, contre une base vierge migrée par Alembic | Qu'une table renommée se découvre en production |
| Aucune requête n'est construite par concaténation : SQLAlchemy Core compose, les valeurs sont liées | Une injection, et une requête qu'aucun test ne peut atteindre |
| Une fonction d'accès non exercée **échoue la porte**, elle ne baisse pas une couverture | Que la porte devienne déclarative |
| Le schéma migré est comparé au schéma attendu : colonne absente, type divergent, contrainte manquante | Qu'une migration oubliée passe la revue |

**Son test négatif** : renommer une colonne dans une migration sans toucher la requête qui la lit. La
porte doit échouer — **plus tard et plus lentement qu'une erreur de compilation, et c'est le prix
accepté** ([ADR 017](adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md)).

Le serveur d'intégration continue arrive quand le script local dépasse deux ou trois minutes et qu'on
cesse de le lancer. Il ne fera que lancer ce script, sans le modifier.

---

## 8. La méthode de travail

### 8.1 Spec Kit

**Étape zéro : écrire la constitution** (`/speckit-constitution`). C'est le fichier que chaque `plan`
vérifie ; tant qu'il est vide, rien n'est contrôlé. Le prompt est en tête de
[04-roadmap.md](04-roadmap.md#étape-0--la-constitution).

Ensuite, chaque tranche de [04-roadmap.md](04-roadmap.md) est rédigée comme un prompt
`/speckit-specify` prêt à coller. Le cycle est : `specify` → `plan` → `tasks` → `implement`.

Trois skills facultatives encadrent ce cycle quand une tranche est floue ou lourde :
`/speckit-clarify` avant `plan`, `/speckit-checklist` après `plan`, `/speckit-analyze` avant
`implement`. Deux autres existent et **ne servent pas ici** : `/speckit-taskstoissues` pousse les
tâches vers des issues GitHub, `/speckit-converge` recense l'écart entre le code et la spec — utile sur
du legacy, sans objet sur un dépôt qu'on écrit tranche par tranche.

> **Toute phase de planification lit [02-domaine.md](02-domaine.md) et [03-api.md](03-api.md) avant de
> produire un modèle ou un contrat local, et en dérive — jamais n'invente.** Un changement nécessaire
> se propose comme diff explicite sur le fichier projet, **avant** de continuer.

### 8.2 Le design, écran par écran

Une revue visuelle par tranche, en session dédiée, après `specify` et avant `plan`. Le gabarit du
prompt et la procédure de rangement sont en fin de [05-design.md](05-design.md).

### 8.3 La définition de terminé

1. Critères d'acceptation couverts par des tests, dont les transitions d'état.
2. Schémas Pydantic à jour, client TypeScript régénéré sans retouche manuelle.
3. Migration Alembic **dans le dossier du module**, **réversible**, appliquée sur base vierge, seeds à
   jour — et **toute requête neuve exercée par un test contre cette base** (P-12).
4. **RLS activée et forcée** sur toute nouvelle table, avec test d'isolation entre deux tenants.
5. Événement outbox émis pour tout changement d'état métier.
6. **Clés `fr` et `en` externalisées** ; aucune chaîne en dur, aucun libellé métier hors country pack.
7. **Écran vérifié en clair et en sombre, dans un navigateur réel**, Chromium et WebKit. Monter un
   composant dans un test ne prouve pas qu'une page s'atteint.
8. **Écran budgété : son poids est mesuré et sous le plafond** (P-10).
9. Tout paramètre qualifié de « paramétrable » est exposé dans le catalogue, jamais en dur.
10. Tout document imprimé vérifié à l'aperçu, au gabarit du country pack.
11. **Toute écriture porte sa clé d'idempotence, et le rejeu est testé.**
12. **Aucune provision d'extension dégradée** — P-08 passe. Quand la tranche touche une provision, on
    relit la porte avant de figer le modèle : une provision coûte zéro aujourd'hui et une migration
    demain.
13. **`scripts/verifier.sh` passe en une commande.**

---

## 9. Licences des dépendances

| Régime | Licences |
|---|---|
| **Autorisé** | MIT, Apache-2.0, BSD-2/3, ISC, Zlib, Unicode, MPL-2.0, **OFL 1.1** pour les polices ; BlueOak-1.0.0 et CC0-1.0, permissives, arrivées avec Nuxt ; CC-BY-4.0 pour `caniuse-lite` seul, donnée de construction qui ne voyage pas (T0b) |
| **Refusé** | GPL, AGPL, LGPL et tout copyleft fort — le produit est un logiciel propriétaire vendu par abonnement |
| **Contrôle** | Un vérificateur de licences côté Python et un côté npm, adossés aux lockfiles (porte P-07) |

**Ce que le produit redistribue appelle une attribution** : les polices servies au navigateur et les
icônes embarquées voyagent jusqu'au client. Leur avis de copyright et leur licence accompagnent les
fichiers, entrent dans le paquet distribué, et sont atteignables depuis un écran « À propos ». Une
bibliothèque de développement, elle, ne voyage pas — mais **une dépendance embarquée dans l'image
applicative livrée, si** : elle relève du même régime.

> ⚠️ **Les trois polices du design system sont aujourd'hui chargées depuis un service distant.** Elles
> doivent être servies localement avant la première mise en production : une dépendance réseau sur le
> chemin du premier affichage contredit le budget de poids, et le pilote est en Côte d'Ivoire.

---

## 10. Ce que la stack ne fait pas

| Absent | Pourquoi |
|---|---|
| Service worker avec cache d'écriture, IndexedDB, file de synchronisation, résolution de conflit | Le hors-connexion est **différé**, pas exclu → [ADR 001](adr/001-hors-connexion-differe.md). Les quatre fondations qui le rendront additif, elles, se posent maintenant |
| Capacitor, Tauri, chaîne de build native, magasins d'applications | **La PWA est la cible**, installable dès le MVP ; Capacitor (mobile) et Tauri (poste) l'empaqueteront plus tard, sans réécriture → [ADR 002](adr/002-web-d-abord-capacitor-plus-tard.md) |
| Serveur dans l'établissement | Électricité intermittente, sécurité physique, maintenance à distance impossible |
| Kubernetes, file de messages, microservices | Un seul processus, un seul VPS, un worker in-process → [ADR 003](adr/003-monolithe-modulaire-microservices-plus-tard.md) |
| ORM | SQLAlchemy **Core** et `asyncpg`. Le SQL est écrit, pas deviné — et P-12 le vérifie contre une base réelle |
| Un service d'inférence séparé | Les deux capacités du MVP sont un paquet du socle. **Un service de moins à opérer** → [ADR 017](adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md) |
| Reconnaissance faciale, biométrie serveur | Donnée sensible sous régime renforcé, aucun gain proportionné |
| Un agent IA par service | Six capacités, pas trente-quatre agents → [ADR 011](adr/011-six-capacites-ia-pas-trente-quatre-agents.md) |

---

**Suite** → [02-domaine.md](02-domaine.md) — les entités et leurs invariants.
