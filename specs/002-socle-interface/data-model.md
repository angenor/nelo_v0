# Modèle : Le socle d'interface (T0b)

*Phase 1 du plan. Aucune table, aucune persistance : cette tranche ne manipule que des formes.
Chaque forme dit d'où elle vient dans le corpus, ce qui la valide, et où elle vit dans `web/`.*

## 1. Le contexte de composition

**Source** : [03-api.md § 1.9](../../docs/03-api.md), avec l'`administrateur` ajouté à `specify`.
**Où** : modèle Pydantic `modules/shared/contexte.py`, enregistré dans les composants OpenAPI sans
route (research R-05) ; type TypeScript dérivé `components["schemas"]["ContexteCapacites"]` dans
`contrat/client.d.ts`, réexporté par `web/app/core/contexte/types.ts`.

| Modèle | Champs | Validation |
|---|---|---|
| `ContexteCapacites` | `compte`, `etablissements[]`, `etablissement_actif`, `annees[]`, `annee_active`, `capacites[]`, `acces_nominatifs[]`, `country_pack`, `parametres_effectifs{}`, `alertes[]` | `etablissement_actif` ∈ `etablissements[].id` ; `annee_active` ∈ `annees[].id` |
| `Compte` | `id`, `nom`, `prenoms`, `langue` | `langue` : code à deux lettres |
| `EtablissementContexte` | `id`, `nom`, `sites[]`, `cycles_actifs[]`, `modules_actifs[]`, `administrateur` | `sites[]` : `{id, nom}` ; `cycles_actifs`, `modules_actifs` : codes `SCREAMING_SNAKE_CASE` |
| `Administrateur` | `nom`, `prenoms`, `telephone` | `telephone` : chaîne au format du pack, jamais vide |
| `AnneeContexte` | `id`, `libelle`, `etat` | `etat` ∈ `PREPARATION`, `ACTIVE`, `CLOTUREE`, `ARCHIVEE` ([02-domaine.md § 16](../../docs/02-domaine.md)) |
| `CapaciteContexte` | `code`, `perimetre{}` | `code` : `^[a-z_]+\.[a-z_]+\.[a-z_]+$` (domaine.objet.verbe) ; `perimetre` : listes d'identifiants nommées `*_ids` |
| `AccesNominatif` | `code`, `fin` | `fin` : date scolaire `YYYY-MM-DD` |
| `CountryPackContexte` | `pays`, `version`, `devise{code, exposant}`, `langues[]`, `decoupage`, `vocabulaire{}` | `langues` non vide ; `vocabulaire` : `{ CODE_NEUTRE: { fr: "…", en: "…" } }` pour les codes de [02-domaine.md § 15](../../docs/02-domaine.md) |
| `AlerteContexte` | `type`, `gravite`, `details{}` | `gravite` ∈ `INFO`, `ALERTE`, `CRITIQUE` |

> **Un ajout par rapport à l'exemple de § 1.9** : `country_pack.vocabulaire`. Le § 1.9 dit que le
> pack porte le vocabulaire métier ([02-domaine.md § 1.3](../../docs/02-domaine.md)) et que le
> client résout les libellés par lui ([03-api.md § 1.4](../../docs/03-api.md)) ; le contexte doit
> donc transporter ce vocabulaire, sinon l'interface ferait une seconde requête (`GET /country-pack`)
> au démarrage, ce que § 1.9 exclut (« une seule requête »). C'est une dérivation, appliquée dans
> le schéma et dans l'exemple de § 1.9 (voir le plan, diffs).

**Ce que le client n'en fait jamais** : aucun calcul. Le contexte est lu, jamais dérivé vers un
rôle, jamais mis en cache par le service worker.

## 2. Les formes dérivées du contexte

**Où** : `web/app/core/composition/` : fonctions pures, testées par Vitest (research R-14).

### `Domaine`

| Champ | Type | Origine |
|---|---|---|
| `code` | chaîne | premier segment d'un `CapaciteContexte.code` |
| `libelleCle` | clé i18n | registre |
| `famille` | code de famille ou `null` | registre |
| `ordre` | entier | registre |
| `route` | chemin | registre |
| `compte` | entier ou `null` | `alertes[]` ou donnée de démonstration ; jamais calculé par le client |

**Registre** (`web/app/core/composition/registre.ts`) : la liste des domaines que l'interface
sait afficher, avec leur famille et leur ordre. Il **ne contient aucun rôle**. Entrées de cette
tranche, dérivées de la planche du shell et de l'artboard US3 : `scolarite` (famille `ELEVES`),
`vie_scolaire` (`ELEVES`), `pedagogie` (`ENSEIGNEMENT`), `evaluation` (`ENSEIGNEMENT`), `conseil`
(`ENSEIGNEMENT`), `finance` (`GESTION`), `personnel` (`GESTION`), `communication`
(`COMMUNICATION`), `tenant` (`PARAMETRES`). Un code de capacité dont le domaine n'est pas au
registre est ignoré et journalisé en développement (cas limite de la spec).

### `Famille`

`code`, `libelleCle`, `ordre`. Cinq familles : `ELEVES`, `ENSEIGNEMENT`, `GESTION`,
`COMMUNICATION`, `PARAMETRES`. Une famille n'est **jamais** une route.

### `Situation`

Résultat de `composer(contexte)` :

| Valeur | Condition | Ce que rend la coquille |
|---|---|---|
| `AUCUNE_CAPACITE` | zéro domaine | l'écran qui nomme `etablissements[etablissement_actif].administrateur` |
| `MONO_DOMAINE` | un domaine | l'accueil **est** ce domaine ; navigation à plat |
| `MULTI_PLAT` | deux à cinq domaines | tableau composé ; navigation à plat |
| `MULTI_FAMILLES` | six domaines ou plus | tableau composé ; navigation regroupée, familles non vides seulement |

Invariants testés : un domaine sans capacité est absent de toute liste ; l'ordre est celui du
registre ; le seuil est **cinq inclus / six** (spec, cas limites) ; aucune entrée grisée n'existe
comme valeur possible du modèle (il n'y a pas de champ `desactive`).

## 3. L'état du ruban

**Où** : `web/app/core/saisie/etat-ruban.ts` (pure) et `composables/useSaisieDemonstration.ts`.

| Entrée | Type |
|---|---|
| `reseau` | `'bon' \| 'faible' \| 'absent'` (plateforme) |
| `enAttente` | entier ≥ 0 |
| `dernierEnregistrement` | instant ou `null` |

| État dérivé | Condition | Voix | Forme | Mots (clés) |
|---|---|---|---|---|
| `enregistre` | `enAttente = 0` et `reseau ≠ absent` | réussite | coche | `ruban.enregistre`, `ruban.dernier_a`, `ruban.aucune_attente`, `ruban.lien_bon` / `ruban.lien_faible` |
| `envoi` | `enAttente > 0` et `reseau ≠ absent` | marque | point qui pulse | `ruban.envoi_de` (n), `ruban.dernier_a`, `ruban.continuez`, `ruban.lien_bon` / `ruban.lien_faible` |
| `hors_ligne` | `reseau = absent` | ocre | lien barré | `ruban.hors_ligne`, `ruban.conservees` (n) / `ruban.aucune_attente`, `ruban.rien_perdu`, `ruban.pas_de_lien` |

`dernierEnregistrement = null` → clé `ruban.aucun_enregistrement` à la place de l'heure. Le compte
s'affiche exact. Aucun état ne produit une voix rouge : l'énumération des voix du ruban est
`reussite | marque | ocre`, et le type l'interdit.

## 4. L'interface de plateforme

**Où** : `web/app/core/plateforme/` (research R-09). Contrat détaillé dans
[contracts/interfaces-client.md](contracts/interfaces-client.md).

| Capacité | Forme | Réponse « indisponible » |
|---|---|---|
| `reseau` | `etat`, `surChangement(cb): () => void` | jamais indisponible : `bon` par défaut si le navigateur ne dit rien |
| `stockage` | `disponible`, `lire(cle)`, `ecrire(cle, valeur)`, `effacer(cle)` | `disponible = false`, `lire` rend `null`, `ecrire` ne lève pas |
| `camera` | `disponible`, `capturer()` | `capturer` rend `null` |
| `notifications` | `disponible`, `demander()`, `afficher(titre, corps)` | `demander` rend `'refusee'`, `afficher` ne lève pas |

Ce que le stockage porte dans cette tranche : `theme` (`light` \| `dark`), et rien d'autre. Aucune
saisie, aucune donnée métier, aucun jeton.

## 5. Les écrans et leurs budgets

**Où** : `web/ecrans.json`, un seul fichier (research R-12, R-16).

```json
[
  { "nom": "accueil", "route": "/", "budgetKo": 120, "personas": ["un-domaine", "cinq-domaines", "sept-domaines", "aucune-capacite"] },
  { "nom": "domaine", "route": "/d/vie_scolaire", "budgetKo": 120, "personas": ["un-domaine"] },
  { "nom": "a-propos", "route": "/a-propos", "budgetKo": 150 },
  { "nom": "style", "route": "/style", "budgetKo": null, "developpement": true }
]
```

Validation : `budgetKo` entier positif ou `null` ; toute page de `web/app/pages/` absente de ce
fichier fait échouer P-05 (« écran non déclaré ») ; tout écran à `budgetKo: null` sans
`developpement: true` est listé « non budgété » par P-10.

## 6. Les libellés

**Où** : `web/app/core/i18n/fr.json`, `en.json` ; `web/app/core/pack/`.

| Forme | Règle |
|---|---|
| Clé d'interface | `segment.segment[.segment]`, minuscules et `_` ; présente dans **les deux** fichiers (P-06) ; paramètres `{n}` |
| Code neutre | `SCREAMING_SNAKE_CASE`, parmi [02-domaine.md § 15](../../docs/02-domaine.md) ; résolu par `country_pack.vocabulaire[code][langue]` |
| Langue courante | `compte.langue` si ∈ `country_pack.langues`, sinon `langues[0]` |

`docs/design/lexique.md` fige les mots ; les fichiers JSON les portent ; un test compare les deux
pour les mots du lexique (états, ruban, coquille).

## 7. Les personas de démonstration

**Où** : `web/app/core/demonstration/personas/*.json`, chacun un `ContexteCapacites` complet,
validé au test contre le schéma du contrat (donc sans rôle).

| Persona | Capacités | Situation attendue |
|---|---|---|
| `un-domaine` | `vie_scolaire.appel.faire`, `vie_scolaire.sanction.poser` | `MONO_DOMAINE` |
| `cinq-domaines` | `scolarite.inscription.valider`, `pedagogie.edt.publier`, `vie_scolaire.appel.faire`, `evaluation.note.saisir`, `communication.circulaire.envoyer` | `MULTI_PLAT` |
| `sept-domaines` | les cinq ci-dessus + `conseil.decision.arreter`, `finance.encaissement.saisir` | `MULTI_FAMILLES` |
| `aucune-capacite` | aucune | `AUCUNE_CAPACITE` |

Tous portent le même établissement fictif (« Les Palmiers », site Angré, administrateur
« M. Konan Bertin »), l'année `2026-2027` active, le pack de démonstration, et pour
`cinq-domaines` et `sept-domaines` une alerte `BUDGET_SMS_BAS` de gravité `ALERTE`. Les noms
sont fictifs ; les données sont du primaire (CM2 A, maître titulaire).

## 8. Le manifeste et les fichiers générés

| Fichier | Généré depuis | Commité |
|---|---|---|
| `manifest.webmanifest` | `nuxt.config.ts` ← `docs/design/tokens.json` (couleurs), `core/produit.ts` (nom) | non (construction) |
| `public/icones/*.png` | `web/scripts/icones.mjs` ← mêmes sources | non (ignoré, régénéré) |
| `sw.js` | `web/sw/sw.ts` + liste injectée | non (construction) |
| `assets/css/theme.css`, `mesures.css` | copie de `docs/design/` | oui, comparée par P-06 |

## 9. Ce que cette tranche n'a pas

Aucune table, aucune migration, aucune politique RLS, aucun événement outbox, aucune clé
d'idempotence : rien n'est écrit. Le contrôle de constitution du plan le constate principe par
principe.
