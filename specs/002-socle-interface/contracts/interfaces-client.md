# Contrats côté client : ce que chaque brique expose, et rien d'autre

*Les signatures sont données en TypeScript parce que c'est la langue du client ; elles décrivent
une surface, pas une implémentation. Les noms sont en français, comme le code.*

## 1. Les quatorze composants (`components/canon/`)

Chaque composant exporte ses énumérations d'états ; la page de style et `docs/design/composants.md`
lisent ces énumérations, un test compte qu'elles correspondent (FR-092).

| Composant | Props d'état | Énumérations exportées |
|---|---|---|
| `CanonBouton` | `variante`, `inactif?: { raison: cle }`, `type` | `VARIANTES = ['principal','secondaire','discret','danger']` |
| `CanonChamp` | `type`, `etat`, `aide?`, `unite?`, `erreur?: cle`, `inactif?` | `TYPES = ['texte','nombre','choix','case']`, `ETATS = ['repos','focus','erreur','inactif']` |
| `CanonInterrupteur` | `modelValue: boolean`, `inactif?` | aucune |
| `CanonPastilleEtat` | `voix`, `forme`, `mot: cle` | `VOIX = ['reussite','ocre','rouge','neutre','contour']`, `FORMES = ['rond','capsule']` |
| `CanonPastilleCanal` | `canal`, `cout?: { montant, devise }` | `CANAUX = ['EN_LIGNE','WHATSAPP','SMS','PAPIER']` |
| `CanonRecherche` | `portee: cle`, `etat`, `raccourci?` | `ETATS = ['repos','focus','saisie','resultats','aucun']` |
| `CanonAvatar` | `initiales`, `photo?`, `taille` | `TAILLES = ['petite','grande']` |
| `CanonFilAriane` | `segments: { libelle, route? }[]` | aucune (le dernier n'a pas de route) |
| `CanonOnglets` | `onglets: { cle, compte? }[]`, `actif` | aucune |
| `CanonCarteIndicateur` | `valeur`, `libelle: cle`, `variation?: { sens, texte }` | `SENS = ['positive','negative','neutre']` |
| `CanonAlerte` | `niveau`, `titre: cle`, `corps?: cle`, `action?: { libelle: cle, sur }` | `NIVEAUX = ['information','attente','danger','enregistre']` |
| `CanonTableau` / `CanonLigneTableau` | `colonnes: { cle, mono? }[]`, `lignes`, `selection?` | aucune ; carte sous 768 px |
| `CanonRubanSaisie` | `dernierEnregistrement`, `enAttente` | `ETATS = ['enregistre','envoi','hors_ligne']`, `VOIX = ['reussite','marque','ocre']` |
| `CanonCoquille` | `contexte: ContexteCapacites` (slot par défaut : l'écran) | `SITUATIONS = ['AUCUNE_CAPACITE','MONO_DOMAINE','MULTI_PLAT','MULTI_FAMILLES']` |

Règles communes : tout mot visible est une **clé** (`cle`), jamais une chaîne ; toute couleur est
un jeton ; toute cible interactive lit `--cible` ; aucun composant ne lit `navigator` ni `window`.

## 2. Le contexte tactile

```ts
type ContexteTactile = 'classe' | 'standard' | 'poste'
provide('contexte-tactile', ContexteTactile)   // par l'écran ou la coquille
// → variable CSS --cible : var(--cible-classe) | var(--cible-standard) | var(--controle-poste)
//   un contrôle « poste » garde une zone interactive de var(--cible-plancher)
```

## 3. La source de contexte (`core/contexte/`)

```ts
type ContexteCapacites = components['schemas']['ContexteCapacites']   // contrat/client.d.ts

interface SourceContexte {
  charger(): Promise<ContexteCapacites>
}
// T0b : SourceDemonstration (personas JSON). T1a : SourceApi (GET /moi/capacites).
```

## 4. La composition (`core/composition/`)

```ts
function domaineDe(code: string): string                 // 'vie_scolaire.appel.faire' → 'vie_scolaire'
function composer(contexte: ContexteCapacites): Composition
interface Composition {
  situation: Situation
  domaines: Domaine[]                                     // ordre du registre, jamais vide sauf AUCUNE_CAPACITE
  familles: { famille: Famille; domaines: Domaine[] }[]   // vide sauf MULTI_FAMILLES ; familles non vides seulement
  accueil: { route: string }                              // le domaine (mono) ou le tableau composé
}
```

## 5. L'interface de plateforme (`core/plateforme/`)

```ts
interface Plateforme {
  reseau: { readonly etat: 'bon' | 'faible' | 'absent'; surChangement(cb: (etat) => void): () => void }
  stockage: { readonly disponible: boolean; lire(cle: string): string | null; ecrire(cle: string, valeur: string): void; effacer(cle: string): void }
  camera: { readonly disponible: boolean; capturer(): Promise<Blob | null> }
  notifications: { readonly disponible: boolean; demander(): Promise<'accordee' | 'refusee'>; afficher(titre: string, corps: string): void }
}
function usePlateforme(): Plateforme      // fournie par plugins/plateforme.client.ts
// Une implémentation : web.ts. En test et en développement seulement, le plugin accepte une
// implémentation de remplacement posée par les tests ; c'est l'unique porte, dans ce dossier.
```

## 6. Les libellés (`core/i18n/`, `core/pack/`)

```ts
function useLibelles(): { t(cle: string, params?: Record<string, string | number>): string; langue: Ref<'fr' | 'en'>; changer(langue): void }
function usePack(): { libelle(code: string): string; devise: { code: string; exposant: number }; montant(entier: number): string; note(valeur: string, bareme: string): string }
// montant : entier d'unité mineure → chaîne avec espace fine insécable (U+202F) et symbole du pack.
// note : chaîne décimale → virgule décimale et barème. Aucun calcul : mise en forme seulement.
```

## 7. Le thème (`composables/useTheme.ts`)

```ts
function useTheme(): { theme: Ref<'systeme' | 'light' | 'dark'>; forcer(theme): void }
// 'systeme' : aucun attribut ; sinon data-theme sur <html>. Mémorisé par plateforme.stockage('theme').
```

## 8. Le service worker (`sw/sw.ts`)

Contrat de comportement, vérifié par P-05 et par lecture : précache des fichiers listés par la
construction ; navigations et toute autre requête → réseau, sans interception ; message
`SKIP_WAITING` → `skipWaiting()` ; nettoyage des caches périmés. **Rien d'autre.** Aucune requête
vers `/api/` n'est jamais interceptée.

## 9. Les déclarations d'écrans (`web/ecrans.json`)

Voir [data-model.md § 5](../data-model.md). Contrat de P-05 et P-10 : chaque entrée → une route
ouverte sur deux moteurs et deux thèmes ; `budgetKo` non nul → une mesure ; `developpement: true`
→ ouverte sur le serveur de développement, jamais construite.

## 10. Le schéma ajouté au contrat OpenAPI (`modules/shared/contexte.py`)

Les modèles de [data-model.md § 1](../data-model.md), enregistrés dans `components.schemas` par
`api/contrat.py`. Aucune route dans cette tranche. Un test (`tests/portes/`) vérifie que
`contrat/openapi.json` porte `ContexteCapacites` et que `contrat/client.d.ts` en dérive ; P-03
garantit l'absence d'écart.
