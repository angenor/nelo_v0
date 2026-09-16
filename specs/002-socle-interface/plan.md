# Plan d'implémentation : Le socle d'interface (T0b)

**Branche** : `002-socle-interface`, créée depuis `main` le 2026-09-15 ; la spec, la revue visuelle
validée et ce plan y sont commités | **Date** : 2026-09-17 | **Spec** : [spec.md](spec.md)

**Entrée** : la spécification de `specs/002-socle-interface/spec.md`, les huit artboards validés
de [design/](design/) et de `docs/design/canvas/US1.dc.html`, et le corpus qui fait foi :
[05-design.md](../../docs/05-design.md), `docs/design/theme.css`, [03-api.md](../../docs/03-api.md)
§ 1.9, [02-domaine.md](../../docs/02-domaine.md) § 3.4 et § 15, [01-stack.md](../../docs/01-stack.md),
[ADR 002](../../docs/adr/002-web-d-abord-capacitor-plus-tard.md), la
[constitution](../../.specify/memory/constitution.md) v1.0.0.

## Résumé

Poser `web/`, l'application Nuxt 4 dans laquelle toutes les tranches suivantes assembleront au
lieu de dessiner : le thème et les mesures du design copiés tel quel et passés à Tailwind 4 par
une passerelle sans valeur ; quatorze composants canoniques dans `components/canon/`, chacun
exportant ses états, et une page de style de développement qui les itère en clair et en sombre ;
le ruban d'état de saisie dérivé de l'état du réseau et d'une source de démonstration ; une
coquille composée par `composer(contexte)` depuis un contexte dont le type vient du contrat
(schéma Pydantic ajouté aux composants OpenAPI, sans route) ; une interface unique de plateforme à
une implémentation web ; une PWA installable avec un service worker écrit à la main de trente
lignes ; deux fichiers JSON de libellés et un pack de démonstration ; `web/ecrans.json` qui déclare
les écrans et leurs budgets ; et trois portes d'interface, P-05, P-06, P-10, avec leurs tests
négatifs, dans la même commande de vérification que les sept portes serveur.

Le bac à sable a mesuré ce que la spec ne pouvait pas savoir : le socle Nuxt pèse 76 Ko
compressés et les polices 44 Ko au premier affichage, donc **le plafond de 120 Ko n'est atteignable
qu'en comptant les polices à part**. Le plan l'applique à titre provisoire et pose la question
(Q29), parce qu'elle touche la constitution.

## Contexte technique

**Langage / version** : TypeScript 6.0.3 sur Node 24.18.1 ; Python 3.14 pour le seul schéma
Pydantic ajouté au contrat ([R-01](research.md), [R-05](research.md)).

**Dépendances principales** : Nuxt 4.5.2, Vue 3.5.42, Tailwind CSS 4.3.3 (`@tailwindcss/vite`),
`@vite-pwa/nuxt` 1.1.1 et `workbox-precaching` 7.4.1, `@fontsource/archivo`,
`@fontsource/public-sans`, `@fontsource/ibm-plex-mono` 5.3.0, `sharp` pour les icônes ;
`@playwright/test` 1.63.0, `vitest` 5.0.1, `vue-tsc` 3.3.11, `@axe-core/playwright` 4.13.0 ;
toutes épinglées exactement, toutes sous licence autorisée (MIT, Apache-2.0, OFL-1.1, MPL-2.0),
`pnpm-lock.yaml` unique à la racine ([R-01](research.md), [R-14](research.md)).

**Stockage** : aucun. Le stockage de plateforme ne porte que le thème choisi sur l'appareil ; le
service worker ne garde que les fichiers statiques immuables ([R-08](research.md), [R-21](research.md)).

**Tests** : Vitest en Node pour la logique pure ; Playwright sur Chromium et WebKit pour tout ce
qui se regarde ; axe pour le contraste ; `pytest` pour le schéma du contexte côté serveur.

**Plateforme cible** : le navigateur, sur téléphone d'entrée de gamme à 390 px, tablette, poste
partagé ; installable sur Chromium et WebKit ; le WebView de Capacitor et Tauri ensuite, sans
réécriture ([ADR 002](../../docs/adr/002-web-d-abord-capacitor-plus-tard.md)).

**Type de projet** : application web rendue par le serveur puis hydratée, dans un espace de travail
`pnpm` à la racine, membre `web/` ([R-06](research.md)).

**Objectifs de performance** : accueil de la coquille **sous 120 Ko** d'octets d'application et
**sous 45 Ko** de polices (provisoire, Q29), premier affichage utile **sous deux secondes** en 3G
lente simulée ; commande de vérification complète **sous trois minutes** ([R-15](research.md)).

**Contraintes** : CP-01 à CP-06 de la spec ; aucune ressource distante au premier affichage ;
aucune valeur de couleur hors du thème ; 390 px d'abord ; 52 / 48 / 44 px ; français partout,
accents compris, aucun tiret cadratin.

**Échelle** : quatorze composants, quatre personas, quatre écrans déclarés, deux langues, une
soixantaine de clés, dix portes.

## Contrôle de constitution

*Porte : doit passer avant la phase 0 ; revérifiée après la phase 1.* Chaque principe cite comment
la tranche le tient, ou pourquoi il ne s'applique pas encore ; un écart tacite est un refus.

| Principe | Verdict | Comment la tranche le tient |
|---|---|---|
| **I** Le serveur est la seule autorité | Conforme | Le client **affiche** : `usePack().montant()` met en forme un entier déjà calculé, `note()` une chaîne décimale ; aucune formule, aucun rang, aucun solde dans `web/` ([contracts § 6](contracts/interfaces-client.md)). La composition masque, elle n'autorise rien ; T1a et T1b posent la double barrière côté serveur |
| **II** Composition par capacités, jamais par rôles | Conforme | `composer(contexte)` ne lit que `capacites[].code` ; le registre connaît des domaines et des familles, pas des rôles ; les personas sont des listes de capacités validées contre le schéma du contrat ; un domaine sans capacité est absent du modèle (aucun champ `desactive`) ; l'écran sans capacité nomme l'administrateur, que le contexte porte désormais ([R-05](research.md), [data-model § 2](data-model.md)). P-06 règle 5 interdit l'identifiant `role` |
| **III** Cloisonnement = frontière d'import | Conforme | `web/` n'importe aucun paquet Python ; `modules/shared/contexte.py` n'importe rien de `metier/` ; P-04 et P-11 tournent inchangées et couvrent le nouveau fichier |
| **IV** Donnée de mineur | Sans objet, vérifié | Aucune donnée réelle ; les élèves de démonstration sont des noms fictifs dans des fichiers de données, jamais persistés, jamais mis en cache par le service worker |
| **V** Le pays vit dans le pack | Conforme | Aucune littérale de pays, de devise ni de vocabulaire dans `web/app/` : le symbole monétaire, l'exposant et les mots métier viennent de `country_pack` ; le pack fictif prouve que le code ne les connaît pas (FR-053). Le schéma Pydantic ajouté à `shared/` ne porte aucune littérale de pays |
| **VI** Référentiel versionné | Sans objet | Aucune évaluation ; `note()` affiche une chaîne et son barème, ne convertit rien |
| **VII** Toute entité pédagogique porte son année | Conforme à sa mesure | Le contexte porte `annees[]` et `annee_active` ; la coquille affiche l'année de travail ; aucune entité pédagogique n'est créée |
| **VIII** Montants entiers, notes NUMERIC, intervalles | Conforme | `montant(entier)` prend un entier d'unité mineure et l'exposant du pack ; `note(chaine)` prend une chaîne décimale ; les données de démonstration respectent les formats de [03-api.md § 1.4](../../docs/03-api.md) |
| **IX** Aucune saisie ne se perd | Conforme à sa mesure | Le ruban dit en permanence enregistré / en attente / hors ligne, dérivé et non posé ; il ne bloque jamais ; la source de démonstration enregistre par lots. La file d'écritures idempotentes réelle arrive avec T5 et T6b, sans toucher au ruban ([R-04](research.md)) |
| **X** Outbox dans la même transaction | Sans objet | Aucune écriture ; le schéma ajouté au contrat n'a pas de route |
| **XI** Jamais de transaction inter-modules | Sans objet, vérifié | Aucune transaction ; `shared/contexte.py` est un schéma d'échange, place prévue par [01-stack.md § 2.3](../../docs/01-stack.md) |
| **XII** Double barrière d'isolation | Sans objet | Aucune table, aucune requête ; le service worker n'intercepte jamais `/api/` ([contracts § 8](contracts/interfaces-client.md)) |
| **XIII** Le SMS est un canal de premier rang | Conforme à sa mesure | La pastille de canal met le SMS en avant avec son coût à côté de l'action ; aucun envoi |
| **XIV** L'IA propose, un humain décide | Sans objet, vérifié | Aucune capacité d'assistance n'est appelée ; aucune affordance d'assistance n'existe dans la coquille, donc rien à masquer sous suspension |
| **XV** Le poids est une contrainte | **Conforme, avec une question posée** | P-10 mesure chaque écran déclaré et refuse au dépassement ; P-06 interdit toute chaîne en dur et exige `fr` et `en` ; aucune ressource distante ; un refus annoncé avant la saisie (bouton inactif avec sa raison). **Le plafond de 120 Ko ne contient pas les polices** : le plan compte les polices à part, à titre provisoire, et pose Q29 ([R-16](research.md)). Un plafond contourné en silence serait un refus ; posé et mesuré, c'est ce que la gouvernance prévoit |

**Périmètre** : le plan n'ouvre pas `docs/06-apres-mvp.md`. **Méthode** : le plan dérive de
`02-domaine.md`, `03-api.md` et `05-design.md` ; ce qui manquait est appliqué comme diff explicite,
listé en fin de fichier. **Terminé** : rien ne l'est tant que `scripts/verifier.sh` ne passe pas en
une commande, dix portes comprises.

**Verdict de la porte** : passe. Aucune violation ; une question de constitution posée (Q29) et
appliquée à titre provisoire ; trois choix de complexité justifiés ci-dessous.

## Structure du projet

### Documentation (cette tranche)

```text
specs/002-socle-interface/
├── spec.md                       # la spécification, avec l'adresse du canvas validé
├── design/
│   ├── prompt-design.md
│   ├── US2.dc.html … US8.dc.html # revue visuelle, forme A (US1 : docs/design/canvas/)
│   └── canvas.json
├── plan.md                       # ce fichier
├── research.md                   # phase 0 : R-01 à R-22, mesures du bac à sable, diffs, Q29
├── data-model.md                 # phase 1 : le contexte, la composition, le ruban, la plateforme, les écrans, les libellés
├── contracts/
│   └── interfaces-client.md      # ce que chaque brique expose, et rien d'autre
├── quickstart.md                 # phase 1 : démarrer et prouver, user story par user story
└── tasks.md                      # phase 2 : /speckit-tasks, pas ce plan
```

### Code source (racine du dépôt)

```text
nelo_v0/
├── package.json · pnpm-lock.yaml · pnpm-workspace.yaml   # racine : openapi-typescript ; lockfile unique ; membre web
├── docs/design/
│   ├── theme.css                 # inchangé : la seule source des couleurs
│   └── mesures.css               # NOUVEAU : hauteurs, rayons, filet, ruptures, pulsation (R-17)
├── contrat/                      # openapi.json et client.d.ts portent désormais ContexteCapacites (P-03)
├── modules/shared/
│   └── contexte.py               # NOUVEAU : les modèles Pydantic de 03-api § 1.9, sans route (R-05)
├── api/contrat.py                # enregistre ContexteCapacites dans components.schemas
├── web/
│   ├── package.json              # nuxt, vue, tailwind, pwa, fontsource, playwright, vitest ; scripts dev/build/icones/test:*/portes:*
│   ├── nuxt.config.ts            # modules, css, plugin tailwind, manifeste depuis tokens.json et produit.ts, routeRules
│   ├── tsconfig.json · vitest.config.ts · playwright.config.ts   # deux projets : chromium, webkit
│   ├── ecrans.json               # LE SEUL ENDROIT : écrans, routes, personas, budgetKo, budgetPolicesKo, developpement
│   ├── scripts/icones.mjs        # SVG typographique depuis les jetons → PNG 192, 512, maskable, 180 (sharp)
│   ├── public/
│   │   ├── icones/               # généré, ignoré par git
│   │   └── licences/             # OFL des trois polices, atteint par « à propos »
│   ├── app/
│   │   ├── app.vue               # <CanonCoquille :contexte> autour de <NuxtPage>
│   │   ├── assets/css/
│   │   │   ├── theme.css         # copie octet pour octet de docs/design/theme.css (P-06)
│   │   │   ├── mesures.css       # copie octet pour octet de docs/design/mesures.css (P-06)
│   │   │   ├── jetons.css        # @import tailwindcss ; @theme inline : références var(--…), aucune valeur ; ruptures
│   │   │   └── polices.css       # @font-face des graisses servies, font-display: swap
│   │   ├── components/canon/     # les quatorze : Bouton, Champ, Interrupteur, PastilleEtat, PastilleCanal, Recherche,
│   │   │                         #   Avatar, FilAriane, Onglets, CarteIndicateur, Alerte, Tableau + LigneTableau,
│   │   │                         #   RubanSaisie, Coquille (+ CoquilleNavigation, CoquilleEntete, CoquilleSansCapacite)
│   │   ├── composables/          # useTheme, useLibelles, usePack, usePlateforme, useContexte, useSaisieDemonstration, useMiseAJour
│   │   ├── core/
│   │   │   ├── produit.ts        # NOM, NOM_COURT, VERSION : un seul endroit (R-22)
│   │   │   ├── contexte/         # types.ts (réexport du contrat), source.ts (SourceContexte), demonstration.ts
│   │   │   ├── composition/      # registre.ts (domaines, familles), composer.ts (pur), situation.ts
│   │   │   ├── saisie/           # etat-ruban.ts (pur)
│   │   │   ├── plateforme/       # plateforme.ts (interface), web.ts (l'unique implémentation), test.ts (dev et test seulement)
│   │   │   ├── i18n/             # fr.json, en.json, libelles.ts
│   │   │   ├── pack/             # pack.ts (libelle, montant, note)
│   │   │   ├── ecrans.ts         # lecteur de ecrans.json
│   │   │   └── demonstration/    # personas/*.json, pack-demonstration.json, pack-fictif.json, donnees.ts (CM2 A)
│   │   ├── layouts/              # aucun : la coquille est un composant, pas un layout
│   │   ├── pages/
│   │   │   ├── index.vue         # accueil : composé selon la situation
│   │   │   ├── d/[domaine].vue   # l'écran d'un domaine (démonstration : appel du jour, avec le ruban et un champ)
│   │   │   ├── a-propos.vue      # nom, version, licences des polices
│   │   │   └── style.vue         # la page de style, retirée de la construction par un hook pages:extend
│   │   ├── plugins/
│   │   │   ├── plateforme.client.ts  # fournit Plateforme (web, ou test en dev/test)
│   │   │   └── contexte.ts       # charge le contexte par SourceContexte avant le rendu
│   │   └── sw/sw.ts              # le service worker mince (injectManifest)
│   └── tests/
│       ├── unit/                 # composition, etat-ruban, pack, libelles, ecrans, personas contre le schéma
│       ├── e2e/                  # ruban, coquille, langue, disposition, contraste, survol, focus
│       └── portes/               # p05.spec.ts (deux moteurs, deux thèmes, installabilité), p10.spec.ts (CDP), regles-p06.test.ts
├── scripts/
│   ├── verifier.sh               # + P-06, typecheck, vitest, build, P-05, P-10, e2e ; dix portes
│   ├── tests-negatifs.sh         # + P-05, P-06, P-10
│   └── portes/
│       ├── p-05.sh · p-06.sh · p-10.sh
│       ├── p06_interface.mjs     # cinq règles
│       └── negatifs/p-05.sh · p-06.sh · p-10.sh
├── docs/design/
│   ├── composants.md             # NOUVEAU : quatorze composants, états, formes, mots ; les trois écarts tranchés
│   ├── mouvement.md              # NOUVEAU : la pulsation, prefers-reduced-motion, rien d'autre
│   └── lexique.md                # NOUVEAU : le vocabulaire visible de la tranche, semé de 05-design § 8.1
└── tests/portes/                 # + test : le contrat porte ContexteCapacites
```

**Décision de structure** : la coquille est un **composant**, pas un layout Nuxt, parce qu'elle
reçoit le contexte en prop et que sa situation est une valeur testable ; la logique qui décide
(composition, état du ruban, formats) vit dans `core/` en fonctions pures, testées sans DOM ; les
composants ne font qu'afficher ce que `core/` a décidé, et `core/plateforme/` est le seul endroit
qui touche le navigateur ([R-03](research.md), [R-09](research.md), [R-14](research.md)). Le schéma
du contexte vit dans `modules/shared/` parce que c'est la place des schémas d'échange et que T1a
y branchera sa route ([R-05](research.md)).

## Suivi de complexité

Aucune violation de la constitution. Trois choix dépassent le strict minimum et se justifient :

| Choix | Pourquoi il est nécessaire | Alternative plus simple, et pourquoi elle est écartée |
|---|---|---|
| **Un schéma Pydantic sans route dans le contrat** | CP-05 exige que le client ne réécrive aucune forme du contrat ; sans ce schéma, T0b inventerait un type local et T1a le remplacerait | Un type TypeScript local : deux vérités pendant une tranche. Une fausse route de démonstration : un endpoint sans authentification dans le socle |
| **Un module PWA (`@vite-pwa/nuxt`) pour un service worker de trente lignes** | La liste des fichiers immuables avec leurs empreintes change à chaque construction ; l'injecter à la main serait un second outil de construction | Un service worker sans liste : il ne précache rien, l'application installée ne s'ouvre pas hors ligne sur sa coquille. `generateSW` : plusieurs centaines de lignes générées à désactiver |
| **Deux nombres dans P-10 (application, polices)** | Le plafond de 120 Ko ne peut pas contenir les polices, mesure faite ; un seul nombre forcerait le choix avant l'arbitrage | Un plafond relevé en silence : contraire à la constitution. Les polices système : c'est l'issue A de Q29, à l'utilisateur de la choisir |

Et un choix qui n'est pas de la complexité mais qu'il faut voir : **Q29 appliquée à titre
provisoire**, comme Q28 l'avait été en T0a. Changer l'issue touche une ligne de `ecrans.json` et
une règle de P-10.

## Phase 0 : recherche

Produite : [research.md](research.md). Vingt-deux décisions avec motif et alternatives, et un bac
à sable qui a construit la pile retenue et mesuré le socle (76 Ko), le HTML (moins de 1 Ko), le
service worker (5,6 Ko), les polices (44 Ko en graisses fixes du premier affichage, 77 Ko en
variables) et l'effet d'un sous-ensemble (12 %). Q1 et Q4 sont tranchées, Q2 reçoit sa valeur
provisoire, Q29 est posée. Aucune « NEEDS CLARIFICATION » ne subsiste dans le contexte technique.

## Phase 1 : conception et contrats

Produits :

- [data-model.md](data-model.md) : le contexte et ses sous-modèles avec leurs validations, le
  registre des domaines et des familles, la situation et ses invariants, l'état du ruban dérivé,
  l'interface de plateforme, les écrans et leurs budgets, les libellés, les quatre personas, les
  fichiers générés.
- [contracts/interfaces-client.md](contracts/interfaces-client.md) : les props et énumérations
  des quatorze composants, le contexte tactile, la source de contexte, la composition, la
  plateforme, les libellés, le thème, le service worker, les déclarations d'écrans, le schéma
  ajouté au contrat OpenAPI.
- [quickstart.md](quickstart.md) : les commandes et les résultats attendus, user story par user
  story, avec le parcours d'installation vérifié à la main sur Chrome et Safari.

## Ce que le plan remet à `/speckit-tasks`

L'ordre suit les user stories, avec la règle de T0a : **les portes se construisent avec ce
qu'elles vérifient**, et `scripts/verifier.sh` reste vert à chaque commit. Concrètement :
d'abord `web/` vide qui construit, `ecrans.json`, P-06 et P-05 sur une page vide, puis le thème,
les mesures et la passerelle Tailwind ; puis les composants un par un avec la page de style et
`composants.md` qui grandissent ensemble ; puis le ruban et la plateforme ; puis le schéma du
contexte, la composition et la coquille ; puis la PWA ; puis l'i18n et le lexique ; puis P-10 et
les tests négatifs ; enfin la mesure des temps et le journal. Les documents de design
(`composants.md`, `mouvement.md`, `lexique.md`) s'écrivent avec le code qu'ils décrivent, pas
après ; les trois écarts de la revue y entrent tels que [R-19](research.md) les tranche.

Deux tâches de vérification à ne pas oublier : la présence du glyphe U+202F dans chaque fichier
de police servi ([R-07](research.md)), et la mesure réelle de `verifier.sh` et de
`tests-negatifs.sh` reportée au journal ([R-15](research.md)).

## Diffs sur les documents projet, appliqués le 2026-09-17

Détaillés en fin de [research.md](research.md). Chacun dérive du corpus ou d'une mesure ; ils sont
appliqués selon l'arbitrage délégué du 2026-09-14 et tracés au journal.

| Fichier | Quoi | Statut |
|---|---|---|
| `03-api.md § 1.9` | `administrateur` sur chaque établissement | Appliqué à `specify` |
| `03-api.md § 1.9` | `country_pack.vocabulaire` dans le contexte | **Appliqué** |
| `01-stack.md § 1.2` | Back-office en rendu serveur par défaut ; Q4 tranchée | **Appliqué** |
| `01-stack.md § 7` | P-06 : cinq règles, « aucune littérale d'interface » | **Appliqué** |
| `01-stack.md § 3` | La commande de l'interface, l'installation des navigateurs | **Appliqué** |
| `docs/design/mesures.css` | Nouveau : les mesures non colorées | **Appliqué** |
| `05-design.md § 0, § 3.1, § 5` | Rang de `mesures.css` ; 36 px dessinés et 44 px interactifs ; quatre niveaux d'alerte | **Appliqué** |
| `progress.md` | Q1, Q4 tranchées ; Q2 provisoire ; **Q29 ouverte** | À la fin de session |

## Q29 : ce que l'utilisateur doit trancher, et ce qui l'attend

**Le plafond de 120 Ko de l'accueil et de l'appel contient-il les polices ?** Le socle Nuxt pèse
76 Ko, les polices du premier affichage 44 Ko, la coquille elle-même une vingtaine : environ 100 Ko
sans polices, 140 à 150 avec. Trois issues, détaillées en [R-16](research.md) :

| | Issue | Recommandation |
|---|---|---|
| A | Polices système sur les écrans budgétés | Non : le système de design perd sa typographie là où on le regarde le plus |
| **B** | **120 Ko pour l'application, 45 Ko à part pour les polices, immuables et précachées** | **Oui** : ce qui change à chaque version est le code ; une police OFL se télécharge une fois par appareil |
| C | Relever à 170 Ko | Non : 3,4 s de transfert en 3G lente |

Le plan applique **B** à titre provisoire ; P-10 imprime les deux nombres et le total. La réponse
entre dans un ADR, parce que le principe XV nomme le chiffre. **Rien ne bloque `tasks` ni
`implement`** : changer d'issue touche une ligne de `ecrans.json` et une règle de P-10.

## Revérification post-conception

Le contrôle de constitution a été relu après la phase 1 : aucun calcul dans `web/`, aucun rôle,
aucune littérale de pays, aucune couleur hors du thème, aucune ressource distante, aucune donnée
mise en cache, un ruban qui ne bloque rien, un schéma d'échange à sa place. **Verdict inchangé :
passe, avec Q29 posée.** Prochaine étape : `/speckit-tasks`.
