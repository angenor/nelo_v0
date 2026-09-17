# Plan d'implémentation : Se connecter et savoir où l'on est (T1a)

**Branche** : `003-connexion-contexte`, créée depuis `main` le 2026-09-17 ; la spec, les diffs du
corpus et ce plan y sont commités | **Date** : 2026-09-17 | **Spec** : [spec.md](spec.md)

**Entrée** : la spécification de `specs/003-connexion-contexte/spec.md` et le corpus qui fait
foi : [02-domaine.md](../../docs/02-domaine.md) § 0, § 1.2, § 2.2, § 3, § 4.1, § 16, § 17 ;
[03-api.md](../../docs/03-api.md) § 1.2, § 1.3, § 1.6 à § 1.9, § 2.1, § 2.2, § 2.5, § 3 ;
[01-stack.md](../../docs/01-stack.md) § 2.3 à § 2.5, § 5.1, § 7, § 8.3 ; [ADR 005](../../docs/adr/005-isolation-des-tenants-par-rls-et-double-barriere.md),
[ADR 007](../../docs/adr/007-valkey-pour-l-ephemere.md), [ADR 013](../../docs/adr/013-le-sms-est-un-canal-de-premier-rang.md) ;
la maquette A1 ; la [constitution](../../.specify/memory/constitution.md) v1.0.0. **La revue
visuelle n'a pas eu lieu** : le plan est lancé directement après `specify`, à la demande de
l'utilisateur ; le prompt de forme A reste prêt dans [design/prompt-design.md](design/prompt-design.md),
et les écrans s'assemblent à partir de la maquette A1 et des composants de T0b en attendant.

## Résumé

Poser la première frontière de sécurité du produit : un module `habilitations` qui porte le
compte identifié par son numéro de téléphone, le code à usage unique envoyé par l'outbox (jamais
sur le chemin de la réponse, pour qu'une passerelle en panne ne publie pas l'existence des
comptes), le code personnel lié à un appareil connu, la session en Valkey avec un jeton d'accès
signé et un refresh en cookie non lisible par script qui tourne à chaque usage, la révocation par
absence de session consultée à chaque requête, l'invitation par lien, le changement de numéro et
le partage familial tracé. Quatre middlewares ASGI remplacent le tenant provisoire de T0a et
rendent vraie la table de refus des en-têtes. Deux noyaux, `personnes` et `annees`, posent les
seules colonnes que le contexte lit, pour T3a et T2a. Le pack de pays a sa table. Côté interface,
un relais Nitro met l'API sous l'origine de Nuxt et garde tout jeton hors de portée du script ;
la coquille lit le contexte réel, cinq écrans s'assemblent sans composant neuf, et les portes
ouvrent une session semée.

## Contexte technique

**Langage / version** : Python 3.14 (`==3.14.*`), TypeScript 6.0.3 sur Node 24.18.1 ; rien ne
change ([T0a R-01](../001-socle-serveur/research.md), [T0b R-01](../002-socle-interface/research.md)).

**Dépendances principales** : celles de T0a et T0b, inchangées, plus trois paquets Python
épinglés ([R-01](research.md)) : `phonenumbers` 9.0.39 (Apache-2.0), `PyJWT` 2.14.0 (MIT),
`argon2-cffi` 25.1.0 (MIT). Aucune dépendance npm nouvelle : le relais est du Nitro, le client
du `$fetch`.

**Stockage** : PostgreSQL 18, trois schémas neufs (`habilitations`, `personnes`, `annees`) et
deux ajouts à `tenants` (`country_pack`, `administrateur_compte_id`), chaque table sous RLS
activée et forcée ; Valkey pour sessions, liste de révocation, refresh, codes, appareils, limites
([data-model.md](data-model.md)). Aucune donnée durable dans Valkey, aucun secret en clair en base.

**Tests** : `pytest` (paquets `authentification`, `en_tetes`, `contexte`, extension d'`isolation`
et de `module_dore`), Vitest pour la logique pure de l'interface, Playwright sur Chromium et
WebKit avec une session semée ([R-11](research.md), [R-18](research.md)).

**Plateforme cible** : la même qu'en T0b ; le serveur derrière le relais Nuxt, lui-même derrière
un mandataire inverse en production.

**Type de projet** : le monolithe modulaire FastAPI et l'application Nuxt de l'espace de travail.

**Objectifs de performance** : ouverture par code reçu en trois écrans et moins de 90 s après le
message (SC-001) ; réouverture par code personnel sous 10 s et zéro message (SC-002) ; réponse à
la demande de code identique et écart des médianes sous 50 ms (SC-003) ; premier refus à la
requête suivant la suspension (SC-004) ; écran de connexion sous 120 Ko d'application et 45 Ko de
polices (SC-009, Q29 issue B) ; `verifier.sh` sous cinq minutes (SC-012).

**Contraintes** : la table de refus de [03-api.md § 1.2](../../docs/03-api.md) rendue vraie par
des middlewares ; aucun jeton en stockage ni en mémoire de script ; aucun code en clair dans une
table conservée ; aucune littérale de pays hors des lignes semées ; français partout, aucun tiret
cadratin.

**Échelle** : quinze routes, trois schémas et une table, une quinzaine de clés Valkey, cinq écrans,
neuf types d'événements, trois gabarits de message.

## Contrôle de constitution

*Porte : doit passer avant la phase 0 ; revérifiée après la phase 1.* Chaque principe cite comment
la tranche le tient, ou pourquoi il ne s'applique pas encore ; un écart tacite est un refus.

| Principe | Verdict | Comment la tranche le tient |
|---|---|---|
| **I** Le serveur est la seule autorité | Conforme | Le client n'applique aucune règle : la validité d'un code, d'un code personnel, d'un lien, d'un en-tête est décidée par le serveur ; l'écran ne fait qu'annoncer ce que le contrat rend prévisible (format, compte à rebours). Le middleware de session, puis l'établissement, puis l'année refusent avant toute route ([R-04](research.md)) ; la capacité passe par le point d'insertion de T0a, jamais contournée |
| **II** Composition par capacités, jamais par rôles | Conforme | Le contexte est servi avec `capacites` vide jusqu'à T1b et la coquille en dérive l'écran « aucun domaine » qui nomme l'administrateur, désormais une donnée du tenant ([R-19](research.md)) ; aucune énumération de rôles nulle part ; la règle P-06 sur le mot `role` reste active sur les écrans neufs |
| **III** Cloisonnement = frontière d'import | Conforme | Trois paquets neufs dans `socle/`, sous les deux contrats import-linter existants ; aucun n'importe `metier/` ; P-04 et P-11 les couvrent sans changement |
| **IV** Donnée de mineur | Sans objet, vérifié | Aucune donnée d'élève ; le noyau `personnes` porte nom, prénoms, langue et téléphone d'adultes titulaires d'un compte. Le journal des événements de compte est en insertion seule ; le numéro n'apparaît jamais dans une liste ([R-20](research.md)) |
| **V** Le pays vit dans le pack | Conforme | Le pack a sa table et deux packs semés dont un fictif ([R-15](research.md)) ; l'indicatif par défaut est une configuration de déploiement, le format vient de `phonenumbers` ([R-14](research.md)) ; le test d'agnosticité du contexte passe sur le tenant fictif ; consigne laissée à P-09 pour exclure les seeds |
| **VI** Référentiel versionné | Sans objet | Aucune évaluation |
| **VII** Toute entité pédagogique porte son année | Conforme | L'affectation porte `annee_id NOT NULL` ; `X-Nelo-Annee` absent sur une route pédagogique est un `400`, jamais un repli, même quand une seule année existe ; le noyau `annees` pose les index d'unicité de § 4.5 sans en implémenter les transitions ([R-02](research.md), [R-04](research.md)) |
| **VIII** Montants entiers, notes NUMERIC, intervalles | Sans objet, vérifié | Aucun montant, aucune note, aucune absence ; les dates d'affectation sont `date` |
| **IX** Aucune saisie ne se perd | Conforme | Chaque écriture porte `X-Nelo-Requete`, y compris sur `/auth/*` par la clé `idem:auth:` ([R-04](research.md)) ; un rejeu de demande de code ne renvoie pas un second message ; les identifiants de compte sont générés par le serveur pour les seeds seulement, la création par route accepte l'identifiant client comme T0a l'a posé |
| **X** Outbox dans la même transaction | Conforme | Neuf types d'événements, écrits dans la transaction du changement d'état ; l'envoi des messages est un consommateur du travailleur ([R-07](research.md), [R-08](research.md)) ; **écart nommé** : la révocation des sessions et l'oubli des appareils sont des effets sur l'éphémère exécutés après le `COMMIT` de la suspension, parce que Valkey ne participe pas à la transaction ; une panne entre les deux laisse un compte suspendu dont les sessions tombent à la requête suivante par la vérification du statut dans `session_valide`, et c'est testé |
| **XI** Jamais de transaction inter-modules | Conforme | Quatre schémas, aucune clé étrangère traversante (P-01) ; chaque lecture inter-modules passe par l'interface (`personnes.lire_identites`, `annees.lire_annees`, `tenants.lire_pack`) ; l'affectation copie l'établissement de l'année pour ne pas lire `annees` à chaque requête ([R-03](research.md)) |
| **XII** Double barrière d'isolation | Conforme | RLS activée et forcée sur chaque table neuve avec test d'isolation ; le tenant posé dans la transaction depuis le compte de la session ; les trois fonctions `SECURITY DEFINER` neuves sont nommées et énumérées par le test de T0a ; `403` sur l'en-tête d'établissement (l'exception nommée par le principe), `404` sur toute ressource hors périmètre |
| **XIII** Le SMS est un canal de premier rang | Conforme | Trois gabarits rédigés en `fr` et `en`, vérifiés sous 160 caractères par un test au dépôt, pas à l'envoi ([R-17](research.md)) ; **budget et fenêtres** : hors périmètre par la spec (T4a), et un code de connexion est par nature urgent et unitaire |
| **XIV** L'IA propose, un humain décide | Sans objet, vérifié | Aucune capacité d'assistance touchée ; le reparcours sous suspension s'étend aux routes neuves |
| **XV** Le poids est une contrainte | Conforme | Cinq écrans déclarés et budgétés au plafond de l'accueil, mesurés par P-10 avec la session semée ; aucune dépendance npm nouvelle ; clés `fr` et `en` ensemble ; chaque refus prévisible annoncé pendant la saisie avec son versant positif ; la démonstration élaguée de la production ([R-10](research.md), [R-11](research.md)) |

**Périmètre** : le plan n'ouvre pas `docs/06-apres-mvp.md`. **Méthode** : le plan dérive de
`02-domaine.md` et `03-api.md` ; ce qui manquait est appliqué comme diff explicite, listé en fin
de fichier. **Terminé** : rien ne l'est tant que `scripts/verifier.sh` ne passe pas en une
commande.

**Verdict de la porte** : passe. Aucune violation ; deux écarts nommés (les effets éphémères
après `COMMIT`, la vivacité d'une affectation en UTC) ; trois choix de complexité justifiés
ci-dessous.

## Structure du projet

### Documentation (cette tranche)

```text
specs/003-connexion-contexte/
├── spec.md                       # la spécification ; l'adresse du canvas quand la revue aura eu lieu
├── checklists/requirements.md
├── design/prompt-design.md       # forme A, prêt ; la revue n'a pas eu lieu
├── plan.md                       # ce fichier
├── research.md                   # phase 0 : R-01 à R-22, diffs
├── data-model.md                 # phase 1 : quatre schémas, Valkey, jeton, cookies, schémas Pydantic, politique
├── contracts/
│   ├── openapi-attendu.yaml      # quinze routes, ce que la génération doit produire
│   └── interfaces-python.md      # ce que chaque paquet expose, et les briques web
├── quickstart.md                 # phase 1 : démarrer et prouver, user story par user story
└── tasks.md                      # phase 2 : /speckit-tasks, pas ce plan
```

### Code source (racine du dépôt)

```text
nelo_v0/
├── pyproject.toml · uv.lock      # + phonenumbers, PyJWT, argon2-cffi ; + trois membres de l'espace de travail
├── .env.exemple                  # + NELO_SECRET_JETON, NELO_INDICATIF_DEFAUT, NELO_COOKIES_SECURE, NELO_URL_PUBLIQUE, NELO_SMS_JOURNAL, NELO_RELAIS_DE_CONFIANCE
├── contrat/                      # openapi.json et client.d.ts régénérés : quinze routes de plus (P-03)
├── api/
│   ├── main.py                   # quatre middlewares, trois routeurs, l'aiguilleur du travailleur
│   ├── asgi.py                   # NOUVEAU : CHEMINS_LIBRES, en_tete, chemin_de_route (repris du provisoire)
│   ├── session.py · etablissement.py · annee.py   # NOUVEAUX : les trois middlewares (R-04)
│   ├── idempotence.py            # clé idem:auth: sur les chemins libres
│   ├── limitation.py             # NOUVEAU : compter() en Valkey (R-05)
│   ├── consommateurs.py          # NOUVEAU : aiguilleur par type d'événement (R-08)
│   ├── erreurs.py                # en-têtes supplémentaires (Retry-After)
│   ├── contrat.py                # Authorization, X-Nelo-Annee, chemins sans établissement, schéma servi
│   ├── configuration.py          # secret, indicatif, cookies, produit, url publique, journal SMS, relais
│   ├── tenant_provisoire.py      # SUPPRIMÉ
│   └── routes/authentification.py · moi.py · comptes.py   # NOUVEAUX
├── modules/
│   ├── shared/outbox.py          # NOUVEAU : prise, marquage, reprise, génériques sur la table (R-08)
│   ├── shared/contexte.py        # Administrateur.prenoms accepte la chaîne vide
│   ├── shared/erreurs.py         # ErreurMetier.en_tetes
│   ├── socle/habilitations/      # NOUVEAU : compte, affectation, session, code, appareil, invitation, changement
│   │   ├── __init__.py · tables.py · acces.py · service.py · schemas.py · politique.py · pyproject.toml
│   │   └── messages/fr.json · en.json
│   ├── socle/personnes/          # NOUVEAU : le noyau (R-02)
│   ├── socle/annees/             # NOUVEAU : le noyau (R-02)
│   ├── socle/tenants/            # country_pack, administrateur_compte_id, lire_pack, lire_etablissements ; tenant_de_etablissement retiré
│   └── socle/communication/      # la simulation garde ses envois (R-12)
├── migrations/
│   ├── tenants/versions/0002_pack_et_administrateur.py   # NOUVEAU
│   ├── personnes/ · annees/ · habilitations/             # NOUVEAUX : alembic.ini, env.py, versions/0001
├── scripts/
│   ├── bd-vierge.sh              # boucle sur migrations/*/ ; jeu d'essai avec comptes, années, affectations, packs
│   ├── avec-serveur-dev.sh       # lance aussi l'API de test (R-11)
│   ├── portes/p12_acces_exerces.py   # quatre schémas déclarés
│   └── portes/negatifs/          # + les mutations de T1a
├── tests/
│   ├── conftest.py               # tenants_ab étendu ; sessions_ab
│   ├── authentification/ · en_tetes/ · contexte/   # NOUVEAUX
│   ├── module_dore/outils.py     # en_tetes() avec Authorization
│   └── portes/test_security_definer.py · test_contexte_au_contrat.py · test_contrat_attendu.py   # adaptés
└── web/
    ├── nuxt.config.ts            # runtimeConfig (apiBase, indicatifDefaut), define __NELO_DEMONSTRATION__
    ├── ecrans.json               # + cinq écrans, champ session
    ├── server/api/v1/[...].ts    # NOUVEAU : le relais (R-09)
    ├── app/
    │   ├── core/api/ · core/session/ · core/appareil/ · core/contexte/api.ts   # NOUVEAUX
    │   ├── composables/useApi.ts · useSession.ts    # NOUVEAUX
    │   ├── middleware/session.global.ts             # NOUVEAU
    │   ├── plugins/contexte.ts   # choisit la source (R-10)
    │   ├── pages/connexion.vue · connexion/code.vue · connexion/pin.vue · activation/[jeton].vue · compte/telephone.vue   # NOUVEAUX
    │   ├── components/canon/Champ.vue · CoquilleEntete.vue · Coquille.vue · app.vue   # saisie code ; menu de session
    │   └── core/i18n/fr.json · en.json   # espace session.
    └── tests/session.setup.ts · e2e/connexion.spec.ts · e2e/session.spec.ts   # NOUVEAUX
```

**Décision de structure** : la règle métier vit dans `habilitations/service.py` et reçoit Valkey
et la politique en paramètres ; `api/` compose, lit les en-têtes et les cookies, et ne décide
rien. Les deux noyaux sont des modules à part entière, pas des tables rangées dans
`habilitations`, parce que le schéma est la frontière ([R-02](research.md)). Côté interface, le
relais est la seule brique qui connaît un cookie de jeton ; le client, la source et les écrans ne
voient jamais un jeton ([R-09](research.md)).

## Suivi de complexité

Aucune violation de la constitution. Trois choix dépassent le strict minimum et se justifient :

| Choix | Pourquoi il est nécessaire | Alternative plus simple, et pourquoi elle est écartée |
|---|---|---|
| **Un relais Nitro qui transforme cookies et corps** | `SameSite=Strict` imposé par le corpus interdit tout échange entre deux origines ; le rendu serveur de la coquille a besoin des cookies | Un `proxy` de `routeRules` : ne transforme rien, le jeton d'accès resterait en mémoire de script et le rendu serveur peindrait un squelette |
| **Deux noyaux de modules pour quatre colonnes chacun** | Le domaine range la personne et l'année dans leur schéma ; la constitution interdit de les porter ailleurs | Nom et année sur le compte : deux entités hors de leur schéma, une reprise garantie en T2a et T3a |
| **Un consommateur d'outbox avec aiguillage et un code en clair passé par Valkey** | Le code ne doit ni partir sur le chemin de la réponse, ni entrer dans une table conservée | L'envoi synchrone : un `503` de passerelle publierait l'existence des comptes. Le code dans la charge : un secret dans un grand livre |

## Phase 0 : recherche

Produite : [research.md](research.md). Vingt-deux décisions avec motif et alternatives, dont la
chaîne de middlewares, la session et sa rotation, le code à usage unique avant tout tenant,
l'aiguillage du travailleur, le relais Nuxt, la démonstration élaguée, la session semée des
portes. Aucune « NEEDS CLARIFICATION » ne subsiste dans le contexte technique ; Q30 (les valeurs
par défaut) reste ouverte au journal sans bloquer.

## Phase 1 : conception et contrats

Produits :

- [data-model.md](data-model.md) : les quatre schémas, les fonctions `SECURITY DEFINER`, les
  événements, les clés Valkey, le jeton, les cookies, les schémas Pydantic, la politique de
  sécurité.
- [contracts/openapi-attendu.yaml](contracts/openapi-attendu.yaml) : les quinze routes avec
  leurs codes, ce que la génération doit produire.
- [contracts/interfaces-python.md](contracts/interfaces-python.md) : ce que chaque paquet
  expose, la composition d'`api/`, les briques web.
- [quickstart.md](quickstart.md) : les commandes et les résultats attendus, user story par user
  story.

## Ce que le plan remet à `/speckit-tasks`

L'ordre suit la règle de T0a : **les portes se construisent avec ce qu'elles vérifient**, et
`scripts/verifier.sh` reste vert à chaque commit. Concrètement : d'abord les dépendances, les
trois paquets vides et leurs migrations avec RLS, `bd-vierge.sh` en boucle, P-01 et P-12 verts sur
des schémas vides ; puis la migration `0002` de `tenants` (pack, administrateur, clés) ; puis
`habilitations` de l'intérieur vers l'extérieur : normalisation, politique, compte et affectation,
le code à usage unique et son consommateur, la session et la rotation, le code personnel et
l'appareil, l'invitation, la suspension, le changement, le partage ; puis les quatre middlewares
et le retrait du provisoire, avec l'adaptation des suites de T0a ; puis le contexte servi et le
contrat régénéré ; puis, côté web, le relais, le client, la source, la garde, les écrans, la
coquille, le choix d'appareil, les clés et le lexique ; puis la session semée des portes, les
écrans déclarés, les e2e et les tests négatifs ; enfin la mesure des temps et le journal.

Trois tâches de vérification à ne pas oublier : la mesure de SC-003 (cent demandes alternées) ;
l'inspection du stockage après une ouverture réelle (SC-006) ; la longueur des trois gabarits
avec les valeurs les plus longues (R-17).

## Diffs sur les documents projet, appliqués le 2026-09-17

Détaillés en fin de [research.md](research.md). Chacun dérive du corpus ou d'une contrainte
mécanique ; ils sont appliqués selon l'arbitrage délégué du 2026-09-14 et tracés au journal.

| Fichier | Quoi | Statut |
|---|---|---|
| `02-domaine.md § 1.2, § 16, § 17` | administrateur désigné, états du compte, trois clés | Appliqué à `specify` |
| `03-api.md § 1.8, § 2.1, § 2.2, § 2.5` | `API_LIMITE_DEBIT`, codes `AUT_`, `/moi/telephone`, `/comptes` | Appliqué à `specify` |
| `02-domaine.md § 3.2` | `affectation.etablissement_id` | **Appliqué** |
| `03-api.md § 2.1` | `GET /auth/appareil` | **Appliqué** |
| `01-stack.md § 2.1, § 3` | l'état du dépôt, l'API en test | À `implement` |
| `progress.md` | l'entrée du plan | Fin de session |

## Revérification post-conception

Le contrôle de constitution a été relu après la phase 1 : aucune règle côté client, aucun rôle,
aucune littérale de pays hors des seeds, une transaction par module, RLS partout, l'outbox dans
la transaction avec ses deux effets éphémères nommés, le SMS rédigé pour le SMS, cinq écrans
budgétés. **Verdict inchangé : passe, avec Q30 ouverte et la revue visuelle en attente.**
Prochaine étape : `/speckit-tasks`.
