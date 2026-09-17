# Modèle de données : T1a, se connecter et savoir où l'on est

**Phase 1 du plan** · 2026-09-17 · Dérivé de [02-domaine.md § 0, § 1.2, § 2.2, § 3.1, § 3.2,
§ 3.6, § 4.1, § 16 et § 17](../../docs/02-domaine.md), de [03-api.md § 1.2, § 1.9 et § 2.1](../../docs/03-api.md),
de [ADR 007](../../docs/adr/007-valkey-pour-l-ephemere.md) et de [research.md](research.md).
Tables et colonnes en français, accents dans les commentaires, jamais dans les identifiants SQL.

## Conventions, reprises de T0a

- Un schéma PostgreSQL par module. Cette tranche en pose **trois** : `habilitations` (le module de
  la tranche), et les **noyaux** `personnes` et `annees`, dont T3a et T2a sont propriétaires et
  qu'elles complètent sans renommer ni retirer ([research R-02](research.md)). Elle en étend un
  quatrième, `tenants`, d'une colonne et d'une table.
- Identifiants `uuid` v7 générés par l'application ; instants `timestamptz` en UTC.
- Chaque table : `ENABLE` et `FORCE ROW LEVEL SECURITY`, politique
  `tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid` ; propriétaire
  `nelo_proprietaire`, accès par `nelo_app`.
- **Aucune clé étrangère ne traverse un schéma** (R13, porte P-01) : `compte.personne_id`,
  `affectation.annee_id`, `affectation.etablissement_id`, `annee_scolaire.etablissement_id` et
  `etablissement.administrateur_compte_id` sont des identifiants, dont l'intégrité est tenue par
  l'application et testée.
- Chaque schéma porte sa table `evenement_outbox`, copie conforme de celle de `tenants`
  ([T0a, data-model](../001-socle-serveur/data-model.md)).

## Schéma `habilitations`

### `habilitations.compte` : ce par quoi une personne s'identifie

| Colonne | Type | Contraintes | Sens |
|---|---|---|---|
| `id` | `uuid` | PK | |
| `tenant_id` | `uuid` | NOT NULL | l'unité d'isolation |
| `personne_id` | `uuid` | NOT NULL | identifiant vers `personnes.personne`, sans clé étrangère (R13) |
| `identifiant` | `text` | NOT NULL | le numéro **normalisé E.164** (`+2250708123456`), jamais une autre forme |
| `statut` | `text` | NOT NULL, CHECK ∈ {`invite`, `actif`, `suspendu`}, défaut `'invite'` | [02-domaine.md § 16](../../docs/02-domaine.md) |
| `pin_empreinte` | `text` | NULL | Argon2id du code personnel ; `NULL` = absent. **Jamais renvoyée** |
| `pin_verrouille_le` | `timestamptz` | NULL | posé après cinq codes faux, levé par une ouverture par code reçu ou par lien |
| `invitation_empreinte` | `text` | NULL | SHA-256 du jeton du lien en cours ; `NULL` = aucun lien valide |
| `invitation_expire_le` | `timestamptz` | NULL | |
| `invite_le` | `timestamptz` | NULL | date du dernier envoi d'invitation |
| `derniere_connexion` | `timestamptz` | NULL | mise à jour à chaque ouverture (FR-059) |
| `cree_le` | `timestamptz` | NOT NULL, défaut `now()` | |

**Unicité** : `(tenant_id, personne_id)`, une personne a au plus un compte par tenant.
**Pas d'unicité sur `identifiant`** : le partage familial est permis ([spec US8](spec.md)).
**Index** : `(tenant_id, identifiant)`, `(identifiant)` pour la fonction de résolution ci-dessous.

**« Cet identifiant est partagé »** (FR-040) se calcule : plus d'un compte du tenant porte le même
`identifiant`. L'interface de service l'expose (`identifiant_partage(tenant_id, compte_id)`) ;
aucune colonne ne le duplique. La **déclaration** de partage est l'événement
`habilitations.compte.cree` avec `partage_familial = true` et son auteur.

**Transitions** ([02-domaine.md § 16](../../docs/02-domaine.md), diagramme dans le plan) :

| De | Vers | Par | Effets dans la même transaction |
|---|---|---|---|
| *(création)* | `invite` | `POST /comptes` | `invite_le`, `invitation_empreinte`, `invitation_expire_le` ; événement `compte.cree` puis `compte.invite` |
| `invite` | `actif` | lien ouvert, **ou** code reçu vérifié (FR-033) | `invitation_empreinte = NULL` ; événement `compte.active` |
| `invite` | `invite` | `POST /comptes/{id}/invitation` | nouveau jeton, l'ancien invalide ; événement `compte.invite` |
| `actif` ou `invite` | `suspendu` | `POST /comptes/{id}/suspension` | événement `compte.suspendu` ; **après** le `COMMIT`, révocation des sessions et oubli des appareils (éphémère) |
| `suspendu` | *(aucune)* | | la levée n'est pas livrée (FR-029) |

### `habilitations.affectation` : le noyau de l'affectation de § 3.2

Ce que T1a en pose, et rien d'autre : de quoi vérifier les deux en-têtes. T1b ajoute
`modele_role_id`, `perimetre`, `delegation_de` **sans renommer ni retirer**.

| Colonne | Type | Contraintes | Sens |
|---|---|---|---|
| `id` | `uuid` | PK | |
| `tenant_id` | `uuid` | NOT NULL | |
| `compte_id` | `uuid` | NOT NULL, FK → `habilitations.compte(id)` | même schéma : autorisé |
| `annee_id` | `uuid` | NOT NULL | identifiant vers `annees.annee_scolaire` (R4 : une affectation porte son année) |
| `etablissement_id` | `uuid` | NOT NULL | identifiant vers `tenants.etablissement`, **copié de l'année** ([research R-03](research.md)) |
| `debut` | `date` | NOT NULL | |
| `fin` | `date` | NULL | `NULL` = jusqu'à la fin de l'année |
| `cree_le` | `timestamptz` | NOT NULL, défaut `now()` | |

**Index** : `(tenant_id, compte_id, etablissement_id, annee_id)`, la requête des deux middlewares.
**Invariant testé** : `etablissement_id` est celui de l'année désignée par `annee_id`. **Vivante**
à un instant : `debut <= aujourd'hui` et (`fin IS NULL` ou `fin > aujourd'hui`), dans le fuseau de
l'établissement.

### `habilitations.evenement_outbox`

Copie conforme de `tenants.evenement_outbox`. Types émis par la tranche, tous avec `compte_id`
dans la charge :

| Type | Charge | Consommateur |
|---|---|---|
| `habilitations.otp.demande` | `identifiant`, `envoi_id`, `langue` | envoi du message court (le code est lu dans Valkey par `envoi_id`, jamais dans la charge) |
| `habilitations.compte.cree` | `personne_id`, `identifiant`, `partage_familial`, `cree_par` | journal |
| `habilitations.compte.invite` | `envoi_id`, `langue`, `expire_le` | envoi du lien (jeton lu dans Valkey par `envoi_id`) |
| `habilitations.compte.active` | `canal` (`LIEN` \| `CODE`) | journal |
| `habilitations.session.ouverte` | `session_id`, `canal` (`CODE` \| `PIN` \| `LIEN`), `choix_parmi` (nombre de comptes proposés), `appareil_connu` | journal |
| `habilitations.session.fermee` | `session_id`, `motif` (`DECONNEXION` \| `REUTILISATION` \| `SUSPENSION` \| `CHANGEMENT_NUMERO` \| `EXPIRATION`) | journal |
| `habilitations.pin.defini` | `remplace` (booléen) | journal |
| `habilitations.compte.suspendu` | `suspendu_par` | journal |
| `habilitations.identifiant.change` | `ancien`, `nouveau`, `par` (`PERSONNE` \| `ADMINISTRATION`), `envoi_id`, `langue` | envoi du message d'information à l'ancien numéro |

Le consommateur « envoi » compose le texte depuis les gabarits `fr`/`en` de la tranche, appelle
la passerelle, et marque l'événement ; une passerelle indisponible met l'événement en échec, le
travailleur reprend ([T0a R-09](../001-socle-serveur/research.md)).

### Fonctions du schéma `habilitations`

| Fonction | Signature | Sécurité | Rôle |
|---|---|---|---|
| `habilitations.comptes_par_identifiant` | `(text) → setof (id, tenant_id, personne_id, statut)` | `SECURITY DEFINER`, `STABLE` | **avant tout tenant** : les comptes qui portent un numéro, tous tenants confondus (`/auth/otp`, `/auth/otp/verification`) |
| `habilitations.compte_par_invitation` | `(text) → (id, tenant_id, statut, invitation_expire_le)` | `SECURITY DEFINER`, `STABLE` | avant tout tenant : le compte dont l'empreinte d'invitation est celle du lien |
| `habilitations.compte_par_id_sans_tenant` | `(uuid) → (id, tenant_id, statut)` | `SECURITY DEFINER`, `STABLE` | avant tout tenant : le compte d'un appareil connu (`/auth/pin`) |

Le test de T0a qui énumère les fonctions `SECURITY DEFINER` par schéma s'étend à cette table.

## Schéma `personnes` : le noyau

### `personnes.personne`

Les seules colonnes de [02-domaine.md § 2.2](../../docs/02-domaine.md) que le contexte lit ;
T3a pose les autres.

| Colonne | Type | Contraintes | Sens |
|---|---|---|---|
| `id` | `uuid` | PK | |
| `tenant_id` | `uuid` | NOT NULL | |
| `nom` | `text` | NOT NULL | |
| `prenoms` | `text` | NOT NULL | |
| `langue_preferee` | `text` | NOT NULL, CHECK `~ '^[a-z]{2}$'` | `compte.langue` du contexte |
| `telephone_principal` | `text` | NULL | E.164 ; la cohérence avec `compte.identifiant` est une règle de T3a |
| `cree_le` | `timestamptz` | NOT NULL, défaut `now()` | |

**Interface** : `lire_identite(tenant_id, personne_id) → Identite(nom, prenoms, langue)` et
`lire_identites(tenant_id, personne_ids) → dict`. Le schéma porte son `evenement_outbox` (vide en
T1a) pour que P-01 et le travailleur le traitent comme les autres.

## Schéma `annees` : le noyau

### `annees.annee_scolaire`

| Colonne | Type | Contraintes | Sens |
|---|---|---|---|
| `id` | `uuid` | PK | |
| `tenant_id` | `uuid` | NOT NULL | |
| `etablissement_id` | `uuid` | NOT NULL | identifiant vers `tenants.etablissement` |
| `libelle` | `text` | NOT NULL | ex. `2026-2027` |
| `debut` | `date` | NOT NULL | |
| `fin` | `date` | NOT NULL | |
| `etat` | `text` | NOT NULL, CHECK ∈ {`preparation`, `active`, `cloturee`, `archivee`} | [02-domaine.md § 4.3](../../docs/02-domaine.md) ; **aucune transition en T1a** |
| `cree_le` | `timestamptz` | NOT NULL, défaut `now()` | |

**Unicité partielle** : au plus une `active` et une `preparation` par `(tenant_id,
etablissement_id)` (index partiels), l'invariant de § 4.5 posé dès maintenant pour que T2a le
trouve. **Interface** : `lire_annees(tenant_id, etablissement_id) → list[Annee(id, libelle,
etat)]` et `etablissement_de_annee(tenant_id, annee_id)`. Outbox vide.

## Schéma `tenants` : ce que la tranche y ajoute

- **`tenants.etablissement.administrateur_compte_id`** `uuid NULL`, identifiant vers
  `habilitations.compte`, sans clé étrangère ([02-domaine.md § 1.2](../../docs/02-domaine.md),
  diff de `specify`).
- **`tenants.country_pack`** ([02-domaine.md § 1.2](../../docs/02-domaine.md), provision nommée
  par T0a) :

| Colonne | Type | Contraintes | Sens |
|---|---|---|---|
| `pays_code` | `text` | PK (avec `version`) | |
| `version` | `integer` | PK | |
| `contenu` | `jsonb` | NOT NULL | ce que [§ 1.3](../../docs/02-domaine.md) énumère ; T1a n'en lit que le sous-ensemble du contexte et le format de numéro |
| `publie_le` | `timestamptz` | NOT NULL, défaut `now()` | **jamais modifié en place** |

**Politique** : comme `parametre_catalogue`, lecture seule pour `nelo_app` sous
`current_setting IS NOT NULL` ; un pack n'appartient à aucun tenant. Le tenant y pointe par
`(pays_code, country_pack_version)`. **Semé** : le pack de la Côte d'Ivoire, sous-ensemble utile,
et le **pack fictif** du test d'agnosticité (échelle sur 10, deux périodes, un autre indicatif),
dans une migration de `tenants`.

Ce que `contenu` porte en T1a, et que `country_pack` du contexte reflète :

```json
{ "devise": { "code": "XOF", "exposant": 0, "symbole": "F" }, "langues": ["fr", "en"],
  "decoupage": "TRIMESTRES", "telephone": { "indicatif": "225" },
  "vocabulaire": { "CLASSE": { "fr": "Classe", "en": "Class" }, "…": {} } }
```

Ces valeurs sont des **données semées**, jamais des littérales du code (principe V, porte P-09).

## Ce qui vit dans Valkey, jamais en base

Perdre Valkey ne coûte que des reconnexions (FR-016, [ADR 007](../../docs/adr/007-valkey-pour-l-ephemere.md)).

| Clé | Valeur | Durée | Rôle |
|---|---|---|---|
| `session:{session_id}` | `{compte_id, tenant_id, ouverte_le, canal, refresh_courant}` | `securite.duree_session_minutes` | **la liste de révocation** : une session dont la clé n'existe plus est révoquée ; consultée à chaque requête |
| `sessions_compte:{compte_id}` | ensemble de `session_id` | idem | suspension et changement administratif : tout révoquer d'un coup |
| `refresh:{sha256(jeton)}` | `{session_id, generation, remplace_le?}` | durée de session restante | rotation : le jeton courant ; un jeton **remplacé** garde sa clé le temps de la fenêtre de concurrence (10 s) avec `remplace_le` ; représenté hors fenêtre, il révoque la session |
| `otp:{identifiant}` | `{empreinte, tentatives, comptes: [{id, tenant_id}], envoi_id}` | 10 min | le code en cours pour un numéro ; un nouveau remplace |
| `otp_texte:{envoi_id}` | le code en clair | 10 min | lu et effacé par le consommateur qui envoie le message ; **jamais dans l'outbox** |
| `otp_renvoi:{identifiant}` | `1` | 60 s | le délai avant renvoi |
| `otp_debit:{identifiant}` | compteur | 1 h | cinq demandes par heure et par numéro |
| `otp_debit_client:{adresse}` | compteur | 1 h | la limitation par client, avant toute lecture |
| `changement:{compte_id}` | `{nouveau_identifiant, empreinte, tentatives, envoi_id}` | 10 min | le code de vérification d'un nouveau numéro (FR-035) |
| `appareil:{sha256(secret)}` | `{compte_id, tenant_id, connu_le}` | `securite.appareil_connu_jours` | un appareil connu d'un compte ; le secret vit dans le cookie `nelo_appareils` |
| `appareils_compte:{compte_id}` | ensemble d'empreintes | idem | « oublier tous ses appareils » |
| `pin_tentatives:{compte_id}` | compteur | 1 h | cinq codes faux ; le **verrou** qui en résulte est durable (`pin_verrouille_le`) |
| `invitation_texte:{envoi_id}` | le jeton en clair | 1 h | lu et effacé par le consommateur ; l'empreinte durable est sur le compte |

## Le jeton d'accès

JWT signé **HS256** avec `NELO_SECRET_JETON`, soixante minutes ([03-api.md § 1.2](../../docs/03-api.md)),
claims : `sub` (compte), `ten` (tenant), `sid` (session), `iat`, `exp`, `jti`. Il n'est **pas** un
secret durable : sa révocation est l'absence de `session:{sid}`. Aucune autre donnée (nom, capacité)
n'y entre : le contexte est la seule source.

## Les cookies

| Nom | Contenu | Attributs | Posé par |
|---|---|---|---|
| `nelo_refresh` | le jeton de rafraîchissement (opaque, 32 octets aléatoires en base64url) | `HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/rafraichissement` (et `/api/v1/auth/session` pour la fermeture) | l'API |
| `nelo_appareils` | la liste des secrets d'appareil (un par compte connu), séparés par `.` | `HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth` ; `Max-Age` = validité la plus lointaine | l'API |
| `nelo_acces` | le jeton d'accès | `HttpOnly; Secure; SameSite=Strict; Path=/` | **la couche Nuxt** ([research R-09](research.md)) : l'API rend le jeton dans le corps, le serveur Nuxt le range dans ce cookie et le retransforme en `Authorization: Bearer` |

`Secure` est levé en développement local sur `http://localhost` par la configuration, jamais en
production.

## Schémas Pydantic, la frontière de l'API

Déclarés dans `modules/socle/habilitations/schemas.py` ; les formes exactes sont dans
[contracts/openapi-attendu.yaml](contracts/openapi-attendu.yaml).

| Schéma | Sens |
|---|---|
| `CorpsDemandeCode` | `identifiant` (chaîne, normalisée par le service ; `AUT_NUMERO_INVALIDE` sinon) |
| `CorpsVerificationCode` | `identifiant`, `code` (six chiffres), `compte_id?` (le choix quand plusieurs comptes) |
| `ChoixCompte` | `compte_id`, `nom`, `prenoms`, `etablissement_nom` : ce que l'écran « qui ouvre la session ? » affiche |
| `ReponseVerificationCode` | soit `SessionOuverte`, soit `ChoixRequis(comptes: list[ChoixCompte])` (discriminant `resultat`) |
| `SessionOuverte` | `jeton_acces`, `expire_dans` (secondes), `compte: {id, nom, prenoms, langue, pin_defini}`, `appareil_connu` (booléen) |
| `CorpsOuverturePin` | `compte_id`, `pin` (quatre chiffres) |
| `CorpsDefinitionPin` | `pin`, `pin_courant?` |
| `ReponseAppareil` | `comptes: list[{compte_id, nom, prenoms, pin_defini}]` : les comptes connus de cet appareil |
| `CorpsCreationCompte` | `personne_id`, `identifiant`, `partage_familial` (défaut `false`) |
| `CompteCree` | `id`, `statut`, `invite_le` (**jamais** le jeton) |
| `CorpsChangementTelephone` | `nouvel_identifiant` |
| `CorpsVerificationChangement` | `code` |
| `CorpsChangementAdministratif` | `nouvel_identifiant` |
| `ContexteCapacites` | inchangé, celui de T0b dans `modules/shared/contexte.py` |

Les `EnveloppeErreur` et les codes `AUT_` sont ceux de [03-api.md § 1.6 et § 2.1](../../docs/03-api.md).

## Entités hors base

| Entité | Où | Forme |
|---|---|---|
| `PolitiqueSecurite` | `modules/socle/habilitations/politique.py` | **les constantes du produit**, en un seul endroit (FR-060) : `OTP_LONGUEUR = 6`, `OTP_VALIDITE = 10 min`, `OTP_TENTATIVES = 5`, `OTP_RENVOI = 60 s`, `OTP_PAR_HEURE_PAR_NUMERO = 5`, `OTP_PAR_HEURE_PAR_CLIENT = 20`, `PIN_LONGUEUR = 4`, `FENETRE_CONCURRENCE_REFRESH = 10 s`, `DISPENSE_PIN_COURANT = 10 min`, `JETON_ACCES = 60 min` |
| `SessionCourante` | `api/session.py`, déposée dans `scope["state"]` | `compte_id`, `tenant_id`, `session_id` |
| `ContexteRequete` | idem | + `etablissement_id`, `annee_id?` |
| `Configuration` | `api/configuration.py` | + `NELO_SECRET_JETON`, `NELO_INDICATIF_DEFAUT` (l'indicatif proposé avant toute session, FR-002), `NELO_COOKIES_SECURE`, `NELO_NOM_PRODUIT`, `NELO_SMS_JOURNAL` (chemin d'un journal des messages en simulation, développement et test seulement) |
| Gabarits de messages courts | `modules/socle/habilitations/messages/{fr,en}.json` | `otp`, `invitation`, `changement_ancien_numero` ; un test vérifie que chaque rendu tient sous 160 caractères avec les valeurs les plus longues |
