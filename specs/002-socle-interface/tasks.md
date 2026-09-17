# Tâches : Le socle d'interface (T0b)

**Entrée** : les documents de conception de `specs/002-socle-interface/` : [plan.md](plan.md),
[spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/interfaces-client.md](contracts/interfaces-client.md), [quickstart.md](quickstart.md),
et les artboards validés de [design/](design/).

**Tests** : la spécification les exige. Chaque écran s'atteint dans un vrai navigateur (P-05),
aucune littérale d'interface (P-06), aucun dépassement de budget (P-10), chaque porte a son test
négatif (US7), et « monter un composant dans un test ne prouve pas qu'une page s'atteint ». Les
tâches de test sont donc livrées **avant** l'implémentation de chaque story, et doivent échouer
avant qu'elle n'existe.

**Organisation** : par user story, dans l'ordre de priorité de la spec. La règle de T0a traverse
toutes les phases : **les portes se construisent avec ce qu'elles vérifient**, et
`scripts/verifier.sh` reste vert à chaque commit. Les documents de design (`composants.md`,
`mouvement.md`, `lexique.md`) s'écrivent avec le code qu'ils décrivent, jamais après.

## Format : `[ID] [P?] [Story] Description`

- **[P]** : parallélisable, fichiers différents, aucune dépendance sur une tâche inachevée
- **[Story]** : la user story servie (US1 à US8)
- Chaque description porte son chemin exact, relatif à la racine du dépôt

## Conventions de chemins

Celles de [plan.md](plan.md) « Structure du projet » : `web/app/{assets,components/canon,
composables,core,pages,plugins,sw}/`, `web/tests/{unit,e2e,portes}/`, `web/scripts/`,
`scripts/portes/`, `modules/shared/`, `docs/design/`. Tout est en français, accents compris dans
les commentaires, les clés i18n et les messages ; les identifiants TypeScript restent sans accent.
**Aucun tiret cadratin**, nulle part.

---

## Phase 1 : Mise en place (infrastructure partagée)

**But** : `web/` existe, construit, est verrouillé, passe P-02 et P-07, et la commande de
vérification le connaît.

- [X] T001 Créer l'arborescence de `web/` : `web/app/assets/css/`, `web/app/components/canon/`, `web/app/composables/`, `web/app/core/{contexte,composition,saisie,plateforme,i18n,pack,demonstration/personas}/`, `web/app/pages/`, `web/app/plugins/`, `web/app/sw/`, `web/public/licences/`, `web/scripts/`, `web/tests/{unit,e2e,portes}/`, avec un `.gitkeep` par dossier vide
- [X] T002 Écrire `web/package.json` : `name` `nelo-web`, `private`, `type: module`, `packageManager` `pnpm@10.26.2`, dépendances **épinglées exactement** selon [research.md R-01, R-07, R-08, R-14](research.md) (`nuxt` 4.5.2, `vue` 3.5.42, `@vite-pwa/nuxt` 1.1.1, `workbox-precaching` 7.4.1, `@fontsource/archivo`, `@fontsource/public-sans`, `@fontsource/ibm-plex-mono` 5.3.0 ; dev : `typescript` 6.0.3, `vue-tsc` 3.3.11, `tailwindcss` et `@tailwindcss/vite` 4.3.3, `@playwright/test` 1.63.0, `vitest` 5.0.1, `@axe-core/playwright` 4.13.0, `sharp` à sa dernière version stable, `@vue/compiler-sfc` 3.5.42), scripts `dev`, `build`, `preview`, `icones`, `typecheck`, `test:unit`, `test:e2e`, `portes:p05`, `portes:p10` selon [quickstart.md](quickstart.md) ; `engines.node` `24.18.1`
- [X] T003 [P] Écrire `web/nuxt.config.ts` minimal : `compatibilityDate`, `css` (les quatre fichiers de `app/assets/css/`), `vite.plugins` avec `@tailwindcss/vite`, `nitro.compressPublicAssets: true`, `app.head` (`lang` posé plus tard par le contexte, `viewport`), `typescript.strict` ; `web/tsconfig.json` étendant `.nuxt/tsconfig.json` ; `web/vitest.config.ts` (environnement `node`, `include: ['tests/unit/**/*.test.ts']`) ; `web/playwright.config.ts` (projets `chromium` et `webkit`, `testDir: 'tests'`, `webServer` sur `node .output/server/index.mjs` port 3000, `use.serviceWorkers: 'block'` pour le projet `p10`)
- [X] T004 [P] Écrire `web/app/app.vue` (un `<NuxtPage />` dans un `<main>` avec `id="principal"`) et `web/app/pages/index.vue` vide (un titre par clé i18n, posée à T020) ; écrire `web/app/core/produit.ts` (`NOM`, `NOM_COURT`, `VERSION` lue de `package.json`) selon [research.md R-22](research.md)
- [ ] T005 Exécuter `pnpm install` à la racine (le lockfile unique s'étend à `web/`), puis `pnpm exec playwright install chromium webkit` **une fois avec réseau** ; vérifier `pnpm --filter web build` passe et `node .output/server/index.mjs` sert `/` ; commiter `pnpm-lock.yaml`
- [X] T006 [P] Mettre à jour `.gitignore` : `web/.nuxt/`, `web/.output/`, `web/public/icones/`, `web/test-results/`, `web/playwright-report/` ; **ne pas** ignorer `web/public/licences/`
- [X] T007 Vérifier que P-02 et P-07 couvrent `web/` sans modification (`scripts/portes/p-02.sh` inspecte déjà `web/package.json`, `pnpm licenses` voit l'espace de travail) et que `scripts/verifier.sh` passe encore ; si `sharp` ou une dépendance transitive porte une licence hors liste, la remplacer, jamais élargir la liste sans le tracer dans [research.md](research.md)
- [X] T008 Écrire `web/ecrans.json` selon [data-model.md § 5](data-model.md) avec `budgetKo`, `budgetPolicesKo` (45 pour les écrans budgétés, [research.md R-16](research.md)), `personas` et `developpement`, et `web/app/core/ecrans.ts` (lecteur typé, validation : `budgetKo` entier positif ou `null`, `developpement` implique `budgetKo: null`) ; test `web/tests/unit/ecrans.test.ts`
- [X] T009 Étendre `scripts/verifier.sh` de trois étapes après le reparcours sous suspension : `etape "typecheck" pnpm --filter web typecheck`, `etape "vitest" pnpm --filter web test:unit`, `etape "construction" pnpm --filter web build` ; vérifier que la commande passe en une invocation

---

## Phase 2 : Fondations (prérequis bloquants)

**But** : le thème et les mesures copiés et passés à Tailwind, les polices servies, l'interface de
plateforme, les libellés et le pack, le type du contexte dans le contrat, P-06 et P-05 vivantes sur
une page vide. Sans cela, aucune story ne peut être testée.

**⚠️ CRITIQUE** : aucune story ne commence avant la fin de cette phase.

### Le thème, les mesures, Tailwind, les polices

- [X] T010 Copier `docs/design/theme.css` vers `web/app/assets/css/theme.css` et `docs/design/mesures.css` vers `web/app/assets/css/mesures.css`, **sans une modification** ; écrire `web/tests/unit/copies-design.test.ts` qui compare les deux paires octet à octet
- [X] T011 [P] Écrire `web/app/assets/css/jetons.css` : `@import "tailwindcss"` puis `@theme inline` qui mappe **par référence** chaque jeton de `theme.css` (`--color-bg: var(--bg)`, `--color-surface`, `--color-surface-sunken`, `--color-border`, `--color-border-strong`, `--color-text`, `--color-text-muted`, `--color-primary`, `--color-primary-hover`, `--color-primary-soft`, `--color-primary-ink`, `--color-accent*`, `--color-danger*`, `--color-success*`, `--color-board`) et de `mesures.css` (`--radius-carte: var(--rayon-carte)`, …), les deux points de rupture `--breakpoint-md: 768px` et `--breakpoint-xl: 1200px` (seule exception, [research.md R-17](research.md)), et les familles `--font-titres`, `--font-texte`, `--font-mono` ; test `web/tests/unit/jetons.test.ts` : aucune valeur de couleur dans le fichier, et les ruptures égales à celles de `mesures.css`
- [X] T012 [P] Écrire `web/app/assets/css/polices.css` : `@font-face` pour Public Sans 400 et 500, Archivo 700 (préchargées via `app.head.link` dans `nuxt.config.ts`), Archivo 500 et 600, Public Sans 600, IBM Plex Mono 500 (à la demande), tous `font-display: swap`, fichiers importés depuis `@fontsource/*` ([research.md R-07](research.md)) ; copier les trois `LICENSE` de fontsource dans `web/public/licences/{archivo,public-sans,ibm-plex-mono}.txt` ; écrire `web/tests/unit/polices.test.ts` qui vérifie que chaque fichier `woff2` référencé existe et, avec `fonttools` via `uvx` si disponible, qu'il porte le glyphe U+202F (sinon le test l'indique en avertissement, jamais en silence)

### La plateforme, les libellés, le pack, le thème

- [X] T013 [P] Écrire `web/app/core/plateforme/plateforme.ts` (l'interface `Plateforme` de [contracts § 5](contracts/interfaces-client.md)), `web/app/core/plateforme/web.ts` (l'unique implémentation : `navigator.onLine` + `navigator.connection.effectiveType` pour `faible`, `localStorage` protégé par try/catch, `getUserMedia`, `Notification`), `web/app/core/plateforme/test.ts` (une implémentation pilotable exposée **seulement** si `import.meta.dev || import.meta.env.MODE === 'test'`, lue sur `window.__nelo_plateforme_test`), `web/app/plugins/plateforme.client.ts` (fournit l'une ou l'autre), `web/app/composables/usePlateforme.ts` ; test `web/tests/unit/plateforme-web.test.ts` sur les réponses « indisponible » (aucune exception, `capturer()` rend `null`)
- [X] T014 [P] Écrire `web/app/core/i18n/fr.json` et `web/app/core/i18n/en.json` avec les premières clés (`coquille.*`, `ruban.*`, `apropos.*`, `style.*`, `etat.*`, `canal.*`), **les deux fichiers dans le même commit**, `web/app/core/i18n/libelles.ts` (`t(cle, params)` avec `{n}`, chaîne vide et `console.warn` en développement si absente) et `web/app/composables/useLibelles.ts` (langue réactive) ; test `web/tests/unit/libelles.test.ts` : mêmes clés dans les deux fichiers, paramètres, clé absente jamais rendue brute
- [X] T015 [P] Écrire `web/app/core/demonstration/pack-demonstration.json` (pays fictif, devise `{ code, exposant: 0 }` avec symbole « F », langues `["fr","en"]`, `vocabulaire` pour les dix-sept codes de [02-domaine.md § 15](../../docs/02-domaine.md) en `fr` et `en`) et `pack-fictif.json` (même forme, exposant 2, symbole différent, « classe » dit autrement) ; écrire `web/app/core/pack/pack.ts` (`libelle(code)`, `montant(entier)` avec U+202F et symbole, `note(valeur, bareme)` avec virgule) et `web/app/composables/usePack.ts` ; test `web/tests/unit/pack.test.ts` : `145000` → `145 000 F`, `"14.25"` + `"20"` → `14,25 / 20`, exposant 2 → `1 450,00`, `libelle('CLASSE')` selon le pack et la langue
- [X] T016 [P] Écrire `web/app/composables/useTheme.ts` selon [contracts § 7](contracts/interfaces-client.md) et [research.md R-21](research.md) : lit `stockage.lire('theme')`, pose ou retire `data-theme` sur `<html>`, `forcer()` écrit par la plateforme ; test `web/tests/unit/theme.test.ts` sur une plateforme de test

### Le type du contexte, dans le contrat

- [X] T017 Écrire `modules/shared/contexte.py` : les modèles Pydantic de [data-model.md § 1](data-model.md) (`ContexteCapacites`, `Compte`, `EtablissementContexte`, `Administrateur`, `AnneeContexte`, `CapaciteContexte`, `AccesNominatif`, `CountryPackContexte` avec `vocabulaire`, `AlerteContexte`), validateurs (`code` de capacité `domaine.objet.verbe`, `etablissement_actif` et `annee_active` cohérents, `langues` non vide), aucune littérale de pays ; exporter dans `modules/shared/__init__.py`
- [X] T018 Étendre `api/contrat.py` pour enregistrer `ContexteCapacites` et ses sous-modèles dans `components.schemas` du document OpenAPI sans route ; régénérer `contrat/openapi.json` et `contrat/client.d.ts` (`python -m api.contrat` puis `pnpm contrat:client`) ; écrire `tests/portes/test_contexte_au_contrat.py` (le schéma est présent, `client.d.ts` porte `ContexteCapacites`) ; vérifier P-03 et `pytest` passent
- [X] T019 [P] Écrire `web/app/core/contexte/types.ts` (réexport de `components['schemas']['ContexteCapacites']` et des sous-types depuis `../../../../contrat/client.d.ts`) et `web/app/core/contexte/source.ts` (`SourceContexte`)

### P-06 et P-05 sur une page vide

- [X] T020 Écrire `scripts/portes/p06_interface.mjs` selon [research.md R-11](research.md) : règle 1 chaînes en dur (nœuds texte avec une lettre et attributs `placeholder`, `title`, `alt`, `aria-label`, `aria-description`, `label` statiques dans les `.vue` de `web/app/`, via `@vue/compiler-sfc`), règle 2 clés `fr` = `en` et clés appelées par `t()` existantes, règle 3 couleurs littérales (`#hex`, `rgb(`, `hsl(`, `oklch(`, noms de couleur CSS) hors `assets/css/theme.css` et `mesures.css`, règle 4 appels de plateforme hors `core/plateforme/web*.ts`, `core/plateforme/test.ts` et `app/sw/`, règle 5 identifiants `role` hors attributs ARIA ; plus la comparaison octet à octet des deux copies de design ; sortie `PORTE P-06 : n fichiers, n clés, 0 littérale` ou `PORTE P-06 ÉCHOUÉE : <règle> <fichier>:<ligne>` ; écrire `scripts/portes/p-06.sh` ; écrire `web/tests/portes/regles-p06.test.ts` avec un cas positif et un cas négatif par règle sur des extraits en mémoire
- [X] T021 [P] Écrire `web/tests/portes/p05.spec.ts` : lit `web/ecrans.json`, pour chaque écran × persona × thème (`light`, `dark` par `data-theme` posé avant navigation) ouvre la route, attend `main#principal` visible, échoue sur `pageerror` ou `console.error` en nommant écran, moteur, thème ; les écrans `developpement: true` sont ouverts sur `nuxt dev` (port 3001, lancé par le script) ; écrire `scripts/portes/p-05.sh` (lance `pnpm --filter web portes:p05` sur `.output`, démarre et arrête `nuxt dev` pour la page de style, imprime `PORTE P-05 : n écrans × 2 moteurs × 2 thèmes`) ; ajouter `porte P-06` (avant P-01) et `porte P-05` (après la construction) dans `scripts/verifier.sh` ; vérifier que la commande passe avec la page vide

**Point de contrôle** : `scripts/verifier.sh` passe, neuf portes, sur une application vide qui
sert le thème.

---

## Phase 3 : User Story 1, la page de style montre les quatorze composants (Priorité : P1) 🎯 MVP

**But** : les quatorze composants existent dans tous leurs états, sur des données de démonstration
du primaire, et une page de style de développement les montre chacun deux fois, clair et sombre.

**Test indépendant** : ouvrir `/style`, compter ; `cmp` du thème ; P-06 à zéro ; `/style` absente
de la construction.

### Tests pour la User Story 1

- [X] T022 [P] [US1] Écrire `web/tests/unit/composants-etats.test.ts` : pour chaque composant de `web/app/components/canon/`, les énumérations exportées (`VARIANTES`, `ETATS`, `VOIX`, …) correspondent **exactement** aux états listés dans `docs/design/composants.md` (parseur du tableau markdown) ; échoue tant que le document ou un composant manque
- [X] T023 [P] [US1] Écrire `web/tests/e2e/style.spec.ts` : `/style` (serveur de développement) porte quatorze sections `section[data-composant]`, chaque état apparaît dans un conteneur `[data-theme="light"]` et un `[data-theme="dark"]` côte à côte ; une image de `/style` n'est pas nécessaire ; vérifier que `.output` ne contient aucune route `style`
- [X] T024 [P] [US1] Écrire `web/tests/e2e/voix.spec.ts` : sur `/style`, aucune pastille, alerte ou ruban ne porte la couleur seule (chaque état a un `data-forme` et un texte non vide), les états d'attente ont `data-voix="ocre"`, seuls `IMPAYE` et `NON_JUSTIFIE` parmi les pastilles de démonstration ont `data-voix="rouge"`

### Implémentation de la User Story 1

- [X] T025 [US1] Écrire `docs/design/composants.md` : les quatorze composants, chacun avec ses états, sa forme, sa voix et ses mots (clés), d'après la planche 13, [05-design.md § 5](../../docs/05-design.md) et [contracts § 1](contracts/interfaces-client.md) ; y tracer les trois écarts de [research.md R-19](research.md) (Validé en réussite, canal « En ligne », champ en erreur en voix danger) et le seuil cinq / six ; le document est la source que T022 lit
- [X] T026 [P] [US1] Écrire `web/app/core/demonstration/donnees.ts` : élèves de CM2 A (noms fictifs, matricules `ELV-2026-0xxx`), reçus `REC-000xxx`, indicateurs (encaissé, reste à payer, effectif), lignes de tableau, tous en formats de [03-api.md § 1.4](../../docs/03-api.md) (montants entiers, notes en chaîne)
- [X] T027 [P] [US1] Écrire `web/app/components/canon/Bouton.vue` (`VARIANTES`, `inactif: { raison: cle }` affichée sous le bouton, `min-height: var(--cible)`, focus visible, aucun état au survol qui révèle) et `web/app/components/canon/Interrupteur.vue` (`modelValue`, `inactif`, rôle `switch`)
- [X] T028 [P] [US1] Écrire `web/app/components/canon/Champ.vue` : `TYPES` texte, nombre (clavier numérique par `inputmode`), choix (`<select>`), case ; `ETATS` repos, focus, erreur (voix danger, icône SVG en ligne, message par clé), inactif ; `aide`, `unite` ; étiquette toujours visible au-dessus
- [X] T029 [P] [US1] Écrire `web/app/components/canon/PastilleEtat.vue` (`VOIX`, `FORMES`, `mot` obligatoire, `data-voix`, `data-forme`, contour ouvert en pointillé pour `contour`) et `web/app/components/canon/PastilleCanal.vue` (`CANAUX` `EN_LIGNE`, `WHATSAPP`, `SMS`, `PAPIER`, SMS mis en avant, `cout` mis en forme par `usePack().montant`)
- [X] T030 [P] [US1] Écrire `web/app/components/canon/Recherche.vue` (`ETATS`, `portee` par clé affichée dans le champ, raccourci affiché seulement en contexte `poste`), `web/app/components/canon/Avatar.vue` (initiales ou photo, `TAILLES`, jamais une couleur seule : les initiales sont toujours rendues sous la photo absente) et `web/app/components/canon/FilAriane.vue` (`segments`, dernier non cliquable, `aria-current`)
- [X] T031 [P] [US1] Écrire `web/app/components/canon/Onglets.vue` (rôle `tablist`, `compte` par onglet, clavier flèches), `web/app/components/canon/CarteIndicateur.vue` (chiffre clé Archivo tabulaire, `SENS`, variation avec signe et mot) et `web/app/components/canon/Alerte.vue` (`NIVEAUX` information, attente, danger, enregistre ; une icône SVG par niveau ; `action` optionnelle ; jamais deux niveaux)
- [X] T032 [P] [US1] Écrire `web/app/components/canon/Tableau.vue` et `web/app/components/canon/LigneTableau.vue` : en-tête sur `--surface-sunken`, colonnes `mono` en IBM Plex Mono tabulaire, pastille dans une cellule ; sous `--rupture-deux-colonnes`, chaque ligne devient une carte avec le libellé de colonne **au-dessus** de la valeur (CSS seul, sans second gabarit)
- [X] T033 [P] [US1] Écrire `web/app/components/canon/RubanSaisie.vue` en **présentation seule** : props `etat` (`ETATS`), `dernierEnregistrement`, `enAttente`, `reseau` ; trois formes SVG en ligne (coche, point pulsant par `--pulsation-*`, lien barré) et les barres de lien ; `VOIX` réussite, marque, ocre ; mots par clés `ruban.*` ; `position: sticky; bottom: 0` ; `@media (prefers-reduced-motion: reduce)` arrête la pulsation
- [X] T034 [P] [US1] Écrire `web/app/components/canon/Coquille.vue` en **présentation seule** avec ses sous-composants `CoquilleEntete.vue` (établissement · site, année, sélecteur de langue, sélecteur de thème, avatar), `CoquilleNavigation.vue` (liste à plat ou par familles, barre basse sous 768 px et tiroir depuis un bouton menu selon l'artboard US3, latérale au-dessus), `CoquilleSansCapacite.vue` (titre, texte, administrateur nommé avec téléphone, action « demander mes accès ») ; props typées par `Composition` de [contracts § 4](contracts/interfaces-client.md) ; slot par défaut pour l'écran
- [X] T035 [US1] Écrire `web/app/pages/style.vue` : quatorze sections `data-composant`, chaque état rendu dans deux conteneurs `[data-theme="light"]` et `[data-theme="dark"]` côte à côte en itérant les énumérations exportées et `donnees.ts` ; un bloc `pages:extend` dans `nuxt.config.ts` retire la page hors développement ; ajouter `style` à `web/ecrans.json` (`developpement: true`) ; vérifier T022 à T024 et P-05 passent

**Point de contrôle** : la page de style montre les quatorze composants dans tous leurs états, en
clair et en sombre ; c'est le premier critère de fin de la roadmap.

---

## Phase 4 : User Story 2, le ruban dit trois choses et ne bloque jamais (Priorité : P1)

**But** : l'état du ruban est dérivé du réseau et d'une source de démonstration ; la saisie
continue sous les trois états ; le retour du lien vide la file sans geste.

**Test indépendant** : `pnpm --filter web test:e2e -- ruban` avec la plateforme de test.

### Tests pour la User Story 2

- [X] T036 [P] [US2] Écrire `web/tests/unit/etat-ruban.test.ts` : la table de [data-model.md § 3](data-model.md) ligne par ligne, `dernierEnregistrement: null` → clé `ruban.aucun_enregistrement`, compte exact au-delà de 99, `hors_ligne` avec zéro en attente, aucune voix rouge possible (type)
- [X] T037 [P] [US2] Écrire `web/tests/e2e/ruban.spec.ts` : sur `/d/vie_scolaire?persona=un-domaine`, plateforme de test à `bon` → « Tout est enregistré » ; à `faible` avec deux saisies → « Envoi de 2 saisies », point pulsant ; à `absent` → « Hors ligne », quatre saisies tapées dans le champ → compte 4, **aucun** élément `disabled` ni `aria-disabled` ajouté, champ toujours éditable ; retour à `bon` → compte 0 et « Tout est enregistré » en moins de deux secondes sans clic ; `prefers-reduced-motion` émulé → `animation-name: none` sur le point, forme et mot présents ; le ruban reste visible après défilement et ne recouvre pas le bouton principal

### Implémentation de la User Story 2

- [X] T038 [US2] Écrire `web/app/core/saisie/etat-ruban.ts` (fonction pure `deriverEtatRuban(reseau, enAttente, dernierEnregistrement)`) selon [data-model.md § 3](data-model.md)
- [X] T039 [US2] Écrire `web/app/composables/useSaisieDemonstration.ts` : `saisir(valeur)` incrémente `enAttente`, un lot part après un délai quand `reseau ≠ absent` et pose `dernierEnregistrement`, reprise automatique à `surChangement` de la plateforme ([research.md R-04](research.md)) ; brancher `RubanSaisie.vue` sur `deriverEtatRuban` et `usePlateforme().reseau`
- [X] T040 [US2] Écrire `web/app/pages/d/[domaine].vue` : l'écran de démonstration d'un domaine (pour `vie_scolaire` : « Appel du jour » de l'artboard US3, un `CanonChamp` de saisie branché sur `useSaisieDemonstration`, un `CanonBouton` principal pleine largeur en bas, le `CanonRubanSaisie` ancré) ; contexte tactile `classe` fourni ; ajouter `domaine` à `web/ecrans.json` (budget 120, `budgetPolicesKo` 45)
- [X] T041 [US2] Écrire `docs/design/mouvement.md` : la pulsation (`--pulsation-duree`, `--pulsation-courbe`), la règle `prefers-reduced-motion`, et « aucune autre durée n'existe ; une durée nouvelle entre dans `mesures.css` avant d'entrer dans un composant »

**Point de contrôle** : le composant le plus important de la tranche informe et ne bloque jamais.

---

## Phase 5 : User Story 3, la coquille se compose depuis le contexte (Priorité : P1)

**But** : quatre personas, quatre situations, aucun rôle nulle part.

**Test indépendant** : `test:unit -- composition` et `test:e2e -- coquille`.

### Tests pour la User Story 3

- [X] T042 [P] [US3] Écrire `web/tests/unit/composition.test.ts` : `domaineDe`, `composer` sur les quatre personas (situation, domaines dans l'ordre du registre, familles non vides seulement), seuil cinq → `MULTI_PLAT` et six → `MULTI_FAMILLES`, domaine inconnu ignoré, accueil mono-domaine = route du domaine
- [X] T043 [P] [US3] Écrire `web/tests/unit/personas.test.ts` : chaque JSON de `web/app/core/demonstration/personas/` est valide contre le schéma `ContexteCapacites` de `contrat/openapi.json` (validateur JSON Schema minimal écrit dans le test ou `ajv` si sa licence est autorisée), aucun ne porte une clé `role`
- [X] T044 [P] [US3] Écrire `web/tests/e2e/coquille.spec.ts` : à 390 et 1200 px, `?persona=un-domaine` → l'accueil est l'écran du domaine, trois entrées, aucune famille ; `cinq-domaines` → tableau composé de cinq blocs, navigation à plat de cinq ; `sept-domaines` → familles présentes, aucune famille vide, bouton menu à 390 px ouvre le tiroir ; `aucune-capacite` → aucune navigation, l'administrateur « M. Konan Bertin » et son téléphone visibles, bouton « Demander mes accès » ; pour tous : aucun élément `[aria-disabled]` ni `.grise` dans la navigation ; l'alerte `BUDGET_SMS_BAS` rendue en `data-niveau="attente"` ; en-tête avec établissement, site, année, langue, avatar

### Implémentation de la User Story 3

- [X] T045 [P] [US3] Écrire les quatre personas `web/app/core/demonstration/personas/{un-domaine,cinq-domaines,sept-domaines,aucune-capacite}.json` selon [data-model.md § 7](data-model.md), chacun un `ContexteCapacites` complet avec l'administrateur, le pack de démonstration, l'année active et, pour deux d'entre eux, l'alerte
- [X] T046 [P] [US3] Écrire `web/app/core/composition/registre.ts` (domaines et familles de [data-model.md § 2](data-model.md), clés de libellé, ordre, routes ; **aucun rôle**), `web/app/core/composition/situation.ts` (`SITUATIONS`) et `web/app/core/composition/composer.ts` (`domaineDe`, `composer`)
- [X] T047 [US3] Écrire `web/app/core/contexte/demonstration.ts` (`SourceDemonstration` : persona par `?persona=` en développement, `un-domaine` sinon), `web/app/plugins/contexte.ts` (charge le contexte avant le rendu, `useState`), `web/app/composables/useContexte.ts` ; poser `lang` sur `<html>` depuis `compte.langue`
- [X] T048 [US3] Brancher `Coquille.vue` sur `composer(useContexte())` dans `web/app/app.vue`, rendre `CoquilleSansCapacite` quand la situation l'exige, les alertes du contexte par `CanonAlerte` (gravité `ALERTE` → attente, `CRITIQUE` → danger seulement si le type est un impayé ou une absence non justifiée, sinon attente ; inconnue → information) ; ajouter à `en.json` et `fr.json` les clés de domaines et de familles
- [X] T049 [US3] Écrire `web/app/pages/index.vue` : redirection vers la route du domaine en `MONO_DOMAINE`, tableau composé (un `CanonCarteIndicateur` par domaine dans l'ordre du registre, données de démonstration) en multi, rien en `AUCUNE_CAPACITE` (la coquille affiche l'écran) ; ajouter les personas d'`accueil` à `web/ecrans.json` ; vérifier T042 à T044 et P-05 passent

**Point de contrôle** : trois situations composées, aucune liste de rôles dans le code ; la règle 5
de P-06 le garde.

---

## Phase 6 : User Story 4, installable, autonome, une seule plateforme (Priorité : P2)

**But** : manifeste, icônes, service worker mince, mise à jour d'elle-même, « à propos ».

**Test indépendant** : critères d'installabilité dans P-05, parcours à la main du quickstart.

### Tests pour la User Story 4

- [X] T050 [P] [US4] Étendre `web/tests/portes/p05.spec.ts` d'un bloc « installabilité » : `/manifest.webmanifest` répond, `display === 'standalone'`, `name` et `short_name` = `produit.ts`, icônes 192 et 512 (dont une `maskable`) atteignables, `<link rel="apple-touch-icon">` et `<meta name="apple-mobile-web-app-capable">` présents, `theme_color` et `background_color` égaux aux jetons de `docs/design/tokens.json` ; sur Chromium seulement : `navigator.serviceWorker.ready` et `controller` non nul après rechargement
- [X] T051 [P] [US4] Écrire `web/tests/unit/sw.test.ts` : le source `web/app/sw/sw.ts` ne contient ni `fetch` handler, ni `caches.match`, ni `/api/`, ni `indexedDB` ; seulement `precacheAndRoute`, `cleanupOutdatedCaches`, `SKIP_WAITING`
- [X] T052 [P] [US4] Écrire `web/tests/e2e/navigation.spec.ts` : accueil → domaine → `/a-propos` → retour par le bouton de la coquille, zéro navigation complète (`page.on('load')` compté une fois) ; un lien profond `/d/vie_scolaire` ouvert directement se rend dans la coquille

### Implémentation de la User Story 4

- [X] T053 [P] [US4] Écrire `web/scripts/icones.mjs` : SVG typographique (la lettre de `NOM_COURT`, fond `--primary` et encre `--primary-ink` lus dans `docs/design/tokens.json`), rastérisé par `sharp` en `web/public/icones/{192,512,512-maskable,180}.png` ; script `icones` appelé par `predev` et `prebuild`
- [X] T054 [P] [US4] Écrire `web/app/sw/sw.ts` selon [contracts § 8](contracts/interfaces-client.md) : `precacheAndRoute(self.__WB_MANIFEST)`, `cleanupOutdatedCaches()`, message `SKIP_WAITING` ; rien d'autre
- [X] T055 [US4] Configurer `@vite-pwa/nuxt` dans `web/nuxt.config.ts` : `strategies: 'injectManifest'`, `srcDir: 'sw'`, `filename: 'sw.ts'`, `registerType: 'prompt'`, `injectManifest.globPatterns` (`js`, `css`, `html`, `woff2`, `png`), `manifest` généré depuis `tokens.json` et `produit.ts` (`display: standalone`, `lang` selon la langue, icônes de T053, `start_url: '/'`), `pwaAssets` désactivé ; ajouter au `<head>` `apple-touch-icon` et `apple-mobile-web-app-capable`
- [X] T056 [US4] Écrire `web/app/composables/useMiseAJour.ts` : écoute `needRefresh` du plugin, envoie `SKIP_WAITING` **seulement** si `useSaisieDemonstration().enAttente === 0`, sinon attend ; puis `location.reload()` piloté par la plateforme (ajouter `plateforme.application.recharger()` à l'interface, implémentation web) ; aucune chaîne « rechargez la page » nulle part
- [X] T057 [US4] Écrire `web/app/pages/a-propos.vue` : `NOM`, `VERSION`, les trois polices avec lien vers `public/licences/*.txt`, mention « icônes dessinées dans les composants, aucune attribution externe » par clé ; ajouter `a-propos` à `web/ecrans.json` (150, polices 45) ; lien depuis l'en-tête de la coquille
- [ ] T058 [US4] Dérouler le parcours à la main du [quickstart.md § US4](quickstart.md) sur Chrome et sur Safari, noter la date et le résultat dans `docs/progress.md` ; vérifier T050 à T052 et P-05 passent

**Point de contrôle** : l'application s'installe depuis Chromium et WebKit ; c'est le troisième
critère de fin de la roadmap.

---

## Phase 7 : User Story 5, les mots viennent des clés et du pack (Priorité : P2)

**But** : changement de langue complet, pack fictif substituable, lexique figé.

**Test indépendant** : `test:e2e -- langue`, `test:unit -- pack`, P-06 règle 2.

### Tests pour la User Story 5

- [X] T059 [P] [US5] Écrire `web/tests/e2e/langue.spec.ts` : capturer tous les textes visibles en `fr`, cliquer `EN`, aucun texte identique ne subsiste hors noms propres, matricules et chiffres ; le mot du pack pour `CLASSE` change ; aucune clé brute (`/^[a-z_]+(\.[a-z_]+)+$/`) visible ; avec `?pack=fictif` en développement, le mot pour « classe » est celui du pack fictif ; persona dont `compte.langue` n'est pas dans `langues` → première langue du pack
- [X] T060 [P] [US5] Écrire `web/tests/unit/lexique.test.ts` : chaque mot du tableau « On dit » de `docs/design/lexique.md` existe dans `fr.json`, et aucun mot de la colonne « On ne dit jamais » n'apparaît dans `fr.json`

### Implémentation de la User Story 5

- [X] T061 [US5] Écrire `docs/design/lexique.md` : le vocabulaire visible de la tranche, semé de [05-design.md § 8.1](../../docs/05-design.md) (les deux colonnes), plus les mots des états, du ruban, de la coquille, des canaux (« En ligne » ; « Web » dans « on ne dit jamais ») ; règle en tête : il prime sur les clés
- [X] T062 [US5] Compléter `fr.json` et `en.json` pour tout ce que les phases 3 à 6 affichent, dans le même commit ; brancher le sélecteur de langue de `CoquilleEntete.vue` sur `useLibelles().changer` et `usePack()` ; `SourceDemonstration` accepte `?pack=fictif` en développement seulement
- [X] T063 [US5] Vérifier P-06 règle 2 et T059, T060 passent ; relire chaque libellé de refus (bouton inactif, champ en erreur) pour qu'il dise son versant positif (FR-056)

---

## Phase 8 : User Story 6, le poids est déclaré, mesuré, et le dépassement refuse (Priorité : P2)

**But** : P-10 sur Chromium par CDP, deux nombres, le premier affichage en 3G lente.

**Test indépendant** : `scripts/portes/p-10.sh` ; test négatif à 300 Ko.

### Tests pour la User Story 6

- [X] T064 [P] [US6] Écrire `web/tests/portes/p10.spec.ts` selon [research.md R-13](research.md) : projet `p10` (Chromium, `serviceWorkers: 'block'`), par écran budgété × persona : session CDP, `Network.enable`, somme des `encodedDataLength` jusqu'à `networkidle`, séparée entre polices (`.woff2`) et le reste ; compare à `budgetKo` et `budgetPolicesKo`, échoue en nommant écran, plafond, mesure ; liste les écrans `budgetKo: null` non `developpement` comme « non budgété » ; échoue sur toute requête hors `localhost` ; sous `Network.emulateNetworkConditions` (400 kbit/s, 400 ms) le ruban est visible en moins de 2 000 ms ; rapport `PORTE P-10 : <écran> plafond <n> Ko mesuré <m> Ko (polices <p> Ko, total <t> Ko)`
- [X] T065 [P] [US6] Écrire `scripts/portes/negatifs/p-10.sh` : génère une image PNG de 300 Ko (`sharp` ou `head -c` d'un bruit dans un PNG valide) dans `web/public/`, et l'ajoute en `<img>` dans `web/app/pages/index.vue`

### Implémentation de la User Story 6

- [X] T066 [US6] Écrire `scripts/portes/p-10.sh` (construction déjà faite par `verifier.sh` ; lance `pnpm --filter web portes:p10`) ; ajouter `porte P-10` après P-05 dans `scripts/verifier.sh`
- [X] T067 [US6] Mesurer chaque écran budgété, reporter les nombres dans `docs/progress.md` ; si l'accueil dépasse 120 Ko hors polices, réduire (découpage de routes, `experimental.payloadExtraction`, imports différés) **avant** tout autre geste, jamais relever le plafond ; vérifier P-10 passe et le test négatif échoue

---

## Phase 9 : User Story 7, chaque écran s'atteint, et les trois portes prouvent qu'elles mordent (Priorité : P2)

**But** : dix portes dans une commande, dix tests négatifs, dépôt intact, temps mesuré.

**Test indépendant** : `scripts/verifier.sh` puis `scripts/tests-negatifs.sh`.

### Tests pour la User Story 7

- [X] T068 [P] [US7] Écrire `scripts/portes/negatifs/p-05.sh` : insère `throw new Error('cassé')` dans `<script setup>` de `web/app/pages/a-propos.vue`
- [X] T069 [P] [US7] Écrire `scripts/portes/negatifs/p-06.sh` : insère une chaîne en dur `<p>Bonjour</p>` dans `web/app/components/canon/Coquille.vue`

### Implémentation de la User Story 7

- [X] T070 [US7] Étendre `scripts/tests-negatifs.sh` : `PORTES` += `P-05 P-06 P-10` ; pour ces trois portes la copie de travail fait `pnpm install --frozen-lockfile --offline` et, pour P-05 et P-10, `pnpm --filter web icones && pnpm --filter web build` avant la porte ; l'échec attendu porte `PORTE P-XX ÉCHOUÉE` ; comparaison du `git status` avant et après inchangée
- [X] T071 [US7] Ordonner `scripts/verifier.sh` selon [research.md R-15](research.md) : `ruff` → P-02 → P-07 → P-04 → P-11 → P-06 → P-01 → P-12 → P-03 → reparcours → typecheck → vitest → construction → P-05 → P-10 → e2e (`pnpm --filter web test:e2e`) ; compteur à dix portes ; mettre à jour le commentaire d'en-tête avec l'ordre et le motif
- [X] T072 [US7] Lancer `scripts/verifier.sh` et `scripts/tests-negatifs.sh`, noter les deux durées et « dix cassées, dix échecs, dépôt intact » dans `docs/progress.md` ; si la vérification dépasse trois minutes, le dire au journal avec le découpage proposé (SC-011), sans retirer une porte

---

## Phase 10 : User Story 8, 390 px d'abord, rien de caché, rien de trop petit (Priorité : P3)

**But** : disposition, cibles, survol, contraste, zoom, clavier, mouvement réduit.

**Test indépendant** : `test:e2e -- disposition` et `-- contraste`.

### Tests pour la User Story 8

- [X] T073 [P] [US8] Écrire `web/tests/e2e/disposition.spec.ts` : à 390, 768 et 1200 px sur `/`, `/d/vie_scolaire`, `/a-propos`, `/style` : `document.documentElement.scrollWidth <= innerWidth` ; `CanonTableau` rend des cartes (`data-mode="cartes"`) à 390 et des lignes à 768 ; le bouton principal de `/d/vie_scolaire` est en bas et pleine largeur à 390 ; à 125 % (`deviceScaleFactor` et `zoom` CSS) aucun débordement
- [X] T074 [P] [US8] Écrire `web/tests/e2e/cibles.spec.ts` : pour chaque élément interactif (`a, button, input, select, [role=switch], [role=tab]`) de chaque écran, `getBoundingClientRect` ou la zone du pseudo-élément ≥ 44 × 44 ; ≥ 52 sur `/d/vie_scolaire` (contexte `classe`) ; ≥ 48 sur `/a-propos` (`standard`)
- [X] T075 [P] [US8] Écrire `web/tests/e2e/survol-clavier.spec.ts` : capturer les éléments visibles, `hover` sur chaque zone, aucun élément nouveau n'apparaît ; `Tab` parcourt toutes les actions de la coquille et de `/style` dans l'ordre du DOM avec `:focus-visible` (contour non nul)
- [X] T076 [P] [US8] Écrire `web/tests/e2e/contraste.spec.ts` : `@axe-core/playwright` sur `/style` en `light` et en `dark`, règles `color-contrast` (AA) sans violation ; sur `/` et `/d/vie_scolaire` aussi

### Implémentation de la User Story 8

- [X] T077 [US8] Écrire `web/app/composables/useContexteTactile.ts` (`provide`/`inject` de `'contexte-tactile'`, pose `--cible` sur le conteneur, `poste` pose `--cible: var(--controle-poste)` plus un pseudo-élément de `var(--cible-plancher)` sur les contrôles) ; l'appliquer à `/d/vie_scolaire` (`classe`), `/a-propos` et `/` (`standard`), et proposer `poste` sur `/style` pour la démonstration
- [X] T078 [US8] Corriger ce que T073 à T076 révèlent dans les composants (`web/app/components/canon/*.vue`) et les pages, sans toucher au thème ni aux mesures ; vérifier que les quatre tests passent sur Chromium et que P-05 passe sur WebKit

---

## Phase 11 : Finition et transverse

**But** : le dépôt dit ce qu'il contient, le journal dit ce qui a été mesuré, et le quickstart se
déroule sur un clone frais.

- [ ] T079 [P] Mettre à jour `docs/01-stack.md § 2.1` « Ce qui existe aujourd'hui » : `web/` et sa structure, dix portes, `contrat/` avec `ContexteCapacites` ; et `README.md` : les commandes de l'interface
- [ ] T080 [P] Mettre à jour `docs/05-design.md § 0.1` : `composants.md`, `mouvement.md`, `lexique.md` existent ; retirer le tableau « ce qui manque encore » ou le réduire à ce qui manque vraiment
- [ ] T081 [P] Relire `docs/design/composants.md`, `mouvement.md`, `lexique.md` contre la page de style et les artboards validés ; aucun tiret cadratin dans les trois
- [ ] T082 Dérouler [quickstart.md](quickstart.md) sur un clone frais du dépôt (`git clone` dans le scratchpad, `pnpm install --frozen-lockfile`, navigateurs déjà présents), chronométrer jusqu'à `/style` ouverte et jusqu'à `scripts/verifier.sh` vert ; corriger ce qui manque
- [ ] T083 Écrire l'entrée de journal de fin d'implémentation dans `docs/progress.md` : les mesures (poids par écran, polices, premier affichage, durée de `verifier.sh` et de `tests-negatifs.sh`), les écarts d'implémentation par rapport au plan, la définition de terminé de [01-stack.md § 8.3](../../docs/01-stack.md) relue point par point, l'état de Q29 ; mettre l'état courant à « T0b implémentée, en attente de fusion »

---

## Dépendances et ordre d'exécution

### Dépendances entre phases

- **Mise en place (phase 1)** : aucune dépendance ; T005 attend T002 à T004 ; T009 attend T005.
- **Fondations (phase 2)** : dépend de la phase 1 ; **bloque toutes les stories**. T018 attend
  T017 ; T019 attend T018 ; T021 attend T020 (P-06 avant P-05 dans `verifier.sh`).
- **Stories (phases 3 à 10)** : dépendent de la phase 2. US1 d'abord (les composants servent à
  tout) ; US2 et US3 peuvent se mener en parallèle après US1 ; US4 après US3 (la coquille et
  l'écran « à propos ») ; US5 après US3 ; US6 après US3 et US4 (les écrans à mesurer existent) ;
  US7 après US6 ; US8 après US1 à US4 (les écrans à mesurer existent).
- **Finition (phase 11)** : après toutes les stories.

### Dépendances entre stories

- **US1** : après la phase 2 seulement.
- **US2** : après US1 (T033 `RubanSaisie.vue`).
- **US3** : après US1 (T034 `Coquille.vue`).
- **US4** : après US3 (T048, T049) ; T053, T054 peuvent commencer après la phase 1.
- **US5** : après US3 (le sélecteur de langue vit dans l'en-tête).
- **US6** : après US3, US4 (accueil, domaine, « à propos » déclarés).
- **US7** : après US6 (P-10 existe) ; T068, T069 peuvent s'écrire dès la phase 2.
- **US8** : après US1 à US4.

### À l'intérieur d'une story

- Les tests s'écrivent d'abord et **échouent** avant l'implémentation.
- Les fonctions pures de `core/` avant les composants, les composants avant les pages.
- La story est complète, et `scripts/verifier.sh` vert, avant la suivante.

### Possibilités de parallélisme

- Phase 1 : T003, T004, T006 ensemble après T002.
- Phase 2 : T011, T012 ensemble après T010 ; T013 à T016 ensemble ; T019 et T021 ensemble
  après T018 et T020.
- US1 : T022 à T024 ensemble ; T026 à T034 ensemble après T025 (neuf fichiers de composants,
  aucun ne dépend d'un autre).
- US3 : T042 à T044 ensemble ; T045 et T046 ensemble.
- US4 : T050 à T052 ensemble ; T053 et T054 ensemble.
- US8 : T073 à T076 ensemble.
- Phase 11 : T079 à T081 ensemble.

---

## Exemple de parallélisme : User Story 1

```bash
# Les trois tests d'abord, ils échouent :
Tâche : "T022 composants-etats.test.ts"
Tâche : "T023 style.spec.ts"
Tâche : "T024 voix.spec.ts"

# Puis composants.md (T025), puis les neuf fichiers de composants ensemble :
Tâche : "T027 Bouton.vue + Interrupteur.vue"
Tâche : "T028 Champ.vue"
Tâche : "T029 PastilleEtat.vue + PastilleCanal.vue"
Tâche : "T030 Recherche.vue + Avatar.vue + FilAriane.vue"
Tâche : "T031 Onglets.vue + CarteIndicateur.vue + Alerte.vue"
Tâche : "T032 Tableau.vue + LigneTableau.vue"
Tâche : "T033 RubanSaisie.vue"
Tâche : "T034 Coquille.vue et ses trois sous-composants"
Tâche : "T026 donnees.ts"

# Enfin la page de style (T035), qui les itère tous.
```

---

## Stratégie d'implémentation

### D'abord le MVP : User Story 1 seule

1. Phase 1, phase 2 : une application vide qui sert le thème et passe neuf portes.
2. Phase 3 : les quatorze composants et la page de style.
3. **S'arrêter et valider** : `/style` montre tout, clair et sombre ; `scripts/verifier.sh` vert.
   C'est le premier critère de fin de la roadmap, et ce que la revue visuelle a validé sur US1.

### Livraison incrémentale

1. US2 : le ruban vit. US3 : la coquille se compose. Chaque fois, vérification verte.
2. US4 : l'application s'installe (parcours à la main noté au journal).
3. US5, US6, US7 : la langue, le poids, les dix portes et leurs tests négatifs.
4. US8 : la discipline de disposition, qui corrige ce que les composants ont laissé passer.
5. Finition : le dépôt et le journal disent ce qui existe.

### Un développeur seul : l'ordre recommandé

T001 → T083 dans l'ordre, en respectant les [P] comme des lots à écrire d'un trait, et un commit
par point de contrôle au minimum. Les deux constructions des tests négatifs (P-05, P-10) rendent
`tests-negatifs.sh` long : le lancer aux points de contrôle, pas à chaque commit.

---

## Notes

- Les tâches [P] touchent des fichiers différents et n'attendent aucune tâche inachevée.
- Le label [Story] rend chaque tâche traçable à sa user story.
- Chaque story est complétable et testable seule, dans un vrai navigateur.
- Un test qui passe avant l'implémentation est un test faux.
- Commit après chaque tâche ou groupe logique ; le message dit ce qui existe maintenant.
- **Q29** (le plafond et les polices) est appliquée en issue B ; si l'utilisateur tranche
  autrement, T008 (`ecrans.json`) et T064 (règle de P-10) changent, rien d'autre.
- Aucun tiret cadratin, nulle part : ni code, ni commentaire, ni clé, ni document.
