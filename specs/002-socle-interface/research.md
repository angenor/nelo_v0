# Recherche : Le socle d'interface (T0b)

*Phase 0 du plan. Chaque décision porte son motif et les alternatives écartées. Ce qui a été
mesuré l'a été dans un bac à sable hors dépôt le 2026-09-17, sur le poste de développement.*

Ce que la spécification laissait au plan : les versions et les licences (CP-02, FR-074), la
stratégie de rendu (CP-06, Q4), les polices (Q1), le nom et l'icône provisoires (Q2), la mécanique
des trois portes d'interface et de leurs tests négatifs (FR-070 à FR-075), la source du type de
contexte (CP-05, FR-020), l'interface de plateforme (FR-043, FR-044), le service worker (FR-045),
la mesure du poids (FR-060 à FR-064), l'i18n (FR-050 à FR-054), et les trois écarts relevés à la
revue visuelle.

## R-01 : Node 24, Nuxt 4.5.2, TypeScript 6.0.3, versions épinglées exactement

**Décision.** Node 24.18.1 (présent sur le poste, dans les moteurs exigés par Nuxt :
`^22.19.0 || ^24.11.0 || >=26`), `pnpm` 10.26.2 (déjà le gestionnaire du dépôt), Nuxt 4.5.2,
Vue 3.5.42, TypeScript 6.0.3, `vue-tsc` 3.3.11. Toutes les dépendances de `web/package.json` sont
épinglées `x.y.z`, comme P-02 l'exige déjà pour le `package.json` racine ; `pnpm-lock.yaml` reste
**unique, à la racine**, puisque `pnpm-workspace.yaml` déclare déjà `web`.

**Motif.** La règle de version du corpus est « la dernière stable, sauf conflit constaté »
([01-stack.md § 1](../../docs/01-stack.md)). TypeScript 7.0.2 existe sur le registre mais c'est le
portage natif, sorti depuis peu ; `vue-tsc` 3.3 et l'outillage Nuxt sont testés contre la lignée 6.
Le bac à sable a construit la combinaison retenue sans conflit (voir R-07 pour les mesures).

**Alternatives écartées.** TypeScript 7 : trop neuf pour la chaîne Vue, aucun gain pour la tranche.
Un second lockfile dans `web/` : P-02 en compte deux aujourd'hui (`uv.lock`, `pnpm-lock.yaml`), un
troisième compliquerait la porte sans rien protéger de plus.

## R-02 : Tailwind 4 par le plugin Vite, le thème copié tel quel, une passerelle de jetons sans valeur

**Décision.** Tailwind CSS 4.3.3 via `@tailwindcss/vite` 4.3.3, comme la pile le prévoit
([01-stack.md § 1](../../docs/01-stack.md), ligne « Style »). Trois fichiers CSS dans
`web/app/assets/css/` :

1. `theme.css` : **copie octet pour octet** de `docs/design/theme.css`, comparée par P-06 ;
2. `mesures.css` : copie de `docs/design/mesures.css` (R-17), même règle ;
3. `jetons.css` : `@import "tailwindcss"` puis un bloc `@theme inline` qui **mappe** chaque jeton
   du thème vers un nom Tailwind (`--color-primary: var(--primary)`, …) : ce fichier ne contient
   **aucune valeur**, seulement des références.

Les composants emploient les utilitaires Tailwind ainsi dérivés ou `var(--jeton)` directement ;
jamais une couleur.

**Motif.** Tailwind 4 lit les variables CSS natives, donc le thème reste la seule source et la
bascule `[data-theme]` fonctionne sans configuration. Le CSS produit ne contient que les classes
employées : quelques kilo-octets, compatibles avec R-16.

**Alternatives écartées.** CSS pur sans Tailwind : possible, mais la pile le nomme, et l'auteur de
tranche assemble plus vite avec des utilitaires. Réécrire les jetons dans la config Tailwind :
une seconde vérité, exactement ce que le corpus interdit.

## R-03 : Quatorze composants dans `components/canon/`, un contexte tactile fourni par l'écran

**Décision.** Un fichier par composant dans `web/app/components/canon/` : `Bouton.vue`,
`Champ.vue`, `Interrupteur.vue`, `PastilleEtat.vue`, `PastilleCanal.vue`, `Recherche.vue`,
`Avatar.vue`, `FilAriane.vue`, `Onglets.vue`, `CarteIndicateur.vue`, `Alerte.vue`,
`LigneTableau.vue` (avec `Tableau.vue` pour l'en-tête et la transformation en cartes),
`RubanSaisie.vue`, `Coquille.vue`. Nuxt les importe automatiquement sous le préfixe `Canon`
(`<CanonBouton>`). Chaque état est une **prop typée** (`variante`, `etat`, `voix`) documentée dans
`docs/design/composants.md`, et la page de style itère sur ces mêmes listes : c'est ce qui rend
FR-092 vérifiable, la page et le document lisent la même énumération exportée par le composant.

Le **contexte tactile** (`classe` | `standard` | `poste`) est fourni par l'écran via
`provide('contexte-tactile')` et se traduit par une variable CSS `--cible` que chaque composant
interactif emploie en `min-height` et `min-width` ; la valeur de repli est `standard`. Le poste
dessine à 36 px mais garde une zone interactive de 44 px par un pseudo-élément (FR-082).

**Motif.** Un nom unique par composant, une énumération d'états unique, et une page de style qui
ne peut pas diverger du document parce qu'elle lit la même liste.

**Alternatives écartées.** Une bibliothèque de composants tierce : poids, survol, cibles et voix de
couleur à combattre à chaque écran, et un système de design qui n'est plus le nôtre.

## R-04 : Le ruban lit le réseau par la plateforme et les saisies par une source de démonstration

**Décision.** `RubanSaisie.vue` reçoit trois entrées : `dernierEnregistrement` (instant ou
`null`), `enAttente` (entier), et l'état du réseau lu par `usePlateforme().reseau` (R-09). L'état
du ruban est **dérivé** : `enregistre` si réseau bon et zéro en attente, `envoi` si des saisies
sont en attente et le lien existe, `hors_ligne` si le lien est absent. Un composable
`useSaisieDemonstration()` simule l'enregistrement par lots : chaque saisie incrémente le compte,
et un lot part au bout d'un délai quand le lien existe, ce qui fait descendre le compte sans geste
(FR-014). Les tranches de saisie (T5, T6b) remplaceront cette source par la vraie file
d'écritures idempotentes ; **le ruban ne change pas**.

**Motif.** Le ruban doit être testable dès maintenant sous les trois états et prouver qu'il ne
bloque rien (US2) ; l'état du réseau doit venir de l'interface unique, jamais de `navigator.onLine`
dans le composant (FR-016, FR-044).

**Alternatives écartées.** Un état de ruban posé par l'écran : chaque écran l'aurait recalculé
différemment. Une vraie file d'écritures dès T0b : c'est de la persistance, hors périmètre.

## R-05 : Le type du contexte vient du contrat, par un schéma enregistré sans route

**Décision.** Le contexte de [03-api.md § 1.9](../../docs/03-api.md) devient un modèle Pydantic
`ContexteCapacites` dans `modules/shared/contexte.py` (le paquet `shared` porte les « schémas
Pydantic d'échange », [01-stack.md § 2.3](../../docs/01-stack.md)), avec ses sous-modèles
(`Compte`, `EtablissementContexte`, `Administrateur`, `AnneeContexte`, `CapaciteContexte`,
`AccesNominatif`, `CountryPackContexte`, `AlerteContexte`). `api/contrat.py` l'ajoute aux
`components.schemas` du document OpenAPI **sans route** ; P-03 régénère `contrat/client.d.ts`,
qui expose `components["schemas"]["ContexteCapacites"]`. Côté client, `core/contexte/types.ts`
ne fait que **réexporter** ce type. T1a écrira la route `GET /moi/capacites` qui renvoie ce
modèle : le point de jonction est le même fichier.

`SourceContexte` est une interface à une méthode (`charger(): Promise<ContexteCapacites>`) ;
l'implémentation de cette tranche, `SourceDemonstration`, lit un des personas JSON de
`core/contexte/demonstration/` (un domaine, cinq, sept, aucune capacité), choisi par un réglage
de développement (`?persona=` en développement, le premier sinon). Chaque persona est une liste
de capacités et un contexte complet, **jamais un nom de rôle** (FR-021).

**Motif.** CP-05 interdit de réécrire une forme du contrat à la main ; sans ce schéma, T0b aurait
dû inventer un type local, et T1a l'aurait remplacé, deux vérités pendant une tranche.

**Alternatives écartées.** Une route `GET /moi/capacites` de démonstration côté serveur : un faux
endpoint sans authentification dans un socle qui n'en a pas encore, à retirer ensuite. Un type
TypeScript local : contraire à CP-05.

## R-06 : La coquille est rendue par le serveur ; Q4 est tranchée, avec un diff sur 01-stack § 1.2

**Décision.** La coquille et les écrans qui s'y assemblent en classe sont **rendus par le
serveur** (mode universel de Nuxt, hydratation ensuite). Le site public restera statique et les
portails rendus serveur, comme l'hypothèse le disait ; la ligne « back-office : rendu client »
est **contredite par la mesure** et remplacée : rendu serveur par défaut, rendu client possible
écran par écran, par règle de route, quand P-10 et le premier affichage le permettent.

**Motif.** L'arithmétique de SC-006 : 120 Ko à 400 kbit/s (le profil « 3G lente ») font 2,4 s de
transfert seul. Un rendu client ne peint rien avant d'avoir reçu le paquet JavaScript ; un rendu
serveur peint la coquille et le ruban avec le HTML et le CSS, une vingtaine de kilo-octets, sous
la seconde. L'écran d'appel, qui s'assemblera dans cette coquille, porte la même contrainte et
c'est lui que la ligne « back-office » aurait classé en rendu client. Q4 disait « se réexamine si
la mesure la contredit » : c'est le cas.

**Alternatives écartées.** Rendu client avec squelette : le squelette n'est pas un affichage utile.
Pré-rendu statique de la coquille : elle dépend du contexte de la personne.

**Diff appliqué** sur [01-stack.md § 1.2](../../docs/01-stack.md) : la ligne « Back-office »
devient « Rendu serveur par défaut ; rendu client écran par écran, par règle de route, quand la
mesure P-10 le permet », et l'encadré cesse de renvoyer la question au journal. Q4 passe en
« tranchée » dans `progress.md`.

## R-07 : Trois polices servies localement, variables quand elles existent, latin seul ; Q1 tranchée

**Décision.** `@fontsource/archivo` 5.3.0 (700, puis 500 et 600 à la demande),
`@fontsource/public-sans` 5.3.0 (400 et 500, puis 600 à la demande), `@fontsource/ibm-plex-mono`
5.3.0 (500 seule, à la demande), toutes **OFL-1.1**, déjà dans la liste blanche de P-07. Seul le sous-ensemble **latin** est servi ; il doit contenir U+202F, l'espace fine
insécable des montants, que la revue visuelle a exigée. `font-display: swap`, préchargement des
trois fichiers du premier affichage (Public Sans 400 et 500, Archivo 700), le reste chargé à sa
première utilisation. L'avis de licence des trois polices est copié dans `web/public/licences/` et
l'écran « à propos » y renvoie (FR-008, [01-stack.md § 9](../../docs/01-stack.md)).

**Mesures du bac à sable** (fichiers `woff2`, sous-ensemble latin) : Archivo variable
34 928 o, Public Sans variable 26 832 o, IBM Plex Mono 500 14 888 o, soit
76 648 o pour les trois. À comparer aux graisses fixes : Archivo 600 + 700
28 328 o, Public Sans 400 + 500 + 600 43 880 o.

**Motif.** Le premier affichage ne charge rien d'un service distant (FR-063, constitution XV) ;
le
sous-ensemble latin couvre le français et l'anglais, et les deux langues sont les seules du pack.
**Le sous-ensemble ne suffit pas** : réduit par `fonttools` aux plages du français et de
l'anglais (U+202F compris), chaque fichier ne perd que 12 % (Archivo variable 30 528 o, Public
Sans variable 24 100 o, Plex Mono 13 080 o). Le levier réel est de ne charger au premier
affichage que les graisses qu'il emploie : Public Sans 400 et 500, Archivo 700, soit 44 Ko en
graisses fixes, la mono et les autres graisses à leur première utilisation. **Les polices
variables sont donc écartées pour le premier affichage** et gardées pour les écrans qui emploient
plus de trois graisses. La présence du glyphe U+202F dans chaque fichier servi est une tâche de
vérification à `implement` (le contrôle du bac à sable n'a pas pu la lire) ; à défaut, la police
de repli le rend comme une espace, ce qui reste lisible.

**Alternatives écartées.** Google Fonts : distant, interdit sur le chemin du premier affichage.
Les polices système : ce serait abandonner le système de design.

## R-08 : Une PWA par `@vite-pwa/nuxt` en mode `injectManifest`, un service worker écrit à la main

**Décision.** `@vite-pwa/nuxt` 1.1.1 (MIT) avec la stratégie **`injectManifest`** : le service
worker est **notre fichier**, `web/sw/sw.ts`, une trentaine de lignes lisibles, dans lequel le
plugin injecte la liste des fichiers statiques immuables produits par la construction
(`precacheAndRoute` de `workbox-precaching`, MIT). Le service worker **ne fait rien d'autre** : pas
de mise en cache à l'exécution, pas de réponse portant une donnée, pas d'écriture, pas de file
(FR-045). Les navigations vont toujours au réseau.

**Mise à jour** (FR-042) : `registerType: 'prompt'` côté plugin, et un composable `useMiseAJour()`
qui, quand un nouveau service worker attend, demande `skipWaiting` **seulement** si aucune saisie
n'est en attente (R-04), sinon à la prochaine ouverture. Aucun message « rechargez la page ».

**Manifeste** : généré dans `nuxt.config.ts` à partir de `docs/design/tokens.json` pour les
couleurs (`theme_color` = `--primary` clair, `background_color` = `--bg` clair) et de
`web/app/core/produit.ts` pour le nom (R-22). **Icônes** : un script `web/scripts/icones.mjs`
dessine un SVG typographique depuis les mêmes jetons et le rastérise avec `sharp` (Apache-2.0) en
192, 512, 512 maskable et 180 (`apple-touch-icon`) dans `web/public/icones/`, dossier ignoré par
git et régénéré par `pnpm --filter web icones`, appelé avant `dev` et `build`. Le contrôle des
littérales de couleur exempte le manifeste généré et ce dossier.

**Installabilité** : P-05 vérifie mécaniquement les critères sur les deux moteurs (manifeste
servi et valide, `display: standalone`, icônes 192 et 512 présentes, `apple-touch-icon` et
`apple-mobile-web-app-capable` dans le `<head>`, service worker enregistré et contrôlant la page
sur Chromium). **L'installation elle-même est un parcours vérifié à la main** dans le
[quickstart](quickstart.md), sur Chrome et sur Safari : aucun moteur n'expose l'interface
d'installation à un test automatisé, et le dire vaut mieux qu'un test qui prétend.

**Motif.** Le plugin fait ce qu'il est pénible de refaire (la liste des fichiers avec leurs
empreintes, l'enregistrement) et laisse le service worker entièrement lisible, ce que
[ADR 002](../../docs/adr/002-web-d-abord-capacitor-plus-tard.md) appelle « mince ».

**Alternatives écartées.** `generateSW` : un service worker généré de plusieurs centaines de lignes,
avec des stratégies de cache à désactiver une par une. Un service worker sans plugin : la liste
des fichiers immuables change à chaque construction, il faudrait réécrire l'injection.

## R-09 : L'interface de plateforme, une implémentation web, un plugin qui la fournit

**Décision.** `web/app/core/plateforme/` porte `Plateforme` (interface TypeScript) :
`reseau` (`etat: 'bon' | 'faible' | 'absent'`, `surChangement(cb)`), `stockage` (`lire`, `ecrire`,
`effacer`, `disponible`), `camera` (`capturer(): Promise<Blob | null>`, `disponible`),
`notifications` (`demander()`, `afficher()`, `disponible`). Chaque capacité expose `disponible`
et répond `indisponible` ou `null` sans lever (FR-043). `web.ts` est l'unique implémentation :
`navigator.onLine` et `navigator.connection` quand elle existe, `localStorage`, `getUserMedia`,
`Notification`. Un plugin Nuxt client la fournit ; `usePlateforme()` l'injecte. Le plugin
Capacitor ou Tauri de demain fournira une autre instance, aucun écran ne change.

**Motif.** [ADR 002](../../docs/adr/002-web-d-abord-capacitor-plus-tard.md) : « un seul point
d'appel, une seule implémentation, web ». Le contrôle mécanique de FR-044 (R-11) interdit
`navigator.`, `window.`, `localStorage`, `Notification`, `document.` hors de ce dossier.

**Alternatives écartées.** Une bibliothèque d'abstraction (Capacitor Core dès maintenant) : poids
et dépendance à une chaîne native que l'ADR diffère.

## R-10 : L'i18n est un composable et deux fichiers JSON, le pack un troisième

**Décision.** `web/app/core/i18n/fr.json` et `en.json`, clés plates en notation pointée
(`ruban.enregistre`, `coquille.aucune_capacite.titre`), chargés selon la langue du contexte ;
`useLibelles()` expose `t(cle, params)`. **Aucune bibliothèque d'i18n.** Le vocabulaire métier
passe par `usePack()` : `libelle(code)` résout un code neutre (`CLASSE`, `PERIODE`,
`RESPONSABLE`, …) dans le pack du contexte, pour la langue courante. Le pack de démonstration
est `core/pack/demonstration.json` ; un pack **fictif** `core/pack/fictif.json`, au vocabulaire
différent, sert au test de FR-053. À l'exécution, une clé absente rend une chaîne vide et
journalise en développement, jamais la clé brute (FR-054).

**Motif.** La tranche a quelques dizaines de clés, deux langues, aucune pluralisation complexe, et
un budget de 120 Ko : `@nuxtjs/i18n` embarque `vue-i18n` (une vingtaine de kilo-octets
compressés) et un routage par langue dont le produit ne veut pas.

**Alternatives écartées.** `@nuxtjs/i18n` 10.6.0 : voir ci-dessus, réexaminable si une tranche
exige des pluriels par langue.

## R-11 : P-06 devient « aucune littérale d'interface », cinq règles, un script

**Décision.** `scripts/portes/p-06.sh` lance `scripts/portes/p06_interface.mjs` (Node, sans
dépendance hors `@vue/compiler-sfc`, déjà présent via Vue et épinglé à la même version). Cinq
règles, chacune nommant le fichier en échec :

1. **Chaînes en dur** : dans chaque `.vue` de `web/app/`, tout nœud texte du gabarit contenant
   une lettre, et toute valeur statique des attributs `placeholder`, `title`, `alt`,
   `aria-label`, `aria-description`, `label`, est une violation ; la liste d'attributs est dans le
   script. Les fichiers de démonstration JSON sont des données, hors contrôle.
2. **Clés orphelines** : les ensembles de clés de `fr.json` et `en.json` sont identiques ; toute
   clé passée à `t()` dans le code existe.
3. **Couleurs littérales** : aucune occurrence de `#xxx`/`#xxxxxx`, `rgb(`, `hsl(`, `oklch(`,
   ni de nom de couleur CSS dans `web/app/`, hors `assets/css/theme.css` (comparé octet à octet à
   `docs/design/theme.css`) et `assets/css/mesures.css` ; le manifeste et `public/icones/` sont
   générés et exemptés.
4. **Plateforme** : `navigator.`, `window.`, `document.`, `localStorage`, `sessionStorage`,
   `indexedDB`, `Notification`, `caches` sont interdits hors `core/plateforme/web*.ts` et du
   service worker.
5. **Rôles** : aucun identifiant `role`, `roles`, `Role` ni chaîne `"role"` dans `web/app/` hors
   des attributs ARIA (`role="…"` dans un gabarit est permis) ; les personas de démonstration sont
   validés contre le schéma du contexte, qui ne porte pas de rôle.

**Motif.** Une seule porte, une seule commande, cinq règles nommées : c'est moins de cérémonie que
trois portes nouvelles, et la constitution associe déjà P-06 au principe XV. **Diff appliqué** sur
[01-stack.md § 7](../../docs/01-stack.md) : P-06 « Aucune littérale d'interface en dur : chaîne
visible, valeur de couleur, appel direct de plateforme, rôle ; les clés `fr` et `en` existent
toutes les deux ».

**Test négatif** : une chaîne en dur dans `Coquille.vue`. Une seule mutation suffit ; les quatre
autres règles ont chacune un test unitaire positif et négatif dans `web/tests/portes/`.

**Alternatives écartées.** Un plugin ESLint : une dépendance de plus, et la règle des couleurs et
de la plateforme aurait de toute façon exigé un script.

## R-12 : P-05 ouvre chaque écran déclaré dans `web/ecrans.json`, sur deux moteurs, deux thèmes

**Décision.** `web/ecrans.json` est **le seul endroit** qui déclare les écrans : pour chacun,
`route`, `nom`, `budgetKo` (entier ou `null`), `developpement` (booléen) et, pour l'accueil, les
personas à parcourir. `@playwright/test` 1.63.0 (Apache-2.0) avec deux projets, `chromium` et
`webkit` ; `web/tests/portes/p05.spec.ts` ouvre chaque route × persona × thème (`data-theme`
forcé à `light` puis `dark`), attend le repère `main`, et échoue sur toute erreur de page ou de
console, en nommant écran, moteur et thème. Les critères d'installabilité (R-08) sont dans le même
fichier. La construction se fait **une fois** (`nuxt build`), servie par `node .output/server/index.mjs` ;
la page de style s'atteint en développement par un second serveur `nuxt dev`, lancé et arrêté par
la porte.

**Navigateurs** : Playwright 1.63 attend Chromium 1243 et WebKit 2359 ; le cache du poste porte
d'autres révisions, donc `pnpm exec playwright install chromium webkit` **une fois, avec réseau**,
au démarrage rapide. La vérification est ensuite hors ligne.

**Test négatif** : une page qui lève au montage. P-05 doit échouer en nommant l'écran.

**Motif.** « Monter un composant dans un test ne prouve pas qu'une page s'atteint : la porte
ouvre un vrai navigateur. » Deux moteurs parce que le corpus les nomme, et parce que WebKit est le
seul moteur d'iOS.

**Alternatives écartées.** Firefox en troisième : hors corpus, temps de porte. Des captures d'écran
comparées : fragiles, et la revue visuelle est déjà faite ailleurs.

## R-13 : P-10 mesure les octets transférés par le protocole du navigateur, service worker bloqué

**Décision.** `web/tests/portes/p10.spec.ts` sur Chromium seulement : une session CDP par écran
budgété, `Network.enable`, somme des `encodedDataLength` des événements `loadingFinished` entre la
navigation et `networkidle`, **service worker bloqué** (`serviceWorkers: 'block'`) pour mesurer ce
qu'une première visite transfère. Le serveur de production (`.output`) sert les fichiers statiques
compressés (`nitro.compressPublicAssets`), le HTML est compté tel quel. La porte compare chaque
mesure au `budgetKo` de `web/ecrans.json`, échoue au premier dépassement en nommant écran,
plafond et mesure, et **liste les écrans sans budget** (FR-060). Le premier affichage utile
(SC-006) est mesuré dans le même fichier sous `Network.emulateNetworkConditions` (400 kbit/s,
400 ms), par l'instant où le ruban est visible.

**Test négatif** : une image PNG de 300 Ko ajoutée au gabarit de l'accueil.

**Motif.** `encodedDataLength` est ce qui a traversé le réseau, compression comprise ; c'est la
définition du corpus (« Ko transférés »).

**Alternatives écartées.** Peser `.output/public` : ignore ce que l'écran charge réellement.
Lighthouse : lourd, et son audit PWA n'existe plus.

## R-14 : Vitest pour la logique pure, Playwright pour tout ce qui se regarde, axe pour le contraste

**Décision.** `vitest` 5.0.1 en environnement Node pour les fonctions pures : la composition
(`composer(contexte) → situation`), la résolution des libellés et du pack, le lecteur de
`ecrans.json`, la dérivation de l'état du ruban. Aucun DOM simulé. Les scénarios des user stories
(ruban sous trois états, quatre situations de coquille, changement de langue et de pack, cartes à
390 px, cibles tactiles, focus clavier, survol) sont des tests Playwright dans `web/tests/e2e/`,
sur Chromium, à 390, 768 et 1200 px. `@axe-core/playwright` 4.13.0 (**MPL-2.0**, autorisée par
[01-stack.md § 9](../../docs/01-stack.md)) vérifie le contraste AA de la page de style dans les
deux thèmes (FR-085). Le réseau des tests e2e est simulé par une **implémentation de test** de
`Plateforme`, injectée par une variable de fenêtre lue **uniquement** par le plugin de plateforme
en développement et en test : c'est la seule porte d'entrée, et elle vit dans `core/plateforme/`.

**Motif.** Ce qui est pur se teste en millisecondes ; ce qui se regarde se teste dans un navigateur
réel. `happy-dom` et `@nuxt/test-utils` n'apportent rien entre les deux.

**Alternatives écartées.** Tests de composants montés en DOM simulé : c'est précisément ce que le
corpus refuse comme preuve.

## R-15 : `scripts/verifier.sh` s'allonge de cinq étapes, la construction n'a lieu qu'une fois

**Décision.** Ordre : `ruff` → P-02 → P-07 → P-04 → P-11 → **P-06** (statique, quelques secondes)
→ P-01 → P-12 → P-03 → reparcours sous suspension → **`vue-tsc` + `vitest`** → **`nuxt build`
(une fois)** → **P-05** → **P-10** → **e2e**. Le rapport final compte dix portes. Les trois portes
d'interface partagent `.output` ; P-05 lance en plus `nuxt dev` pour la page de style. Chaque
porte d'interface écrit sa ligne `PORTE P-XX : …` ou `PORTE P-XX ÉCHOUÉE : …`, comme les sept
autres, et `tests-negatifs.sh` ajoute `P-05`, `P-06`, `P-10` à sa liste : chaque copie de travail
fait `pnpm install --offline` puis, pour P-05 et P-10, une construction.

**Coût estimé** : construction 30 à 60 s, P-05 une trentaine de secondes (une douzaine d'écrans ×
deux moteurs × deux thèmes), P-10 et e2e une trentaine de secondes, `vue-tsc` et `vitest`
une dizaine. Total attendu : **2 à 2 min 30 s** avec les 19 s de T0a, sous les trois minutes de
SC-011 ; la mesure réelle est reportée dans le journal à `implement`. `tests-negatifs.sh` passera
de 49 s à plusieurs minutes à cause des deux constructions : ce n'est pas la commande quotidienne.

**Motif.** Une seule commande, du moins cher au plus cher, sortie au premier rouge : la règle de
T0a ([research.md R-18](../001-socle-serveur/research.md)).

## R-16 : Les budgets en un seul fichier, et ce que le bac à sable dit du plafond de 120 Ko

**Décision.** `web/ecrans.json` (R-12) porte les budgets. Cette tranche déclare : `accueil`
(personas un domaine, cinq, sept, aucune) **120 Ko**, `domaine` 120 Ko (c'est l'accueil
mono-domaine), `a-propos` 150 Ko, `style` non budgété et `developpement: true`. Les plafonds du
corpus ([05-design.md § 9.3](../../docs/05-design.md)) sont recopiés en commentaire du fichier.

**Mesures du bac à sable** (Nuxt 4.5.2, Tailwind 4, PWA, une page minimale, sortie compressée) :

| Ce qui est transféré au premier affichage | Octets compressés |
|---|---|
| Socle Nuxt : Vue (41 003 o seul), routeur, en-tête, entrée | 75 878 |
| HTML d'une page minimale | 677 |
| Service worker (bloqué à la mesure, non compté) | 5 644 |
| Polices du premier affichage, graisses fixes (R-07) | 44 292 |
| Polices variables, si elles étaient retenues | 76 648 |

Une coquille réelle ajoute son propre code (dix à quinze kilo-octets), son CSS (quelques
kilo-octets) et un HTML rendu par le serveur (quelques kilo-octets) : **environ 100 Ko sans les
polices, 140 à 150 Ko avec.** Le plafond de 120 Ko est **atteignable sans les polices, pas avec**,
et aucun sous-ensemble ne change cette conclusion (R-07). Le socle Nuxt seul consomme les deux
tiers du plafond, et c'est la pile que le corpus a choisie ([ADR 000](../../docs/adr/000-nuxt-et-rust-une-seule-application.md)).

**Ce que le plan retient, à titre provisoire, et ce qu'il demande.** Le plafond de 120 Ko est
écrit dans la constitution (XV) : le plan ne peut pas le redéfinir seul, il propose. Trois issues :

| Issue | Ce qu'elle coûte |
|---|---|
| **A. Polices système sur les écrans budgétés** | Le système de design perd sa typographie sur l'écran le plus regardé du produit |
| **B. Le plafond compte les octets de l'application (HTML, CSS, JavaScript, images, données) ; les polices ont leur propre plafond, 45 Ko, et sont immuables et précachées par le service worker** (recommandée) | Une première visite non installée transfère jusqu'à 165 Ko ; les visites suivantes et l'application installée n'en transfèrent plus les polices. La mesure reste mécanique : P-10 rapporte **les deux nombres** |
| **C. Relever le plafond de l'accueil et de l'appel à 170 Ko** | Le chiffre du brief change ; sur 3G lente, 170 Ko font 3,4 s de transfert |

**Le plan applique B à titre provisoire** : `ecrans.json` porte `budgetKo` et `budgetPolicesKo`,
P-10 mesure les deux et échoue sur l'un ou l'autre, le rapport imprime aussi le total. Si
l'utilisateur retient A ou C, une ligne de `ecrans.json` et une règle de P-10 changent ; rien
d'autre. **La question est ouverte au journal (Q29)** et son ADR formalisera la réponse, comme la
gouvernance de la constitution l'exige.

**Motif de la recommandation.** Le brief mesure l'adoption ; ce qui change à chaque version, et
qu'il faut retélécharger, est le code ; une police OFL ne change pas d'une année sur l'autre, et
l'installation, qui est la cible, la garde. Le premier affichage utile sous deux secondes (SC-006)
tient dans les trois cas parce que la coquille est rendue par le serveur (R-06) et que
`font-display: swap` peint avant les polices.

## R-17 : Les mesures non colorées entrent dans les actifs de design, `docs/design/mesures.css`

**Décision.** Un fichier nouveau, `docs/design/mesures.css`, copié tel quel dans `web/` comme
`theme.css`, porte les valeurs que [05-design.md § 3](../../docs/05-design.md) et la planche
fixent déjà et que `theme.css` ne porte pas : `--cible-classe: 52px`, `--cible-standard: 48px`,
`--cible-plancher: 44px`, `--controle-poste: 36px`, `--pastille: 24px`, `--rayon-carte: 8px`,
`--rayon-champ: 6px`, `--rayon-pastille: 999px`, `--rayon-micro: 4px`, `--filet: 1px`, les
points de rupture `768px` et `1200px`, et la seule durée connue, `--pulsation: 1.2s
ease-in-out` (la planche, « envoi en cours »). Rien d'autre : aucune valeur inventée. **Une exception mécanique** : une requête média ne peut pas
lire une variable CSS, donc les deux points de rupture sont aussi déclarés dans le bloc `@theme`
de `jetons.css` ; un test compare les deux valeurs à celles de `mesures.css`.

**Motif.** Ces valeurs existent dans le corpus mais dispersées ; un composant qui les écrit en dur
crée la seconde vérité que CLAUDE.md interdit. Le thème « ne se réécrit pas » : on ne le modifie
donc pas, on pose le fichier compagnon à côté, avec la même règle de copie. **Diff appliqué** :
le fichier est créé, et [05-design.md § 0](../../docs/05-design.md) le liste au rang 2.

**Alternatives écartées.** Les écrire dans `theme.css` : le fichier est l'actif du design et sa
copie à l'identique est vérifiée ; le modifier ici, c'est décider à la place du design. Les écrire
dans Tailwind : seconde vérité.

## R-18 : Les données de démonstration sont du primaire, dans `core/demonstration/`

**Décision.** Un dossier `web/app/core/demonstration/` : les quatre personas (R-05), le pack de
démonstration et le pack fictif (R-10), et les jeux de données des composants (élèves de CM2 A,
reçus, indicateurs) que la page de style et les artboards validés emploient. Noms fictifs,
établissement fictif, jamais une donnée réelle ; CM2, maître titulaire, conseil des maîtres,
jamais « 6e B » (FR-091). Ces fichiers sont des données : hors P-06.

## R-19 : Les trois écarts de la revue visuelle, tranchés dans `composants.md` et `lexique.md`

**Décision**, dérivée du corpus, tracée ici et dans les deux documents :

1. **« Validé » prend la voix de réussite**, pas le vert profond : [05-design.md § 1.1](../../docs/05-design.md)
   dit que le vert profond « ne porte aucun état » et que la réussite porte « l'enregistré, le
   soldé, le justifié » ; validé en fait partie. La planche 13 s'écarte de sa propre règle écrite.
2. **Le canal se dit « En ligne »**, comme [05-design.md § 5](../../docs/05-design.md) et
   [ADR 002](../../docs/adr/002-web-d-abord-capacitor-plus-tard.md) (« l'espace en ligne ») ; le
   mot « Web » de la planche entre au lexique dans la colonne « on ne dit jamais ».
3. **Un champ en erreur prend la voix danger** (rouge), avec une icône et son message : c'est le
   niveau « danger » que le composant alerte porte déjà (FR-003), et la planche le dessine ainsi.
   La règle « le rouge est réservé à l'impayé et à l'absence non justifiée » vise les **états
   métier** (pastilles, alertes de situation) ; une erreur de saisie n'est pas un état métier, et
   l'ocre lui est interdit par [05-design.md § 1.3](../../docs/05-design.md) (« l'ocre n'est pas
   un rouge atténué »). `composants.md` l'écrit noir sur blanc.

**Diff appliqué** sur [05-design.md § 5](../../docs/05-design.md) : l'alerte porte quatre niveaux
(information, attente, danger, enregistré), et le § 3.1 précise que les 36 px du contrôle sur
poste sont un dessin dont la zone interactive garde 44 px.

## R-20 : Les icônes sont dessinées en SVG dans les composants, aucune bibliothèque

**Décision.** La tranche emploie moins d'une dizaine d'icônes (coche, point, lien barré, barres de
lien, menu, retour, recherche, fermer, chevron) : elles sont des `<svg>` en ligne dans les
composants, dessinées d'après la planche 13, qui les porte déjà en SVG. Aucune bibliothèque
d'icônes, donc aucune attribution à renseigner : le blanc laissé sur l'artboard US4 se ferme
ainsi, et l'écran « à propos » n'attribue que les polices.

**Motif.** Poids, et une dépendance de moins à peser à chaque écran. Une tranche qui aura besoin
d'un jeu d'icônes plus large le pèsera contre son budget avant de le choisir (constitution XV).

## R-21 : Le thème, mémorisé sur l'appareil par la plateforme, forcé par attribut

**Décision.** `useTheme()` : au démarrage, lit `stockage.lire('theme')` ; absent, aucun attribut
n'est posé et `prefers-color-scheme` décide ; présent (`light` ou `dark`), l'attribut `data-theme`
est posé sur `<html>`. Le sélecteur de la coquille écrit par `stockage.ecrire`. P-05 force
l'attribut. Aucune valeur côté serveur.

## R-22 : Le nom du produit en un seul endroit, l'icône générée

**Décision.** `web/app/core/produit.ts` exporte `NOM = 'Nelo'`, `NOM_COURT = 'Nelo'` et `VERSION`
(lue de `package.json`) ; le manifeste, le `<title>`, l'écran « à propos » et l'icône (R-08) les
lisent. Q2 reste ouverte ; un renommage touche une ligne.

## Diffs sur les documents projet

| Fichier | Quoi | Statut |
|---|---|---|
| `03-api.md § 1.9` | `administrateur` sur chaque établissement du contexte | **Appliqué à `specify`** |
| `03-api.md § 1.9` | `country_pack.vocabulaire` dans le contexte : le § 1.9 veut une seule requête, et le client résout les libellés par le pack ([data-model.md § 1](data-model.md)) | **Appliqué** |
| `01-stack.md § 1.2` | Back-office : rendu serveur par défaut, rendu client par règle de route quand la mesure le permet ; Q4 tranchée (R-06) | **Appliqué** |
| `01-stack.md § 7` | P-06 : « aucune littérale d'interface » en cinq règles (R-11) | **Appliqué** |
| `01-stack.md § 3` | La commande de l'interface et l'installation des navigateurs (R-12) | **Appliqué** |
| `docs/design/mesures.css` | Nouveau : hauteurs, rayons, filet, ruptures, pulsation (R-17) | **Appliqué** |
| `05-design.md § 0, § 3.1, § 5` | Rang de `mesures.css` ; 36 px dessinés, 44 px interactifs ; quatre niveaux d'alerte (R-17, R-19) | **Appliqué** |
| `progress.md` | Q1 et Q4 tranchées, Q2 provisoire, **Q29 ouverte** (le plafond et les polices, R-16) | **À la fin de session** |

Chacun dérive du corpus ou d'une mesure ; aucun n'est un choix produit, **sauf Q29**, qui touche
la constitution et attend l'utilisateur. Ils sont appliqués selon
l'arbitrage délégué du 2026-09-14 et tracés dans le journal.

## Écarts d'implémentation

*Ce que `implement` a trouvé et que le plan n'avait pas prévu. Chaque ligne dit l'écart, sa cause,
et ce qui a été fait. Aucun ne touche le contrat.*

| # | Écart | Cause | Ce qui a été fait |
|---|---|---|---|
| E-01 | `sharp` n'est pas installé ; les icônes sont dessinées par `web/scripts/icones.mjs` avec `opentype.js` 2.0.0 (MIT) et un encodeur PNG en Node pur | `sharp` tire `@img/sharp-libvips-*`, sous LGPL-3.0-or-later, refusée par P-07 (T007). Rastériser par Chromium aurait fait dépendre chaque construction d'un navigateur | Le script lit le glyphe de la lettre dans le `.woff` d'Archivo 700, le remplit (règle non nulle, suréchantillonnage 4 × 4) aux couleurs de `tokens.json`, et encode le PNG par `zlib` ; quatre fichiers en 0,2 s, sans réseau |
| E-02 | P-07 admet BlueOak-1.0.0 et CC0-1.0, et CC-BY-4.0 pour `caniuse-lite` seul | Nuxt, nitropack, workbox-build et browserslist les tirent ; aucune n'est un copyleft, que [01-stack.md § 9](../../docs/01-stack.md) refuse | Liste élargie dans `p07_licences.py`, exception nommée pour `caniuse-lite` (donnée de construction, ne voyage pas) ; ligne « Autorisé » de § 9 complétée |
| E-03 | Les commandes s'écrivent `pnpm --filter nelo-web`, pas `--filter web` | Le filtre de `pnpm` porte sur le nom du paquet, que T002 fixe à `nelo-web` | `verifier.sh` et le quickstart emploient `--filter nelo-web` |
| E-04 | `web/ecrans.json` est un objet `{ plafondsDuCorpus, ecrans }` et non une liste | JSON n'a pas de commentaire, et R-16 veut les plafonds du corpus recopiés dans le fichier | Le lecteur `core/ecrans.ts` lit `ecrans` ; la forme de chaque entrée est celle de data-model § 5 |
| E-05 | `openapi-typescript` voit TypeScript 6.0.3 au lieu de 5.9.3 | Le pair est résolu par l'espace de travail une fois `web/` installé | P-03 régénère le contrat sans écart : aucune conséquence |
| E-06 | Aucun des sept fichiers de police servis ne porte U+202F (Archivo n'a que U+2009, Public Sans et Plex Mono ni l'un ni l'autre) | Le sous-ensemble latin de Fontsource 5.3.0 couvre la plage mais pas le glyphe ; R-07 ne pouvait pas le lire | Le cas prévu par R-07 : la police de repli (`system-ui`, `ui-monospace`) rend ce seul glyphe ; `polices.test.ts` le signale en avertissement à chaque exécution. La demande de la revue visuelle (« les sous-ensembles doivent la conserver ») n'est pas tenue par les fichiers ; la tenir exigerait de modifier les polices |
| E-07 | L'application de test écoute sur 4310, le serveur de développement de P-05 sur 4311 | Le port 3000 est pris sur le poste par un autre projet ; une porte qui interroge le mauvais serveur passerait à tort | `NELO_WEB_PORT` et `NELO_WEB_PORT_DEV` les changent ; `playwright.config.ts` et `p-05.sh` les lisent |
| E-08 | Les trois polices du premier affichage sont préchargées par `app.vue` et non par `app.head.link` de `nuxt.config.ts` | Leur adresse porte l'empreinte de la construction, inconnue au moment de la configuration | `import …woff2?url` puis `useHead` ; la feuille de style et le préchargement désignent le même fichier |
| E-09 | Pas de `core/plateforme/test.ts` exposé par une variable de fenêtre ; `core/plateforme/indisponible.ts` sert le rendu serveur | Les tests e2e tournent sur la construction de production, où une porte d'entrée de test n'a pas sa place ; le navigateur se pilote lui-même | Les tests e2e emploient `context.setOffline()` et un script d'initialisation qui simule `navigator.connection` : c'est `web.ts` lui-même qui est éprouvé. Le rendu serveur reçoit une plateforme où tout est indisponible, sans lever |
| E-10 | La devise du contexte porte `symbole` | T015 exige un symbole venu du pack ; le contrat n'en avait pas, et l'écrire côté client serait une littérale de pays | Diff appliqué sur [03-api.md § 1.9](../../docs/03-api.md) et sur le schéma `Devise` de `modules/shared/contexte.py` |
| E-11 | La logique du thème vit dans `core/theme.ts`, `useTheme` ne fait que l'envelopper | Un composable Nuxt ne s'exécute pas dans Vitest en Node sans DOM simulé, que R-14 écarte | `theme.test.ts` éprouve `lireTheme`, `ecrireTheme`, `attributTheme` sur un stockage de test |
| E-12 | `@types/node` 24.13.5 (MIT) entre dans les dépendances de développement, et `web/tsconfig.tests.json` fait vérifier les tests et les configurations | `nuxt typecheck` ne voyait que `app/` : les tests et `playwright.config.ts` n'étaient jamais vérifiés | Une référence de projet de plus dans `web/tsconfig.json` |
| E-13 | La plateforme expose `apparence` (l'appareil demande-t-il le sombre ?) et le thème pose toujours `data-theme` côté client, `light` ou `dark` | `theme.css` ne réagit qu'à `[data-theme]`, jamais à `prefers-color-scheme` ; R-21 supposait le contraire, et le fichier ne se réécrit pas | `attributTheme(theme, appareilSombre)` ; au rendu serveur aucun attribut, le client le pose au montage. Une personne dont l'appareil est en sombre voit un premier affichage clair le temps de l'hydratation |
| E-14 | `?persona=` et `?pack=fictif` fonctionnent aussi sur la construction, pas seulement en développement | P-05, P-10 et les tests e2e parcourent la construction ; la source entière est de démonstration et T1a la remplace par la route du contexte | `SourceDemonstration` lit les deux paramètres sans condition de mode ; aucune donnée réelle n'est exposée |
| E-15 | La pastille d'état reçoit un **code d'état métier** (`PAYE`, `IMPAYE`, …), et non une voix et un mot | Le contrat de § 1 laissait l'appelant choisir la voix ; FR-005 réserve le rouge à deux états, ce qu'un choix libre ne garantit pas | Registre `ETATS_METIER` dans `core/composants/etats.ts` : la voix et la clé se déduisent du code, seuls `IMPAYE` et `NON_JUSTIFIE` parlent en rouge, par construction |
| E-16 | T042, T043, T045 et T046 (tests, personas, registre, `composer`) sont faites avant T035 | La section « Coquille » de la page de style montre les quatre situations, qui se composent depuis les personas | L'ordre à l'intérieur de la phase 3 change ; les tests d'US3 ont échoué avant d'exister, puis passé |
| E-17 | Les énumérations vivent dans `core/composants/etats.ts` ; chaque composant les réexporte par `ETATS_COMPOSANT` | Un test Vitest en Node ne lit pas un `.vue`, et Nuxt enregistrerait comme composant tout `.ts` posé dans `components/` | `composants-etats.test.ts` compare le document, le registre et la réexportation de chaque fichier |
| E-18 | La navigation mono-domaine liste des **entrées** (« Appel du jour », « Absences et retards », « Sanctions »), que le registre associe à l'objet de chaque capacité | FR-023 et l'artboard US3 ; le data-model ne décrivait que des domaines | `Domaine.entrees` ; les écrans autres que l'appel du jour sont des vues `?vue=` de `/d/[domaine]`, qui disent arriver avec leur tranche |
| E-19 | La pastille `IMPAYE` s'affiche « En retard », pas « Impayé » | [05-design.md § 8.1](../../docs/05-design.md) range « impayé » parmi les mots que l'on ne dit jamais ; la planche 13 l'employait | Le code et la voix rouge restent (FR-005) ; le mot est l'état `en_retard` de l'échéance ([02-domaine.md § 16](../../docs/02-domaine.md)) ; `lexique.md` le trace |
| E-20 | L'état du réseau n'est suivi qu'une fois l'hydratation terminée (`onNuxtReady`) | P-05 a relevé un désaccord d'hydratation : une page asynchrone s'hydrate après `app:mounted`, et Chromium sans tête annonce une connexion lente | Le greffon `reseau.client.ts` attend `onNuxtReady` ; le rendu serveur et la première hydratation disent tous deux « lien bon » |
| E-21 | Les projets Chromium de Playwright emploient `channel: 'chromium'` | Le navigateur complet, sans tête, est plus fidèle que la coquille sans tête, et le poste n'avait pas à télécharger les deux | `playwright.config.ts` |
| E-22 | `SourceDemonstration` et `langueInitiale` sont couvertes par `contexte-source.test.ts`, écrit après T047 ; le repli de langue est prouvé en test unitaire, pas en e2e | Aucun persona n'a une langue hors du pack, et en créer un pour le seul test e2e aurait ajouté une donnée sans usage | Le test unitaire éprouve le repli sur la première langue du pack, pack réordonné compris |
