# Modèle de données — T0a, le socle serveur

**Phase 1 du plan** · 2026-09-10 · Dérivé de [02-domaine.md § 0, § 1 et § 17](../../docs/02-domaine.md)
et de [research.md](research.md). Tables et colonnes en français, accents compris dans les
commentaires, jamais dans les identifiants SQL.

## Conventions du schéma

- Un schéma PostgreSQL par module : ici **`tenants`**, et lui seul. Aucune clé étrangère n'en sort.
- Identifiants : `uuid`, générés **par l'application** en UUID v7 (`uuid.uuid7()`), jamais par la
  base — cohérent avec [03-api.md § 1.4](../../docs/03-api.md) et avec le principe IX de la
  constitution (le client attribue l'identifiant d'une création ; en T0a, le serveur pose lui-même
  les tenants et établissements de test).
- Instants : `timestamptz`, toujours en UTC.
- Chaque table : `ENABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY`, au moins une politique.
  Propriétaire `nelo_proprietaire` ; l'application n'accède que par `nelo_app`.
- L'expression de tenant, partout : `current_setting('app.current_tenant', true)::uuid`. Absente,
  elle vaut `NULL` et aucune ligne ne passe.

## Tables

### `tenants.tenant` — l'unité d'isolation

| Colonne | Type | Contraintes | Sens |
|---|---|---|---|
| `id` | `uuid` | PK | le tenant lui-même |
| `nom` | `text` | NOT NULL | |
| `raison_sociale` | `text` | NULL | |
| `pays_code` | `text` | NOT NULL | ISO 3166-1 alpha-2 ; **jamais interprété par le code** (R8) |
| `country_pack_version` | `integer` | NOT NULL | provision : la table `country_pack` arrive avec la tranche qui l'utilise |
| `statut_abonnement` | `text` | NOT NULL, défaut `'ACTIF'` | valeurs précisées par la tranche éditeur |
| `branding` | `jsonb` | NOT NULL, défaut `'{}'` | |
| `cree_le` | `timestamptz` | NOT NULL, défaut `now()` | |

**Politique** : `id = current_setting('app.current_tenant', true)::uuid` pour toutes les
commandes.

### `tenants.etablissement` — ce que désigne l'en-tête

| Colonne | Type | Contraintes | Sens |
|---|---|---|---|
| `id` | `uuid` | PK | |
| `tenant_id` | `uuid` | NOT NULL, FK → `tenants.tenant(id)` | même schéma : autorisé |
| `nom` | `text` | NOT NULL | |
| `code_officiel` | `text` | NULL | |
| `agrement` | `text` | NULL | |
| `fuseau_horaire` | `text` | NOT NULL | identifiant IANA, ex. `Africa/Abidjan` — une **donnée**, pas une constante du code |
| `telephone` | `text` | NULL | |
| `direction_regionale` | `text` | NULL | |
| `cree_le` | `timestamptz` | NOT NULL, défaut `now()` | |

**Index** : `(tenant_id)`. **Politique** : expression de tenant standard.

### `tenants.parametre_catalogue` — les clés connues

| Colonne | Type | Contraintes | Sens |
|---|---|---|---|
| `cle` | `text` | PK | ex. `assistance.suspendue` |
| `portee_la_plus_basse` | `text` | NOT NULL, CHECK ∈ {`TENANT`, `ETABLISSEMENT`, `SITE`, `CYCLE`} | en dessous, `TEN_PORTEE_INVALIDE` |
| `type` | `text` | NOT NULL, CHECK ∈ {`ENTIER`, `DECIMAL`, `BOOLEEN`, `CHAINE`, `PLAGE_HORAIRE`} | valide `valeur` à l'écriture |
| `valeur_defaut` | `jsonb` | NULL | `NULL` si obligatoire ou fourni par le country pack |
| `origine_defaut` | `text` | NOT NULL, CHECK ∈ {`LITTERALE`, `COUNTRY_PACK`, `OBLIGATOIRE`} | d'où vient le défaut quand `valeur_defaut` est `NULL` |
| `description_cle` | `text` | NOT NULL | clé i18n, **jamais un texte affiché** (FR-049) |

**Politique** : `SELECT` seulement pour `nelo_app`, `USING (current_setting('app.current_tenant',
true) IS NOT NULL)` ; aucune politique d'écriture. Alimentée par la migration (seed ci-dessous).

**Le catalogue seedé** — [02-domaine.md § 17](../../docs/02-domaine.md), ligne pour ligne :

| `cle` | portée | type | défaut | origine |
|---|---|---|---|---|
| `absence.delai_notification_minutes` | ETABLISSEMENT | ENTIER | `15` | LITTERALE |
| `absence.regroupement_recapitulatif` | ETABLISSEMENT | CHAINE | `"HEBDOMADAIRE"` | LITTERALE |
| `note.taille_lot_enregistrement` | TENANT | ENTIER | `5` | LITTERALE |
| `note.tolerance_hors_bornes` | TENANT | CHAINE | `"AUCUNE"` | LITTERALE |
| `bulletin.publication_apres_conseil` | ETABLISSEMENT | BOOLEEN | `true` | LITTERALE |
| `finance.penalite_retard_taux` | ETABLISSEMENT | DECIMAL | `"0"` | LITTERALE |
| `finance.remise_fratrie_taux` | ETABLISSEMENT | DECIMAL | `"0"` | LITTERALE |
| `finance.seuil_alerte_impaye_jours` | ETABLISSEMENT | ENTIER | `30` | LITTERALE |
| `sms.plafond_mensuel` | ETABLISSEMENT | ENTIER | `NULL` | OBLIGATOIRE |
| `sms.fenetre_envoi` | ETABLISSEMENT | PLAGE_HORAIRE | `"07:00-19:00"` | LITTERALE |
| `conseil.delai_recours_jours` | TENANT | ENTIER | `NULL` | COUNTRY_PACK |
| `inscription.derogation_dossier_incomplet` | ETABLISSEMENT | BOOLEEN | `false` | LITTERALE |
| `securite.duree_session_minutes` | TENANT | ENTIER | `480` | LITTERALE |
| `securite.expiration_delegation_max_jours` | TENANT | ENTIER | `90` | LITTERALE |
| **`assistance.suspendue`** | **ETABLISSEMENT** | **BOOLEEN** | **`false`** | **LITTERALE** — Q28, confirmée le 2026-09-14 (R-20) |
| `conservation.dossier_eleve_annees` | TENANT | ENTIER | `NULL` | COUNTRY_PACK |
| `conservation.signalement_annees` | TENANT | ENTIER | `NULL` | COUNTRY_PACK |

Les clés dont § 17 dit « *country pack* » sont posées à la portée `TENANT` — le country pack est
porté par le tenant ([02-domaine.md § 1.4](../../docs/02-domaine.md)) — avec `origine_defaut =
COUNTRY_PACK` : leur défaut viendra du pack quand sa table existera. Les types `CHAINE` de
`absence.regroupement_recapitulatif` et `note.tolerance_hors_bornes` sont volontairement larges :
leurs valeurs permises appartiennent à T5 et T6b, qui les resserreront.

### `tenants.parametre_valeur` — ce qui a été posé

| Colonne | Type | Contraintes | Sens |
|---|---|---|---|
| `id` | `uuid` | PK | |
| `tenant_id` | `uuid` | NOT NULL, FK → `tenants.tenant(id)` | |
| `cle` | `text` | NOT NULL, FK → `tenants.parametre_catalogue(cle)` | |
| `portee` | `text` | NOT NULL, CHECK ∈ {`TENANT`, `ETABLISSEMENT`, `SITE`, `CYCLE`} | |
| `portee_id` | `uuid` | NOT NULL | l'identifiant de la portée ; pour `TENANT`, le `tenant_id` lui-même |
| `valeur` | `jsonb` | NOT NULL | typée par le catalogue, validée par le service |
| `pose_le` | `timestamptz` | NOT NULL, défaut `now()` | |

**Unicité** : `(tenant_id, cle, portee, portee_id)` — c'est la clé naturelle de l'`UPSERT`, et ce
qui rend l'écriture idempotente par nature (R-06). **Index** : `(tenant_id, cle)`. **Politique** :
expression de tenant standard.

**Règles de validation** (service, avant toute écriture, après le schéma Pydantic) :

1. `cle` ∉ catalogue → `TEN_PARAMETRE_INCONNU`, `details.cles_connues` = les clés du catalogue.
2. `portee` plus basse que `portee_la_plus_basse` → `TEN_PORTEE_INVALIDE`,
   `details.portee_la_plus_basse`.
3. `portee` ∈ {`SITE`, `CYCLE`} → `TEN_PORTEE_INVALIDE`, `details.portees_disponibles =
   ["TENANT", "ETABLISSEMENT"]` (R-17).
4. `portee = TENANT` et `portee_id ≠ tenant courant`, ou `portee = ETABLISSEMENT` et `portee_id`
   n'est pas un établissement du tenant → `TEN_PORTEE_INVALIDE`, `details.motif = "HORS_TENANT"`.
5. `valeur` incompatible avec `type` → **`TEN_VALEUR_INVALIDE`**, `champ = "valeur"`,
   `details.type_attendu`. C'est une valeur fautive sur une clé connue : ni `TEN_PARAMETRE_INCONNU`
   (la clé existe), ni `VAL_SCHEMA_INVALIDE` (le schéma a accepté un JSON valide). Le code est entré
   dans [03-api.md § 2.3](../../docs/03-api.md) le 2026-09-14 — voir la note en fin de fichier.

**Résolution de la valeur effective** — un seul trait, quatre portées (FR-011) : pour une clé et
une portée demandée, on lit la valeur posée à la portée la plus proche en remontant
`CYCLE → SITE → ETABLISSEMENT → TENANT` ; sinon `valeur_defaut` ; sinon `NULL` avec
`source = "NON_DEFINIE"`. La réponse dit toujours **à quelle portée** la valeur a été résolue.

### `tenants.evenement_outbox` — l'outbox du module

| Colonne | Type | Contraintes | Sens |
|---|---|---|---|
| `id` | `uuid` | PK | UUID v7 : l'ordre des identifiants suit l'ordre d'écriture |
| `tenant_id` | `uuid` | NOT NULL, FK → `tenants.tenant(id)` | |
| `type` | `text` | NOT NULL | ex. `tenants.parametre.pose` |
| `charge` | `jsonb` | NOT NULL | ce qu'un consommateur a besoin de savoir, sans relire la base |
| `ecrit_le` | `timestamptz` | NOT NULL, défaut `now()` | |
| `etat` | `text` | NOT NULL, CHECK ∈ {`en_attente`, `pris`, `traite`, `en_echec`}, défaut `'en_attente'` | |
| `tentatives` | `integer` | NOT NULL, défaut `0` | |
| `pris_le` | `timestamptz` | NULL | |
| `traite_le` | `timestamptz` | NULL | |
| `derniere_erreur` | `text` | NULL | message, jamais une trace complète |

**Index** : `(tenant_id, etat, ecrit_le, id)` — la requête du travailleur. **Politique** :
expression de tenant standard, `SELECT`, `INSERT`, `UPDATE` ; pas de `DELETE` pour `nelo_app` — un
événement traité reste, il ne s'efface pas (principe X : « une file purgée ne le permet pas, un
grand livre si »).

**Transitions** — celles du diagramme 3 de [design/diagrammes.md](design/diagrammes.md) :

| De | Vers | Quand |
|---|---|---|
| *(transaction)* | `en_attente` | `COMMIT` de la transaction du changement d'état ; un `ROLLBACK` n'écrit rien |
| `en_attente` | `pris` | le travailleur le sélectionne (`FOR UPDATE SKIP LOCKED`), `pris_le = now()` |
| `pris` | `traite` | consommateur revenu sans erreur, `traite_le = now()` |
| `pris` | `en_echec` | consommateur en erreur ou interrompu, `tentatives + 1`, `derniere_erreur` |
| `en_echec` | `en_attente` | à la boucle suivante — reprise, livraison possible une seconde fois |

Un `pris` dont le processus meurt reste `pris` : au redémarrage, le travailleur reprend aussi les
`pris` dont `pris_le` est plus vieux qu'un délai configuré. Jamais perdu.

## Fonctions du schéma

| Fonction | Signature | Sécurité | Rôle |
|---|---|---|---|
| `tenants.tenant_de_etablissement` | `(uuid) → uuid` | `SECURITY DEFINER`, propriétaire `nelo_proprietaire`, `STABLE` | résout le tenant depuis l'en-tête d'établissement **avant** qu'un tenant soit posé — provisoire jusqu'à T1a (R-16) |
| `tenants.tenants_pour_travailleur` | `() → setof uuid` | `SECURITY DEFINER`, propriétaire `nelo_proprietaire`, `STABLE` | donne au travailleur les tenants à parcourir (R-09) |

**Un test énumère les fonctions `SECURITY DEFINER` de chaque schéma de module et échoue s'il en
trouve une qui n'est pas dans cette table.**

## Ce qui vit dans Valkey — jamais en base

| Clé | Valeur | Durée | Rôle |
|---|---|---|---|
| `idem:{tenant_id}:{requete_id}` | JSON `{ "empreinte": sha256, "statut": int, "corps": base64, "en_cours": bool }` | 24 h | la réponse mémorisée de [03-api.md § 1.3](../../docs/03-api.md), bornée au tenant |

Perdre Valkey n'altère aucune donnée durable ([ADR 007](../../docs/adr/007-valkey-pour-l-ephemere.md)).

## Schémas Pydantic — la frontière de l'API

Déclarés dans `modules/socle/tenants/schemas.py`, réutilisés par la route et par la spécification
générée. Les formes exactes sont dans [contracts/openapi-attendu.yaml](contracts/openapi-attendu.yaml).

| Schéma | Sens |
|---|---|
| `ParametreEffectif` | `cle`, `valeur`, `type`, `portee_resolue`, `portee_id`, `source` (`VALEUR` \| `DEFAUT` \| `NON_DEFINIE`) |
| `ReponseParametres` | `etablissement_id`, `parametres: list[ParametreEffectif]` — **pas** paginée : le catalogue est borné et petit |
| `CorpsPoserParametre` | `portee`, `portee_id`, `valeur` — `valeur` typée `bool \| int \| str` en entrée, le service tranche selon le catalogue |
| `ParametrePose` | `cle`, `portee`, `portee_id`, `valeur`, `pose_le` |
| `EnveloppeErreur` | `code`, `message`, `champ`, `details`, `requete_id` — [03-api.md § 1.6](../../docs/03-api.md), dans `modules/shared/erreurs.py` |
| `ReponseSante` | `etat: "OK"` |

## Entités hors base

| Entité | Où | Forme |
|---|---|---|
| `Capacite` | `modules/socle/assistance` | énumération `C1_REDACTION_ASSISTEE`, `C2_QUESTION_REPONSE_DOCUMENTAIRE`, `C3_PLANIFICATION_SOUS_CONTRAINTES`, `C4_ANALYSE_ET_DETECTION_DE_SIGNAUX`, `C5_EXTRACTION_DOCUMENTAIRE`, `C6_ASSISTANCE_A_L_APPRENTISSAGE` — [02-domaine.md § 13.2](../../docs/02-domaine.md) |
| `EtatCapacite` | idem | `NON_LIVREE`, `SUSPENDUE`, `DISPONIBLE` |
| `ModeSimulation` | `modules/shared/simulation.py` | `SUCCES`, `ACCUSE_EN_RETARD`, `ACCUSE_EN_DOUBLE`, `JAMAIS_RECU`, `INDISPONIBLE` |
| `Configuration` | `api/configuration.py` (`pydantic-settings`, préfixe `NELO_`) | URL de la base (rôle `nelo_app`), URL de Valkey, intervalle du travailleur, mode et délai de chaque simulation |

## Note — un code d'erreur qui manquait au contrat

La règle 5 ci-dessus a besoin d'un code pour « clé connue, valeur d'un mauvais type ». Ni
`TEN_PARAMETRE_INCONNU` (la clé est connue) ni `TEN_PORTEE_INVALIDE` (la portée est bonne) ni
`VAL_SCHEMA_INVALIDE` (le schéma a accepté un JSON valide) ne conviennent. Diff **appliqué le
2026-09-14** sur [03-api.md § 2.3](../../docs/03-api.md), avec ceux de [research.md](research.md) :

```diff
-`TEN_PARAMETRE_INCONNU` (`422`), `TEN_PORTEE_INVALIDE` (`422`), `TEN_COUNTRY_PACK_FIGE` (`409`),
+`TEN_PARAMETRE_INCONNU` (`422`), `TEN_PORTEE_INVALIDE` (`422`), `TEN_VALEUR_INVALIDE` (`422`,
+`details.type_attendu`), `TEN_COUNTRY_PACK_FIGE` (`409`),
```
