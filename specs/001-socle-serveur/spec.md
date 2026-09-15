# Feature Specification: Le socle serveur (T0a)

**Feature Branch**: `001-socle-serveur`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: le prompt **T0a — Le socle serveur** de
[docs/04-roadmap.md](../../docs/04-roadmap.md#t0a--le-socle-serveur), collé tel quel. Il tient en
trois phrases : poser le socle serveur avant toute règle métier ; prouver qu'il tient par des
contrôles **mécaniques**, en **une seule commande** ; livrer un module doré qui sert de patron à
toutes les tranches suivantes.

> **Exception de rédaction assumée** ([04-roadmap.md § T0](../../docs/04-roadmap.md#t0--fondations)) :
> cette tranche nomme la pile technique, parce qu'ici la pile *est* le sujet. Toutes les tranches
> suivantes s'en abstiennent. Ce que la pile impose est isolé dans la section « Contraintes de
> pile » ; le reste de la spécification décrit des comportements observables.

**Sources qui font foi** : [docs/01-stack.md](../../docs/01-stack.md) (§ 2 structure et
hiérarchie, § 3 environnement, § 7 portes, § 9 licences), [docs/03-api.md](../../docs/03-api.md)
(§ 1 conventions et enveloppe d'erreur, § 2.3 ressource paramètres, § 3 règles opposables),
[docs/02-domaine.md](../../docs/02-domaine.md) (§ 0 règles transverses, § 1 schéma `tenants`,
§ 13.4 assistance, § 17 catalogue des paramètres), et la
[constitution](../../.specify/memory/constitution.md) v1.0.0.

## User Scenarios & Testing *(mandatory)*

**Acteurs.** Cette tranche n'a pas d'utilisateur final : elle n'a **aucun écran**. Ses acteurs sont
**le développeur seul** qui la construit et la vérifie, **l'auteur de chaque tranche suivante** qui
copiera le module doré comme patron, et **la commande de vérification** elle-même, qui doit
distinguer un dépôt sain d'un dépôt cassé sans qu'une personne relise quoi que ce soit.

Les user stories sont ordonnées par ce qu'elles débloquent : la première est le critère de fin,
les deux suivantes sont les fondations qui ne se rattrapent pas après coup, les autres sont ce qui
rend le contrôle mécanique et les frontières tenues.

---

### User Story 1 - Le module doré répond, et son contrat se régénère sans écart (Priority: P1)

Le développeur démarre l'environnement d'une seule commande, lance le serveur, et le **module
doré** — le catalogue de paramètres du paquet `tenants`, sur les routes que le contrat d'API lui
réserve déjà — répond en lecture et en écriture. La spécification d'API est produite depuis les
schémas de validation et les routes annotées, le client typé en est dérivé, et le régénérer ne
change rien de ce qui est commité. Un corps invalide est refusé **avant** toute règle, avec son
propre code d'erreur et le chemin de chaque champ fautif.

**Why this priority**: c'est le critère de fin nommé par la roadmap — « un endpoint répond avec un
client typé régénéré sans retouche » — et c'est le **patron** que chaque tranche suivante copiera.
Une erreur de forme ici se recopie vingt fois.

**Independent Test**: sur une base vierge, démarrer l'environnement, appliquer le schéma, lire les
paramètres effectifs d'un tenant, poser une valeur, la relire, régénérer le client, constater un
diff vide. Tout tient dans une session de test sans aucune autre user story.

**Acceptance Scenarios**:

1. **Given** un poste avec le dépôt et un moteur de conteneurs, **When** le développeur lance la
   commande de démarrage, **Then** la base de données, le magasin éphémère et le stockage d'objets
   sont disponibles — **trois services, pas un de plus** — et aucun service distant ni aucune clé
   d'API n'a été requis.
2. **Given** l'environnement démarré et le schéma appliqué sur base vierge, **When** on lit les
   paramètres effectifs d'un tenant, **Then** la réponse porte chaque clé du catalogue avec sa
   valeur effective et la portée à laquelle elle a été résolue.
3. **Given** une clé présente au catalogue, **When** on pose une valeur à une portée valide avec un
   identifiant de requête, **Then** la réponse est celle du contrat, la relecture reflète la
   valeur, et un événement a été écrit dans la même transaction que l'écriture.
4. **Given** un corps où **deux** champs sont invalides, **When** on l'envoie, **Then** la réponse
   est `422` avec le code `VAL_SCHEMA_INVALIDE`, `details` liste le chemin des **deux** champs, et
   `requete_id` reprend l'identifiant reçu.
5. **Given** un corps valide au regard du schéma mais une clé inconnue du catalogue, ou une portée
   invalide, **When** on l'envoie, **Then** le refus porte `TEN_PARAMETRE_INCONNU` ou
   `TEN_PORTEE_INVALIDE` avec, dans `details`, de quoi corriger — et c'est le **code**, jamais le
   seul statut, qui le distingue du refus de schéma.
6. **Given** le serveur lancé, **When** on génère la spécification d'API puis le client typé,
   **Then** le résultat ne diffère en rien de ce qui est commité, et le refus de validation figure
   dans la spécification générée comme n'importe quelle autre réponse du contrat.
7. **Given** le serveur lancé, **When** on interroge la sonde publique `/sante`, **Then** elle
   répond sans authentification.

---

### User Story 2 - Deux tenants ne se voient jamais (Priority: P1)

Deux établissements coexistent dans la même base. Quoi qu'un appel demande, quelle que soit la
connexion réutilisée par le pool, quelle que soit la table, un tenant ne lit ni n'écrit jamais une
ligne d'un autre. La politique d'isolation est **activée et forcée** sur chaque table, la variable
de tenant est posée **dans chaque transaction** et jamais à l'ouverture de connexion, et un test
automatisé le prouve.

**Why this priority**: une fuite entre deux établissements est l'incident qui termine le produit,
et il s'agit de dossiers de mineurs. C'est une des fondations qui ne se rattrapent pas après coup :
chaque table de chaque tranche suivante héritera de ce mécanisme.

**Independent Test**: créer deux tenants avec chacun des valeurs de paramètres, lire depuis
chacun, tenter d'atteindre une ressource de l'autre par son identifiant, réutiliser une même
connexion pour les deux en séquence. Aucune autre user story n'est nécessaire.

**Acceptance Scenarios**:

1. **Given** deux tenants A et B portant chacun des valeurs de paramètres, **When** A lit ses
   paramètres, **Then** aucune ligne de B n'apparaît, et une ressource de B demandée par son
   identifiant répond `404`, jamais `403`.
2. **Given** une transaction ouverte **sans** variable de tenant, **When** on lit une table,
   **Then** aucune ligne n'est visible — pas « toutes » — et toute écriture est refusée.
3. **Given** une connexion du pool utilisée par A puis rendue, **When** B ouvre une transaction sur
   cette même connexion, **Then** rien de A ne fuit : la variable est posée par transaction, jamais
   sur la connexion.
4. **Given** le rôle applicatif distinct du propriétaire des tables, **When** l'application accède
   aux données, **Then** c'est par ce rôle et la politique s'applique même au propriétaire, parce
   qu'elle est forcée.
5. **Given** une table ajoutée sans politique, ou dont la politique est retirée, **When** la
   vérification tourne, **Then** elle échoue en nommant la table.

---

### User Story 3 - Aucune saisie ne se perd : rejeu et événements (Priority: P2)

Sur un réseau lent, un client renvoie ses écritures. Chaque écriture porte un identifiant de
requête que le client a généré ; le serveur mémorise la réponse ; un rejeu identique rend la même
réponse **sans réexécuter l'effet**, un rejeu divergent est refusé. Tout changement d'état écrit un
événement **dans la même transaction**, et un travailleur du **même processus** le consomme — sans
file de messages.

**Why this priority**: la saisie perdue est le seul indicateur du brief dont le rouge est fatal, et
l'idempotence avec mémorisation de la réponse est une des quatre fondations du hors-connexion
différé. L'outbox est ce qui garantit qu'une transaction qui échoue n'envoie rien et qu'une
transaction qui réussit envoie toujours.

**Independent Test**: sur le module doré, poser une valeur avec un identifiant, rejouer à
l'identique, rejouer avec un corps différent, provoquer un échec de transaction, puis laisser le
travailleur consommer. Ne dépend que de la user story 1.

**Acceptance Scenarios**:

1. **Given** une écriture réussie portant l'identifiant R, **When** la même requête est rejouée
   avec R, **Then** la réponse est identique — statut et corps — et l'effet n'a été exécuté qu'une
   fois : une seule valeur, un seul événement.
2. **Given** l'identifiant R déjà consommé, **When** une requête portant R arrive avec un corps
   différent, **Then** la réponse est `409 REQUETE_REJOUEE_DIFFEREMMENT`.
3. **Given** une écriture sans identifiant de requête, ou avec un identifiant malformé, **When**
   elle arrive, **Then** la réponse est `400` avec l'enveloppe d'erreur.
4. **Given** une écriture dont la transaction échoue, **When** on inspecte la table d'événements,
   **Then** aucun événement n'y a été écrit.
5. **Given** un événement écrit, **When** le travailleur tourne dans le processus du serveur,
   **Then** l'événement est consommé et marqué traité ; **Given** un traitement qui échoue,
   **Then** l'événement reste en attente de reprise, jamais perdu.

---

### User Story 4 - Les frontières de paquets tiennent, et un import interdit est arrêté (Priority: P2)

L'espace de travail est découpé selon la hiérarchie `domaine`, `shared`, `socle`, `metier`,
`segments`, `api`. Un développeur qui fait importer un paquet métier par le socle, ou qui importe
le module de protection depuis n'importe où — au niveau du module, différé au fond d'une fonction,
ou par un chemin écrit en chaîne — est arrêté par un test, pas par une relecture. Le cloisonnement
de `protection` tient par **trois verrous**.

**Why this priority**: ce sont les deux garanties que le compilateur donnait gratuitement et que le
changement de pile a transformées en tests à écrire ([ADR 017](../../docs/adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md)).
C'est ce que T0a « pourrait fermer » selon la roadmap : le socle contaminé par un module,
`protection` importé. Un module qui pourrait lire un signalement finirait par le lire.

**Independent Test**: introduire tour à tour chaque import interdit dans une copie de travail et
constater l'échec nommant l'arête ; retirer l'import et constater le passage. Ne dépend d'aucune
autre user story.

**Acceptance Scenarios**:

1. **Given** la hiérarchie en place, **When** un paquet de `socle/`, `domaine/` ou `shared/`
   importe un paquet de `metier/` ou de `segments/`, **Then** le test de graphe d'imports échoue
   et nomme le paquet importateur et le paquet importé.
2. **Given** un import de `protection` au niveau d'un module, **When** la vérification tourne,
   **Then** elle échoue ; **Given** le même import déplacé au fond d'une fonction, **Then** elle
   échoue encore ; **Given** le chemin du module de protection écrit en chaîne de caractères hors du
   module lui-même, **Then** elle échoue encore.
3. **Given** le point d'entrée du paquet `protection`, **When** il expose une entité, un accès aux
   données ou une session en plus de son interface de service, **Then** la vérification échoue.
4. **Given** une déclaration de dépendance vers `protection` dans la configuration d'un paquet,
   **When** la vérification tourne, **Then** elle échoue.
5. **Given** un dépôt conforme, **When** les tests de graphe passent, **Then** ils annoncent le
   nombre de modules inspectés, et **échouent si ce nombre est nul** — une porte qui n'a rien
   inspecté n'a rien prouvé.

---

### User Story 5 - Une seule commande vérifie tout, et chaque porte prouve qu'elle mord (Priority: P2)

Le développeur lance `scripts/verifier.sh`. Elle enchaîne tout ce qui doit passer, sort en échec au
premier contrôle rouge en nommant la porte, et tient dans un temps qui permet de la lancer avant
chaque commit. Chacune des **sept** portes serveur a son **test négatif** exécutable : on la casse
volontairement, en isolation, sans laisser de trace, et on vérifie qu'elle échoue vraiment.

**Why this priority**: un développeur seul n'a pas le temps de relire des spécifications pour
vérifier qu'un changement est juste. Ce qui a de la valeur est que le contrôle soit mécanique, pas
qu'une machine le lance. Et une porte qui ne trouve jamais rien est indistinguable d'une porte qui
n'a rien à trouver.

**Independent Test**: lancer la commande sur le dépôt conforme (succès), puis lancer la suite des
tests négatifs (sept échecs attendus, sept obtenus, dépôt intact à la fin). Ne dépend que de
l'existence des portes.

**Acceptance Scenarios**:

1. **Given** un dépôt conforme, **When** la commande de vérification tourne, **Then** toutes les
   portes passent, la sortie est un succès, et la durée reste sous le seuil qui justifierait un
   serveur d'intégration continue.
2. **Given** une porte violée, **When** la commande tourne, **Then** elle s'arrête à cette porte,
   sort en échec, et dit **laquelle** et **pourquoi** — jamais un simple « échec ».
3. **Given** la suite des tests négatifs, **When** on l'exécute, **Then** chacune des sept portes
   est cassée une fois, en isolation, échoue, et le dépôt est retrouvé intact.
4. **Given** une fonction d'accès aux données qu'aucun test n'exerce, **When** la vérification
   tourne, **Then** elle **échoue** en nommant la fonction — elle ne baisse pas une couverture.
5. **Given** une colonne renommée par une migration sans que la requête qui la lit soit modifiée,
   **When** la vérification tourne, **Then** elle échoue.
6. **Given** une dépendance déclarée en intervalle, un fichier de verrouillage absent, ou une
   dépendance sous licence copyleft fort, **When** la vérification tourne, **Then** elle échoue en
   nommant la dépendance.
7. **Given** le client typé modifié à la main, **When** la vérification tourne, **Then** elle échoue
   sur l'écart entre le client régénéré et le client commité.

---

### User Story 6 - Les dépendances externes sont simulées, et savent échouer (Priority: P3)

La passerelle de messages courts, l'agrégateur de paiement et le service d'inférence existent
derrière une abstraction chacun, avec une implémentation **simulée** livrée en même temps, active
par défaut. Chaque simulation sait réussir **et** échouer — accusé en retard, en double, jamais
reçu, service indisponible — et son mode se déclenche depuis la configuration. L'interface est
dessinée en pensant à la vraie implémentation qui la servira.

**Why this priority**: la frontière d'une dépendance externe se pose dès le début, l'implémentation
vient plus tard. Quand T4a et T8b arriveront, ce sera un **remplacement**, pas une découverte. Un
webhook de paiement qui n'arrive jamais est le cas nominal à concevoir, pas l'exception.

**Independent Test**: appeler chaque abstraction dans chaque mode configuré et observer le
comportement attendu, dont l'absence de blocage en mode « jamais reçu ». Ne dépend d'aucune autre
user story.

**Acceptance Scenarios**:

1. **Given** la configuration par défaut, **When** on envoie un message court, initie un paiement
   ou demande une inférence par l'abstraction, **Then** la simulation réussit et rend un accusé.
2. **Given** le mode « accusé en retard », **When** on appelle, **Then** l'accusé arrive après le
   délai configuré ; **Given** le mode « accusé en double », **Then** il arrive deux fois ;
   **Given** le mode « jamais reçu », **Then** aucun accusé n'arrive et l'appelant ne bloque pas
   au-delà d'un délai borné.
3. **Given** le mode « indisponible », **When** un appel de l'API dépend de cette dépendance,
   **Then** la réponse est `503` avec l'enveloppe d'erreur.
4. **Given** l'interface de chaque abstraction, **When** on la relit, **Then** chaque opération est
   documentée face à l'opération du fournisseur réel qu'elle représentera, et aucune signature ne
   suppose une réponse synchrone là où le fournisseur répond par accusé différé.
5. **Given** le fichier de composition, **When** on le relit, **Then** le service d'inférence n'y
   figure pas : c'est une dépendance externe derrière son interface, simulée par défaut.

---

### User Story 7 - L'assistance a sa place, et sa suspension est un test (Priority: P3)

L'assistance est un **paquet du socle**, jamais un service à déployer. Cette tranche pose le paquet,
son interface, et le **réglage serveur** du catalogue de paramètres qui la suspend à sa portée. Les
six capacités sont connues de l'interface ; aucune n'est livrée ici, et appeler l'une d'elles est un
refus explicite. La vérification pose la suspension et reparcourt le module doré : tout passe à
l'identique.

**Why this priority**: « la plateforme reste pleinement opérationnelle avec l'assistance
désactivée » est un test, pas une hypothèse — et c'est ce que le changement de pile a transformé :
ce n'est plus un conteneur qu'on arrête, c'est un paramètre posé à sa portée. Le poser maintenant
évite qu'une capacité ultérieure devienne indispensable sans qu'on le voie.

**Independent Test**: appeler une capacité non livrée (refus), poser la suspension par le module
doré, interroger l'interface (suspendue), relancer la suite de tests du module doré (succès
inchangé). Dépend de la user story 1.

**Acceptance Scenarios**:

1. **Given** le paquet d'assistance, **When** une capacité non encore livrée est appelée, **Then**
   le refus est explicite et testé — ni silence, ni simulation qui réussit.
2. **Given** le réglage de suspension posé à une portée par la route d'écriture des paramètres,
   **When** l'assistance est interrogée pour cette portée, **Then** elle se déclare suspendue,
   refuse tout appel, et cet état est exposé de façon que l'interface puisse **ne pas afficher**
   l'affordance — jamais la griser.
3. **Given** la suspension posée, **When** la vérification reparcourt l'ensemble des tests du
   module doré, **Then** tout passe à l'identique — et ce reparcours **fait partie** de la
   commande de vérification.
4. **Given** le fichier de composition et l'espace de travail, **When** on les relit, **Then**
   aucun service d'assistance n'existe : le paquet est appelé comme n'importe quel paquet du socle.

---

### Edge Cases

- **Rejeu après expiration de la mémoire.** La réponse est mémorisée 24 h. Un rejeu au-delà est
  une requête nouvelle, traitée comme telle : le contrat le dit, le test le fixe.
- **Identifiant de requête réutilisé entre deux tenants.** L'identifiant est généré par le client ;
  la mémorisation est bornée au tenant, deux tenants ne peuvent pas se bloquer mutuellement.
- **Transaction sans variable de tenant.** Aucune ligne visible, aucune écriture possible — jamais
  « toutes les lignes ». L'oubli est un refus, pas une fuite.
- **Reprise d'un événement.** Un traitement interrompu est repris ; l'événement peut donc être
  livré plus d'une fois, il n'est jamais perdu. Le consommateur le sait.
- **Travailleur arrêté.** Les événements s'accumulent dans la table et sont consommés au
  redémarrage ; aucun n'est perdu, aucun n'est traité hors de son ordre d'écriture par tenant.
- **Base non vierge.** La porte des migrations s'exerce sur une base **vierge**, recréée ; un
  schéma résiduel n'est jamais pris pour une preuve.
- **Import de `protection` par un chemin écrit en chaîne.** Toute référence textuelle au chemin du
  module de protection hors du module lui-même échoue la porte : la règle est mécanique, pas
  interprétée.
- **Le paquet `protection` s'importe lui-même.** Ses propres fichiers et ses propres tests sont la
  seule exception, et la porte le sait.
- **Simulation en mode « jamais reçu ».** L'appelant attend un délai borné, puis constate l'absence
  d'accusé ; il ne bloque pas le processus.
- **Second fichier de verrouillage absent.** Le verrouillage de l'interface n'existe pas avant T0b.
  La porte vérifie le verrouillage de **chaque espace de travail présent**, et échoue si un espace
  existe sans son verrouillage.
- **Réglage de suspension posé à une portée, lu à une autre.** La résolution suit la chaîne de
  portées avec surcharge locale : suspendue au tenant, l'assistance l'est partout en dessous ;
  suspendue à un établissement, elle ne l'est que là.
- **Test négatif qui laisse une trace.** La suite des tests négatifs restaure le dépôt à
  l'identique ; un test négatif qui laisse un fichier modifié est lui-même un échec.

## Requirements *(mandatory)*

### Contraintes de pile — l'exception assumée

Ces contraintes sont nommées parce que la pile est le sujet de la tranche. Elles font foi par
[docs/01-stack.md § 1](../../docs/01-stack.md) et [ADR 017](../../docs/adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md) ;
elles ne se rediscutent pas ici.

- **CP-01** : FastAPI et Pydantic pour l'API et la frontière de validation.
- **CP-02** : SQLAlchemy **Core** et `asyncpg` pour l'accès aux données — **jamais l'ORM**. Le SQL
  est écrit, pas deviné.
- **CP-03** : Alembic pour les migrations, **un dossier par module**, sous `migrations/<module>/`.
- **CP-04** : `uv` pour l'environnement et le verrouillage (`uv.lock`), `ruff` pour le style et
  l'analyse, `pytest` pour les tests.
- **CP-05** : PostgreSQL, Valkey et Garage, décrits par `compose.yml`, démarrés par Docker Compose.
- **CP-06** : la structure cible de [docs/01-stack.md § 2.3](../../docs/01-stack.md) et la
  hiérarchie de dépendance de son § 2.4, sans variante.

### Functional Requirements

**Environnement**

- **FR-001** : Un fichier de composition unique décrit l'environnement local et se démarre par une
  seule commande ; il fournit **exactement trois services** — la base de données, le magasin
  éphémère, le stockage d'objets.
- **FR-002** : Aucun service distant ni aucune clé d'API n'est requis pour développer ni pour
  vérifier. Le service d'inférence n'est pas un service de la composition.

**Structure et frontières**

- **FR-003** : L'espace de travail est découpé en paquets selon la hiérarchie `domaine`, `shared`,
  `socle`, `metier`, `segments`, `api`, avec au minimum les paquets que cette tranche remplit
  (`socle/tenants`, `socle/assistance`, `shared`, `api`) et le paquet `metier/protection`, présent
  et vide de logique, pour que sa frontière ait un objet.
- **FR-004** : Un test de graphe d'imports échoue si un paquet de `domaine/`, `shared/` ou `socle/`
  importe un paquet de `metier/` ou de `segments/`, et si `metier/` importe `segments/`. Il nomme
  l'arête fautive.
- **FR-005** : Le même test échoue si un paquet quelconque, hors `protection` lui-même, importe
  `protection` — au niveau du module, différé dans une fonction, ou par le chemin du module écrit
  en chaîne.
- **FR-006** : Le cloisonnement de `protection` tient par trois verrous, chacun vérifié : aucune
  déclaration de dépendance vers lui ; le test de graphe d'imports ; un point d'entrée qui n'expose
  rien hors de son interface de service — ni entité, ni accès aux données, ni session.
- **FR-007** : Chaque paquet expose son interface de service par son point d'entrée et rien d'autre
  n'en sort ; les dépendances sont injectées, jamais importées depuis un autre module.
- **FR-008** : Les tests de graphe annoncent le nombre de modules inspectés et échouent s'il est nul.

**Le module doré**

- **FR-009** : Un module doré est écrit **à la main, de bout en bout** — entité, accès aux données,
  service, gestionnaire de requêtes, tests — : le catalogue de paramètres du paquet `tenants`, sur
  les routes `GET /parametres` et `PUT /parametres/{cle}` telles que
  [docs/03-api.md § 2.3](../../docs/03-api.md) les définit.
- **FR-010** : Le module doré ne porte **aucune généricité prématurée** : aucune classe de base,
  aucun dépôt générique, aucune abstraction dont il serait le seul utilisateur. Du code concret se
  refactore ; une abstraction prématurée se subit.
- **FR-011** : La valeur effective d'un paramètre se résout le long de la chaîne de portées
  `tenant → établissement → site → cycle` avec surcharge locale ; un seul trait la porte, testé y
  compris sur les surcharges partielles.
- **FR-012** : Une clé absente du catalogue est refusée avec `TEN_PARAMETRE_INCONNU` ; une portée
  plus basse que la portée la plus basse de la clé, ou hors du tenant, avec `TEN_PORTEE_INVALIDE` ;
  `details` porte de quoi corriger.
- **FR-013** : Chaque écriture du module doré écrit un événement dans la table d'événements, dans
  sa transaction.
- **FR-014** : Une sonde publique `/sante` répond sans authentification.
- **FR-015** : Jusqu'à T1a, aucune session n'existe : le tenant courant est résolu depuis l'en-tête
  d'établissement par un mécanisme **explicitement marqué provisoire**, et la vérification de
  capacité est un **point d'insertion** que T1b remplit. La barrière applicative existe comme point
  de passage obligé dès maintenant, jamais absente, jamais contournable.

**Isolation par tenant**

- **FR-016** : La politique de sécurité au niveau ligne est **activée et forcée** sur chaque table,
  avec sa politique, et le rôle applicatif est distinct du propriétaire des tables.
- **FR-017** : La variable de tenant est posée **dans chaque transaction**, jamais à l'ouverture de
  connexion ; sans elle, aucune ligne n'est visible et aucune écriture n'est possible.
- **FR-018** : Un test d'isolation entre deux tenants est automatisé, y compris sur une connexion
  du pool réutilisée en séquence par les deux.
- **FR-019** : Une ressource hors du périmètre du tenant répond `404`, jamais `403`.

**Idempotence**

- **FR-020** : Toute écriture porte l'en-tête `X-Nelo-Requete`, un UUID v7 généré par le client ;
  absent ou malformé, la réponse est `400` avec l'enveloppe d'erreur.
- **FR-021** : La réponse d'une écriture est mémorisée 24 h ; un rejeu identique rend la même
  réponse — statut et corps — sans réexécuter l'effet.
- **FR-022** : Un rejeu portant le même identifiant et un corps différent est refusé par
  `409 REQUETE_REJOUEE_DIFFEREMMENT`.
- **FR-023** : La mémorisation est bornée au tenant.
- **FR-024** : Toute enveloppe d'erreur porte `requete_id`, l'identifiant reçu.

**Table d'événements et travailleur**

- **FR-025** : Une table d'événements existe ; tout changement d'état y écrit un événement **dans
  la même transaction** ; une transaction qui échoue n'écrit rien.
- **FR-026** : Un travailleur du **même processus** consomme les événements, sans file de messages ;
  il les marque traités ; un traitement en échec laisse l'événement en attente de reprise ; un
  événement n'est jamais perdu et peut être livré plus d'une fois.
- **FR-027** : Les événements sont isolés par tenant comme toute autre table, et consommés dans
  l'ordre de leur écriture par tenant.

**Contrat d'API**

- **FR-028** : La spécification d'API est générée depuis les schémas de validation et les routes
  annotées, et servie par le serveur ; le client typé est généré depuis cette spécification,
  jamais écrit à la main.
- **FR-029** : Le refus de validation est un citoyen de premier rang du contrat : `422`, code
  `VAL_SCHEMA_INVALIDE`, `details` portant le chemin de chaque champ fautif, enveloppe complète —
  et il figure dans la spécification générée.
- **FR-030** : Tout refus, quel que soit son statut, porte l'enveloppe de
  [docs/03-api.md § 1.6](../../docs/03-api.md) avec un code stable préfixé par domaine.
- **FR-031** : Aucune route neuve n'entre dans le code sans entrer dans `docs/03-api.md` dans le
  même changement. Cette tranche n'en ajoute aucune : ses trois routes y figurent déjà.

**L'assistance**

- **FR-032** : L'assistance est un paquet du socle, jamais un service ; son interface connaît les
  six capacités ; aucune n'est livrée ici, et l'appel d'une capacité non livrée est un refus
  explicite, testé.
- **FR-033** : Un réglage serveur du catalogue de paramètres suspend l'assistance à sa portée, posé
  par la route d'écriture des paramètres. Sa clé entre au catalogue de
  [docs/02-domaine.md § 17](../../docs/02-domaine.md) par un diff explicite, proposé dans les
  hypothèses ci-dessous et arbitré **avant** le plan.
- **FR-034** : Suspendue, l'assistance se déclare suspendue, refuse tout appel, et expose cet état
  de façon que l'interface puisse ne pas afficher l'affordance — jamais la griser.
- **FR-035** : La commande de vérification pose la suspension et reparcourt l'ensemble des tests du
  module doré ; le résultat est identique.

**Dépendances externes simulées**

- **FR-036** : Trois abstractions existent — passerelle de messages courts, agrégateur de paiement,
  service d'inférence — chacune avec une implémentation simulée, active par défaut.
- **FR-037** : Chaque simulation sait réussir et échouer selon au moins quatre modes — accusé en
  retard, accusé en double, accusé jamais reçu, service indisponible — déclenchables depuis la
  configuration ; le mode « jamais reçu » ne bloque pas l'appelant au-delà d'un délai borné.
- **FR-038** : La signature de chaque abstraction peut être servie par une vraie implémentation ;
  chaque opération est documentée face à l'opération du fournisseur réel, et l'accusé différé y est
  le cas nominal.
- **FR-039** : Une dépendance externe indisponible fait répondre `503` avec l'enveloppe d'erreur.

**La vérification**

- **FR-040** : `scripts/verifier.sh` enchaîne tout ce qui doit passer en une commande, sort en
  échec au premier contrôle rouge, et nomme la porte et le motif.
- **FR-041** : Sept portes serveur sont livrées — **P-01** (le schéma s'applique sur base vierge,
  un dossier de migration par module, chaque table porte sa politique d'isolation, aucune clé
  étrangère ne traverse un schéma de module), **P-02** (aucune dépendance en intervalle, fichiers
  de verrouillage commités), **P-03** (le client régénéré ne produit aucun écart), **P-04** (aucun
  paquet du socle n'importe un paquet métier), **P-07** (aucune licence copyleft fort), **P-11** (le
  cloisonnement tient par ses trois verrous), **P-12** (toute fonction d'accès aux données est
  exercée contre la base fraîchement migrée).
- **FR-042** : Chaque porte a son test négatif **exécutable**, en isolation, qui casse la porte,
  vérifie qu'elle échoue, et laisse le dépôt intact ; un test négatif qui laisse une trace est un
  échec.
- **FR-043** : Chaque porte annonce ce qu'elle a inspecté et échoue si elle n'a rien inspecté.
- **FR-044** : P-12 : toute fonction d'accès aux données non exercée par un test **fait échouer**
  la porte en la nommant ; aucune requête n'est construite par concaténation ; le schéma migré est
  comparé au schéma attendu — colonne absente, type divergent, contrainte manquante.
- **FR-045** : Les migrations sont **réversibles** ; une migration appliquée n'est jamais modifiée ;
  une migration ne touche jamais le schéma d'un autre module.
- **FR-046** : Toute dépendance est épinglée exactement ; les fichiers de verrouillage de chaque
  espace de travail présent sont commités ; seules les licences autorisées par
  [docs/01-stack.md § 9](../../docs/01-stack.md) sont acceptées.
- **FR-047** : Aucun serveur d'intégration continue ; la vérification tourne sur le poste.

**Langue et libellés**

- **FR-048** : Le code, les commentaires, les noms de tables et de colonnes, les messages d'erreur
  destinés au journal sont en français, accents compris.
- **FR-049** : Aucun libellé visible en dur : le catalogue porte des clés de description, jamais un
  texte affiché ; les clés `fr` et `en` naissent ensemble.

### Key Entities *(include if feature involves data)*

- **Tenant** : le groupe scolaire ou la fondation qui souscrit — l'unité d'isolation. Porte son
  pays et sa version de country pack ([02-domaine.md § 1.2](../../docs/02-domaine.md)).
- **Établissement** : l'unité pédagogique et juridique d'un tenant ; c'est lui que l'en-tête
  d'établissement désigne.
- **Entrée du catalogue de paramètres** : une clé, sa portée la plus basse, son type, sa valeur par
  défaut, sa clé de description.
- **Valeur de paramètre** : une clé, une portée (`TENANT`, `ETABLISSEMENT`, `SITE`, `CYCLE`),
  l'identifiant de la portée, la valeur. Isolée par tenant.
- **Événement** : une ligne de la table d'événements — tenant, type, charge, instant d'écriture,
  état de traitement. Écrit dans la transaction du changement d'état.
- **Réponse mémorisée** : l'identifiant de requête, le tenant, une empreinte du corps reçu, la
  réponse rendue, l'instant ; expire après 24 h.
- **Enveloppe d'erreur** : `code`, `message`, `champ`, `details`, `requete_id`
  ([03-api.md § 1.6](../../docs/03-api.md)).
- **Interface d'assistance** : les six capacités connues, leur état (non livrée, suspendue,
  disponible) à une portée donnée.
- **Abstractions externes** : passerelle de messages courts, agrégateur de paiement, service
  d'inférence — chacune avec son implémentation simulée et son mode configuré.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** : Sur un poste où le dépôt vient d'être cloné, l'environnement démarre par une seule
  commande et le module doré répond en moins de cinq minutes, sans aucun service distant.
- **SC-002** : Le module doré répond sur ses routes de lecture et d'écriture, et la régénération du
  client typé produit **zéro** ligne d'écart avec ce qui est commité.
- **SC-003** : La commande de vérification passe en une invocation sur le dépôt conforme, et
  **chacune des sept portes** échoue quand son test négatif la casse — sept sur sept, dépôt intact
  à la fin.
- **SC-004** : Dans le test d'isolation, un tenant voit **zéro** ligne d'un autre, sur chaque table,
  y compris sur une connexion réutilisée.
- **SC-005** : Un rejeu identique rend une réponse identique octet pour octet et laisse exactement
  une valeur et un événement ; un rejeu divergent est refusé à chaque fois.
- **SC-006** : Cent pour cent des fonctions d'accès aux données sont exercées contre la base
  migrée ; en retirer une du jeu de tests fait échouer la vérification.
- **SC-007** : Un corps portant deux champs invalides produit un refus dont `details` nomme les
  deux chemins, et ce refus apparaît dans la spécification d'API générée.
- **SC-008** : Assistance suspendue, la suite de tests du module doré passe à cent pour cent, et
  l'interface d'assistance répond « suspendue » à chaque capacité.
- **SC-009** : Chacune des trois simulations expose son mode de succès et ses quatre modes d'échec,
  tous déclenchables par configuration sans modifier le code.
- **SC-010** : La commande de vérification complète tient sous trois minutes sur le poste — le
  seuil au-delà duquel [docs/01-stack.md § 7.5](../../docs/01-stack.md) prévoit qu'on cesse de la
  lancer.

## Assumptions

- **Le module doré est le catalogue de paramètres du paquet `tenants`.** Le prompt demande « un
  module doré » sans le nommer. Le catalogue est retenu parce qu'il existe déjà dans le contrat
  (`GET /parametres`, `PUT /parametres/{cle}`), qu'il est le support du réglage de suspension de
  l'assistance exigé par la même tranche, et qu'il offre une lecture, une écriture, un refus de
  schéma et deux refus métier — tout ce que le patron doit montrer. Il appartient au socle, pas au
  métier, et ne porte aucune notion pédagogique.
- **Le schéma `tenants` est posé au minimum pour `tenant`, `etablissement`, `parametre_catalogue`
  et `parametre_valeur`.** `site`, `cycle_actif`, `module`, `module_actif` et `country_pack`
  arrivent avec les tranches qui les utilisent. La chaîne de résolution des portées est écrite
  pour les quatre portées et testée sur celles dont l'entité existe.
- **Diff proposé sur `docs/02-domaine.md` § 17**, à arbitrer avant le plan — le catalogue ne porte
  aujourd'hui aucune clé pour l'assistance :

  ```diff
   | `securite.expiration_delegation_max_jours` | TENANT | `90` |
  +| `assistance.suspendue` | ÉTABLISSEMENT | `false` |
   | `conservation.dossier_eleve_annees` | *country pack* | — |
  ```

  Portée la plus basse `ÉTABLISSEMENT` : c'est l'unité qui souscrit un module et qui décide de ce
  qui apparaît à ses écrans. Une autre clé, une autre portée ou une autre valeur par défaut sont
  des arbitrages de l'utilisateur ; la spécification ne dépend que de l'existence d'un tel réglage.
- **Les sept portes serveur sont P-01, P-02, P-03, P-04, P-07, P-11 et P-12.** P-05, P-06 et P-10
  concernent l'interface et arrivent avec T0b. P-08 et P-09 arrivent avec la première tranche qui
  leur donne matière — T2a pour les provisions d'extension, T6a pour l'agnosticité au pays, selon
  le tableau « Ce qu'une tranche ne doit pas fermer » de la roadmap.
- **Aucune authentification avant T1a.** Le tenant est résolu depuis l'en-tête d'établissement par
  un mécanisme provisoire, la capacité `tenant.parametre.definir` est un point d'insertion vide que
  T1b remplit. Les deux barrières existent dès maintenant comme points de passage ; aucune n'est
  jamais la seule.
- **La mémoire des réponses dure 24 h**, par [docs/03-api.md § 1.3](../../docs/03-api.md).
- **Le fichier de verrouillage de l'interface n'existe pas avant T0b.** La porte P-02 vérifie
  chaque espace de travail présent et échoue si l'un existe sans son verrouillage.
- **La sonde `/sante` est livrée ici** parce qu'elle existe au contrat et que la vérification a
  besoin de savoir que le serveur est levé ; elle ne porte aucune donnée.
- **La supervision (OpenTelemetry) et la console éditeur ne sont pas dans cette tranche** : le
  prompt ne les nomme pas.
- **Les tests négatifs s'exécutent sur une copie de travail temporaire** ou par une mutation
  restaurée en fin de test ; le mécanisme est un choix du plan, la propriété — le dépôt intact —
  est celle de la spécification.

## Hors périmètre

- Toute logique métier, tout écran, toute intégration réelle, tout déploiement.
- Les portes qui concernent l'interface — P-05, P-06, P-10 — livrées par T0b.
- Les portes P-08 et P-09, sans matière avant T2a et T6a.
- L'authentification, les sessions, les capacités et les périmètres — T1a et T1b.
- Les deux capacités d'assistance C1 et C5 — elles arrivent avec leurs tranches.
- Toute implémentation réelle des dépendances externes — T4a et T8b les remplacent.
- Le serveur d'intégration continue.
- Tout ce que [docs/06-apres-mvp.md](../../docs/06-apres-mvp.md) décrit ; ce document ne s'ouvre
  pas pour cette tranche.

## Revue visuelle

Cette tranche ne produit aucun écran : la revue prend la **forme B** de
[docs/05-design.md](../../docs/05-design.md#forme-b--la-tranche-na-pas-décran) — une planche de
diagrammes Mermaid, un seul fichier `design/diagrammes.md`, en session dédiée après cette
spécification et avant le plan. Le prompt prêt à coller est dans
[design/prompt-diagrammes.md](design/prompt-diagrammes.md). **On ne lance pas `/design`.**
