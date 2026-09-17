# Démarrage rapide et validation : T0b, le socle d'interface

Ce guide prouve la tranche user story par user story. Les formes sont dans
[contracts/](contracts/), le modèle dans [data-model.md](data-model.md), les décisions dans
[research.md](research.md). Il ne contient aucun corps d'implémentation.

## Prérequis sur le poste

| Outil | Version | Rôle |
|---|---|---|
| Node | 24.18.1 | l'interface, les portes P-05, P-06, P-10 |
| `pnpm` | 10.26.2 | l'espace de travail, `pnpm-lock.yaml` unique à la racine |
| Playwright | 1.63.0, Chromium 1243 (complet, sans tête) et WebKit 2359 | les navigateurs réels |
| Le socle serveur de T0a | `docker compose up -d`, `uv sync` | P-03 régénère le contrat avec le schéma du contexte |

**Une fois, avec réseau** : `pnpm install --frozen-lockfile` puis
`pnpm --filter nelo-web exec playwright install chromium webkit`. Tout le reste est hors ligne.

## Démarrer

```bash
docker compose up -d                         # T0a : postgres, valkey, garage
pnpm install --frozen-lockfile               # racine + web/
pnpm --filter nelo-web icones                # génère public/icones/ depuis la lettre et les jetons (E-01)
pnpm --filter nelo-web dev                   # http://localhost:3000 (ou le port libre suivant), /style
```

Attendu : l'accueil s'ouvre en persona `un-domaine` ; `?persona=cinq-domaines`,
`?persona=sept-domaines`, `?persona=aucune-capacite` changent la composition sans rechargement de
code. `/style` liste les quatorze composants.

## US1 : la page de style

Ouvrir `/style`. Compter : quatorze sections, chaque état sur un conteneur clair et un conteneur
sombre côte à côte. Puis :

```bash
cmp docs/design/theme.css web/app/assets/css/theme.css && echo "thème identique"
scripts/portes/p-06.sh                       # 0 littérale : chaînes, couleurs, plateforme, rôles ; clés fr = en
pnpm --filter nelo-web build && grep -rl '"/style"' web/.output | wc -l   # attendu : 0, la route n'est pas construite
```

## US2 : le ruban ne bloque jamais

Sur `/d/vie_scolaire` (persona `un-domaine`), le champ de démonstration accepte la saisie. Avec le
réseau de test (`web/tests/e2e/ruban.spec.ts`) : état `absent` → « Hors ligne », le compte monte
à chaque saisie, rien n'est grisé ; état `bon` → le compte descend à zéro, « Tout est enregistré »,
sans geste. Le test vérifie aussi `prefers-reduced-motion` : aucune animation, forme et mot
présents.

```bash
pnpm --filter nelo-web exec playwright test --project=chromium ruban
```

## US3 : la coquille se compose

```bash
pnpm --filter nelo-web exec vitest run composition   # composer(contexte) pour les quatre personas, seuils 5/6, ordre du registre
pnpm --filter nelo-web exec playwright test --project=chromium coquille     # les quatre situations à 390 et 1200 px, aucune entrée grisée, l'administrateur nommé
grep -rn -i "role" web/app --include=*.ts --include=*.vue | grep -v 'role="'   # attendu : rien
```

## US4 : installable, autonome, une seule plateforme

Mécanique (dans P-05) : manifeste servi, `display: standalone`, icônes 192 et 512,
`apple-touch-icon`, service worker enregistré et contrôlant la page.

Chromium juge aussi l'application installable par son propre protocole (`Page.getInstallabilityErrors`,
aucune erreur attendue), dans P-05.

**Parcours vérifié à la main**, une fois par version, et noté dans le journal :

1. **Chrome** (poste ou Android) sur `http://localhost:3000` après `pnpm --filter nelo-web build` puis
   `PORT=3000 pnpm --filter nelo-web preview` :
   l'icône « Installer » apparaît dans la barre ; installer ; l'application s'ouvre sans barre
   d'adresse ; parcourir accueil → domaine → à propos → retour par la coquille.
2. **Safari** (iOS ou macOS 17+) : Partager → « Sur l'écran d'accueil » (ou « Ajouter au Dock ») ;
   ouvrir ; même parcours, même absence de barre.
3. Reconstruire avec un changement visible, relancer `preview`, rouvrir l'application installée :
   la nouvelle version s'applique sans message de rechargement.

```bash
grep -c "addEventListener('fetch'\|caches.match\|api/" web/app/sw/sw.ts   # attendu : 0 interception, 0 requête d'API
```

## US5 : les mots viennent des clés et du pack

```bash
pnpm --filter nelo-web exec playwright test --project=chromium langue     # FR → EN : chaque libellé change ; pack fictif : « classe » change sans code
pnpm --filter nelo-web exec vitest run pack        # montant 145000 → « 145 000 F » (U+202F), note "14.25" → « 14,25 / 20 »
```

## US6 : le poids

```bash
pnpm --filter nelo-web build
scripts/portes/p-10.sh                       # accueil (4 personas) ≤ 120 Ko, domaine ≤ 120 Ko, a-propos ≤ 150 Ko,
                                             # polices ≤ 45 Ko chacun ; style listé comme écran de développement
```

Attendu : une ligne par écran, plafond et mesure ; « premier affichage utile » sous 2 s en 3G lente
simulée ; aucune requête hors `localhost`.

## US7 : les portes

```bash
scripts/verifier.sh                          # dix portes vertes, temps total affiché (cible : sous 3 min)
scripts/tests-negatifs.sh                    # dix portes cassées, dix échecs, dépôt intact
```

Ce que chaque test négatif d'interface casse : P-05, une page qui lève au montage ; P-06, une chaîne
en dur dans `Coquille.vue` ; P-10, une image de 300 Ko dans l'accueil.

## US8 : 390 px d'abord

```bash
scripts/avec-serveur-dev.sh pnpm --filter nelo-web exec playwright test --project=chromium disposition cibles survol    # 390/768/1200 : pas de défilement horizontal ; tableau → cartes ; cibles ≥ 44, 52 en classe ; survol ne révèle rien ; focus visible
scripts/avec-serveur-dev.sh pnpm --filter nelo-web exec playwright test --project=chromium contraste     # axe : AA sur /style, clair et sombre
```

## Les commandes de `web/package.json`

| Commande | Ce qu'elle fait |
|---|---|
| `dev`, `build`, `preview` | Nuxt ; `icones` est appelée avant `dev` et `build` |
| `icones` | `node scripts/icones.mjs` |
| `typecheck` | `vue-tsc --noEmit` |
| `test:unit` | `vitest run` |
| `test:e2e` | `playwright test tests/e2e` (Chromium) ; la page de style exige le serveur de développement : `scripts/avec-serveur-dev.sh pnpm --filter nelo-web test:e2e` |
| `portes:p05`, `portes:p10` | `playwright test tests/portes/p05.spec.ts` (deux moteurs) / `p10.spec.ts` (Chromium, CDP) |
