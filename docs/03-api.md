# 03 — Contrat d'API

*Source de vérité du contrat. Toute phase de planification en dérive ; aucune n'invente.*

> **Si une tranche a besoin d'une ressource, d'un code d'erreur ou d'un en-tête absent d'ici, elle
> propose un diff explicite sur ce fichier AVANT de continuer.** Le contrat OpenAPI généré par
> FastAPI depuis les schémas Pydantic, servi sur `/openapi.json`, fait foi à l'exécution ; ce fichier
> fait foi à la conception. Les deux ne divergent jamais plus d'un commit.

Le front-end est entièrement découplé : **le monolithe n'expose que des API.** Il n'y a pas de
gabarit rendu côté serveur, à une exception près — les documents ([§ 1.10](#110-les-documents-sont-rendus-par-le-serveur)).

---

## 1. Conventions

### 1.1 Adressage

```
https://{hôte}/api/v1/{ressource}
```

- **Une seule version** au MVP. Une rupture de contrat incrémente le segment ; l'ancienne reste
  servie le temps que les clients migrent.
- Ressources au pluriel, en français, sans accent : `/eleves`, `/inscriptions`, `/encaissements`.
- Les sous-ressources qui n'existent pas hors de leur parent sont imbriquées :
  `/seances/{id}/presences`. Les autres restent à plat avec un filtre.

### 1.2 Authentification

**L'identifiant principal est le numéro de téléphone, pas l'e-mail** — beaucoup de responsables
légaux n'en ont pas.

| En-tête | Contenu | Obligatoire |
|---|---|---|
| `Authorization` | `Bearer {jwt}` — jeton d'accès court (60 min par défaut) | Oui, sauf `/auth/*` et `/sante` |
| `X-Nelo-Etablissement` | UUID de l'établissement actif | Sur toute route portant des données d'établissement |
| `X-Nelo-Annee` | UUID de l'année scolaire de travail | Sur toute route pédagogique (R4) |
| `X-Nelo-Requete` | **UUID v7 généré par le client** | **Sur tout `POST`, `PUT`, `PATCH`, `DELETE`** |

- Le refresh est un cookie **`HttpOnly`, `Secure`, `SameSite=Strict`, avec rotation à chaque usage**.
  Le choix du cookie plutôt que du stockage navigateur est délibéré : **les postes sont partagés**
  dans les établissements, et un jeton en `localStorage` survit à la fermeture de session.
- **La révocation est immédiate** : une liste consultée à chaque requête, pas l'expiration du jeton.
  Le départ d'un enseignant en cours d'année coupe l'accès le jour même.
- `X-Nelo-Etablissement` est vérifié contre les affectations du compte. Un établissement non affecté
  répond `403 TEN_ETABLISSEMENT_NON_AUTORISE`, jamais `404` — ne pas publier l'existence d'un établissement tiers.
- **Omettre `X-Nelo-Annee` sur une route pédagogique est une erreur `400 ANN_ANNEE_REQUISE`**, jamais
  un repli silencieux sur l'année active. Un repli implicite écrit une note dans la mauvaise année.

**Ce que vaut un en-tête absent ou refusé.** La table est opposable : c'est elle qui fixe le statut,
pas l'endroit du code où le refus a été écrit.

| En-tête | Absent | Présent, mais refusé |
|---|---|---|
| `Authorization` | `401 AUT_JETON_MANQUANT` | `401 AUT_JETON_INVALIDE`, `401 AUT_SESSION_REVOQUEE` |
| `X-Nelo-Etablissement` | `400 TEN_ETABLISSEMENT_REQUIS` | `403 TEN_ETABLISSEMENT_NON_AUTORISE` — le compte n'y est pas affecté |
| `X-Nelo-Annee` | `400 ANN_ANNEE_REQUISE` sur une route pédagogique | `400 ANN_ANNEE_REQUISE` si ce n'est pas un UUID, `404 TEN_RESSOURCE_INTROUVABLE` si l'année est hors du tenant |
| `X-Nelo-Requete` | `400 REQUETE_CLE_MANQUANTE` | `400 REQUETE_CLE_INVALIDE` — pas un UUID v7 ([§ 1.3](#13-idempotence)) |

> ⚠️ **Ces quatre en-têtes sont lus par un middleware, chacun le sien, avant que FastAPI n'ait validé
> quoi que ce soit.** C'est exactement ce qui rend ces `400` vrais : le refus a lieu hors du chemin de
> Pydantic. **Déclarer l'un d'eux en dépendance `Header(...)` rendrait cette table fausse** — le refus
> sortirait en `422 VAL_SCHEMA_INVALIDE`, et le client testerait un code qui n'arrive jamais
> ([§ 1.8](#18-codes-http)). Le `401` du jeton est la seule exception au `400` : une identité absente
> n'est pas une requête illisible, et l'interface n'en fait qu'une chose — rouvrir une session.

### 1.3 Idempotence

**Toute écriture porte `X-Nelo-Requete`, un UUID v7 généré côté client.** Le serveur mémorise la
réponse associée pendant 24 h.

- Rejouer la même requête renvoie **la même réponse, sans réexécuter l'effet**.
- Réutiliser le même UUID avec un corps différent renvoie `409 REQUETE_REJOUEE_DIFFEREMMENT`.
- **C'est ce qui rend inoffensif un renvoi sur réseau lent** — la situation normale du produit, pas
  l'exception. Sans lui, un appel de séance rejoué crée quarante présences en double.

| Code | Statut | Cas |
|---|---|---|
| `REQUETE_CLE_MANQUANTE` | `400` | En-tête `X-Nelo-Requete` absent sur une écriture |
| `REQUETE_CLE_INVALIDE` | `400` | Présent, mais pas un UUID v7 |
| `REQUETE_REJOUEE_DIFFEREMMENT` | `409` | Même clé, corps différent |
| `REQUETE_EN_COURS` | `409` | Même clé reçue avant la fin de la première exécution |

> ⚠️ **L'idempotence est un middleware, et il lit son en-tête lui-même.** C'est ce qui justifie le
> `400` des deux premiers : ils sont refusés **avant** que FastAPI n'ait validé quoi que ce soit.
> **Déclarer `X-Nelo-Requete` en dépendance `Header(...)` rendrait ces deux codes faux** — le refus
> passerait par le chemin de Pydantic et sortirait en `422 VAL_SCHEMA_INVALIDE`.

> **La mémorisation vit dans Valkey, jamais en base**, et elle est bornée au tenant
> ([ADR 007](adr/007-valkey-pour-l-ephemere.md)). La perdre dégrade un rejeu en réexécution, jamais en
> corruption : la colonne `cle_idempotence` des tables de faits porte la contrainte d'unicité qui
> prend le relais.

### 1.4 Formats

| Donnée | Format | Exemple |
|---|---|---|
| **Identifiant** | UUID v7, en chaîne | `01936b7e-…` |
| **Montant** | **Entier d'unité mineure**, jamais un flottant, jamais une chaîne | `145000` = 145 000 F |
| **Devise et exposant** | ISO 4217 sur le tenant, avec son exposant | `{"code":"XOF","exposant":0}` |
| **Note** | **Chaîne décimale** — jamais un flottant JSON | `"14.25"` |
| **Coefficient** | Chaîne décimale | `"3"`, `"1.5"` |
| **Instant** | RFC 3339 en UTC | `2026-08-20T13:05:00Z` |
| **Date scolaire** | `YYYY-MM-DD`, dans le fuseau de l'établissement | `2026-10-14` |
| **Intervalle** | Objet `{ "debut": ..., "fin": ... }`, borne de fin **exclue** | `[début, fin)` |
| **Énumération** | `SCREAMING_SNAKE_CASE`, valeurs du domaine | `NON_JUSTIFIEE` |
| **Libellé visible** | **Jamais une chaîne littérale** : une clé i18n, résolue par le country pack | `"cle":"periode.trimestre.2"` |

> **Le serveur renvoie les valeurs déjà calculées.** Le client n'applique aucune formule de
> composition, ne convertit aucune note en mention, ne calcule aucun rang, aucun solde, aucune
> pénalité. Il affiche. C'est la conséquence directe de R5 : une moyenne calculée côté client ne porte
> pas la version du référentiel qui l'a produite, et n'est donc pas rejouable.

### 1.5 Pagination, tri, filtres

```
GET /api/v1/eleves?curseur=…&taille=50&tri=nom&classe_id=…&statut=ACTIF
```

- **Pagination par curseur opaque.** `taille` par défaut 50, plafond 200.
- Réponse : `{ "donnees": [...], "curseur_suivant": "…" | null }`.
- Tri par champ, préfixe `-` pour décroissant. Les tris autorisés sont déclarés par ressource.
- **Un filtre inconnu est une erreur `400`**, jamais ignoré en silence — un filtre ignoré rend une
  liste fausse qui a l'air juste.
- **Toute liste est bornée au périmètre effectif du compte.** Un enseignant qui liste `/eleves` sans
  filtre reçoit les élèves de ses seules classes, pas une erreur.

### 1.6 Enveloppe d'erreur

```json
{
  "code": "EVA_NOTE_HORS_BORNES",
  "message": "note 22 hors de l'échelle [0, 20] du référentiel v3 de l'année 2026-2027",
  "champ": "valeur",
  "details": { "echelle_min": "0", "echelle_max": "20", "referentiel_version": 3 },
  "requete_id": "01936b7e-…"
}
```

| Champ | Rôle |
|---|---|
| `code` | Stable, préfixé par domaine. **C'est lui que le client teste**, jamais le message |
| `message` | Français, factuel, destiné au journal et au support — pas affiché tel quel |
| `champ` | Le champ fautif quand il y en a un |
| `details` | **De quoi construire l'issue**, pas seulement constater l'échec |
| `requete_id` | L'`X-Nelo-Requete` reçu, pour rapprocher le journal client et le journal serveur |

### 1.7 Préfixes de code d'erreur

| Préfixe | Domaine |
|---|---|
| `AUT_` | Authentification, session, OTP |
| `HAB_` | Capacités, périmètre, cloisonnement |
| `TEN_` | Tenant, établissement, country pack |
| `PER_` | Personnes, foyers, liens de responsabilité |
| `ANN_` | Année scolaire, période, bascule |
| `STR_` | Structure pédagogique |
| `SCO_` | Scolarité, inscription, dossier |
| `EVA_` | Évaluation, note, bulletin, référentiel |
| `VIE_` | Vie scolaire, appel, absence, discipline |
| `CON_` | Conseil de classe, décision de passage |
| `FIN_` | Finance, facture, paiement, caisse |
| `COM_` | Communication, SMS, routage, budget |
| `PRO_` | Protection de l'enfance, santé — **cloisonnés** |
| `IMP_` | Import et migration |
| `VAL_` | **Validation de schéma** — le refus de Pydantic, avant toute règle métier |
| `REQUETE_` | **Idempotence** — clé de requête, rejeu, mémorisation ([§ 1.3](#13-idempotence)) |
| `API_` | **Ce qui n'appartient à aucun module** — défaillance serveur, limitation de débit |

> **Trois de ces préfixes ne sont pas des modules**, et c'est pourquoi la colonne dit « domaine » :
> `VAL_` est une couche que toute écriture traverse, `REQUETE_` un middleware placé devant toutes les
> écritures, `API_` le serveur lui-même. Aucun paquet de `modules/metier/` ne les porte.

### 1.8 Codes HTTP

| Code | Emploi |
|---|---|
| `200` | Lecture, ou écriture qui ne crée rien |
| `201` | Création — `Location` porte l'URL de la ressource |
| `204` | Action sans corps de réponse |
| `400` | **Ce qui n'a pas pu être lu du tout** : corps illisible, en-tête obligatoire absent ou malformé quand un middleware le lit ([§ 1.2](#12-authentification)), filtre de requête inconnu |
| `401` | Jeton absent, expiré ou révoqué |
| `403` | Authentifié, mais capacité ou périmètre insuffisant |
| `404` | Ressource inexistante **dans le périmètre du tenant** |
| `409` | Conflit d'état : année clôturée, note verrouillée, rejeu divergent |
| `422` | **Deux natures, un seul statut** : corps, paramètre de route ou de requête, ou en-tête déclaré en dépendance, invalide au regard du schéma — code préfixé `VAL_`, la sortie standard de Pydantic, `details` portant le chemin de chaque champ fautif — **ou** règle métier violée sur un corps par ailleurs valide, avec son code de domaine |
| `429` | Limitation de débit — `API_LIMITE_DEBIT`, `Retry-After` obligatoire |
| `500` | **Défaillance non prévue** — `API_ERREUR_INTERNE`, **aucun détail technique dans `message`** : ni trace d'exécution, ni requête SQL, ni nom de table ; `requete_id` suffit à retrouver la trace côté serveur |
| `503` | Dépendance externe indisponible — `API_DEPENDANCE_INDISPONIBLE`, `details.dependance` nomme l'abstraction (agrégateur de paiement, passerelle SMS, service d'inférence) |

> **Le `422` porte deux natures, et c'est délibéré.** Pydantic refuse le corps avant que la moindre
> règle métier s'exécute ; le service refuse ensuite une opération sur un corps valide. **C'est le
> `code` de l'enveloppe qui les distingue**, jamais le statut seul — `VAL_SCHEMA_INVALIDE` pour la
> première, un code de domaine préfixé pour la seconde. Un client qui teste le statut se trompera un
> jour ; c'est pourquoi la règle est écrite ici. Deux conséquences opposables : **le gestionnaire de
> validation de FastAPI est remplacé**, pour qu'un refus de schéma porte l'enveloppe de
> [§ 1.6](#16-enveloppe-derreur) avec son `code` et son `champ` renseignés ; et **`400` se réserve à
> ce qui n'a pas pu être lu du tout**.

**La ligne qui tranche, et elle vaut pour tous les cas à venir :**

> **`400`** — refusé **par un middleware**, avant que FastAPI n'ait validé quoi que ce soit.
> **`422`** — refusé **par la validation FastAPI**, corps **ou en-tête** (code préfixé `VAL_`), ou par
> une **règle métier** sur un corps valide (code de domaine).

> **`403` ne dit jamais ce qui manque en clair.** Il renvoie le code de capacité attendu dans
> `details.capacite_requise`, ce qui permet à l'interface d'orienter vers l'administrateur de
> l'établissement — jamais une page vide, jamais une erreur technique.

### 1.9 Le contexte — ce qui compose l'interface

```
GET /api/v1/moi/capacites
```

Une seule requête au démarrage, et à chaque changement d'établissement ou d'année. Elle porte tout ce
dont l'interface a besoin pour **ne rendre que ce qui existe** :

```json
{
  "compte": { "id": "…", "nom": "…", "prenoms": "…", "langue": "fr" },
  "etablissements": [
    { "id": "…", "nom": "…", "sites": [ … ], "cycles_actifs": ["PRIMAIRE"],
      "modules_actifs": ["SCOLARITE", "EVALUATION", "VIE_SCOLAIRE", "FINANCE", "COMMUNICATION"],
      "administrateur": { "nom": "…", "prenoms": "…", "telephone": "…" } }
  ],
  "etablissement_actif": "…",
  "annees": [{ "id": "…", "libelle": "2026-2027", "etat": "ACTIVE" },
             { "id": "…", "libelle": "2027-2028", "etat": "PREPARATION" }],
  "annee_active": "…",
  "capacites": [
    { "code": "vie_scolaire.appel.faire",   "perimetre": { "classe_ids": ["…", "…"] } },
    { "code": "evaluation.note.saisir",     "perimetre": { "matiere_ids": ["…"], "classe_ids": ["…"] } },
    { "code": "finance.encaissement.saisir","perimetre": { "site_ids": ["…"] } }
  ],
  "acces_nominatifs": [{ "code": "protection.signalement.consulter", "fin": "2027-06-30" }],
  "country_pack": { "pays": "CI", "version": 4, "devise": { "code": "XOF", "exposant": 0, "symbole": "F" },
                    "langues": ["fr", "en"], "decoupage": "TRIMESTRES",
                    "vocabulaire": { "CLASSE": { "fr": "Classe", "en": "Class" }, "…": { } } },
  "parametres_effectifs": { "absence.delai_notification_minutes": 15, "note.taille_lot_enregistrement": 5 },
  "alertes": [{ "type": "BUDGET_SMS_BAS", "gravite": "ALERTE", "details": { "restant": 1240 } }]
}
```

> **C'est ce qui fait qu'une action non autorisée est absente et non grisée** (R10) : le front ne rend
> pas un domaine dont aucune capacité n'est détenue. **Le serveur refuse quand même** — aucune
> vérification côté client n'est jamais la seule (R9).
>
> **Aucune liste de rôles n'est codée en dur côté front.** Sinon chaque nouveau modèle de rôle
> exigerait un déploiement.
>
> **Chaque établissement porte son `administrateur`** — nom, prénoms, téléphone. C'est ce qui permet
> à une personne sans capacité de voir un message qui **nomme** qui peut lui attribuer ses domaines,
> jamais une page vide ([02-domaine.md § 3.4](02-domaine.md#34-composition-de-linterface--les-règles)).
> Le téléphone est celui d'un membre du personnel, montré dans le détail du contexte de la personne,
> jamais dans une liste (R5, [§ 3](#3-règles-de-conception-opposables)). *Ajouté par T0b.*
>
> **Le pack porte son `vocabulaire`** : les codes neutres de [02-domaine.md § 15](02-domaine.md#15-glossaire-des-concepts-neutres)
> avec leurs libellés `fr` et `en`. C'est ce qui permet au client de résoudre un libellé métier
> ([§ 1.4](#14-formats)) **sans seconde requête** au démarrage. *Ajouté par T0b.*
>
> **La devise porte son `symbole`**, ce que l'interface écrit après un montant : le code ISO ne
> se lit pas, et l'écrire côté client serait une littérale de pays. *Ajouté par T0b.*

### 1.10 Les documents sont rendus par le serveur

Bulletin, reçu, liste d'appel, fiche d'urgence, attestation d'effectif, procès-verbal : **le PDF est
produit par le monolithe, jamais par le navigateur.** La mise en page d'un bulletin ne peut pas
dépendre du terminal de l'utilisateur, et le gabarit est une donnée du country pack.

```
POST /api/v1/documents            → { "type": "BULLETIN", "portee": {...} }  → 202 + tache_id
GET  /api/v1/documents/{id}                                                  → état, url, empreinte
```

**Toute liste critique est imprimable à l'avance** : appel, embarquement transport, fiches d'urgence,
personnes autorisées à récupérer un élève. C'est le mode dégradé assumé pour la journée où le réseau
tombe, et il est documenté dans la formation — pas découvert le jour même.

### 1.11 Ce que l'API ne fait pas

| Absent | Pourquoi |
|---|---|
| Endpoint de synchronisation, file d'actions, résolution de conflit | Le hors-connexion est différé → [ADR 001](adr/001-hors-connexion-differe.md). **L'idempotence et l'UUID client sont là ; le moteur de synchronisation, non** |
| Endpoint acceptant une moyenne, un rang ou un solde calculés par le client | Le serveur calcule, le client affiche |
| Endpoint renvoyant une entité d'un autre tenant | RLS forcée : la question ne se pose pas au niveau applicatif |
| Endpoint d'écriture sur une année `cloturee` ou `archivee` | `409 ANN_ANNEE_CLOTUREE`, avec la procédure de rectification dans `details` |
| Endpoint qui expose une donnée cloisonnée sans accès nominatif | `403 HAB_ACCES_NOMINATIF_REQUIS`, et **la tentative s'écrit dans `journal_acces`** |

---

## 2. Carte des ressources

Légende de la colonne **Cap.** : la capacité requise. `—` = authentifié suffit. `▣` = capacité
**cloisonnée**, non attribuable par un rôle.

### 2.1 Authentification

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `POST` | `/auth/otp` | Demander un code par SMS sur un numéro | — |
| `POST` | `/auth/otp/verification` | Échanger le code contre une session | — |
| `POST` | `/auth/pin` | Ouvrir une session par PIN sur un appareil déjà connu | — |
| `POST` | `/auth/pin/definition` | Définir ou changer son PIN | — |
| `POST` | `/auth/rafraichissement` | Rotation du refresh | — |
| `DELETE` | `/auth/session` | Fermer la session courante | — |
| `POST` | `/auth/invitation/{jeton}` | Activer un compte depuis un lien à usage unique | — |

`AUT_OTP_EXPIRE`, `AUT_OTP_INVALIDE`, `AUT_OTP_TENTATIVES_EPUISEES`, `AUT_NUMERO_INCONNU`,
`AUT_NUMERO_INVALIDE` (`422`), `AUT_COMPTE_SUSPENDU`, `AUT_COMPTE_DEJA_ACTIF` (`422`),
`AUT_PIN_INVALIDE`, `AUT_PIN_ABSENT`, `AUT_PIN_TENTATIVES_EPUISEES`, `AUT_APPAREIL_INCONNU`,
`AUT_INVITATION_INVALIDE`, `AUT_IDENTIFIANT_DEJA_UTILISE` (`422`), `AUT_SESSION_REVOQUEE`,
`AUT_JETON_MANQUANT` (`401`), `AUT_JETON_INVALIDE` (`401`).

> **Sur `/auth/*`, un refus de preuve est un `401`** : code reçu faux, expiré ou épuisé, code
> personnel faux, absent ou verrouillé, appareil inconnu, lien consommé ou expiré, compte suspendu.
> **Un refus de règle sur un corps valide est un `422`** avec son code `AUT_` : numéro mal formé,
> compte déjà actif, identifiant déjà porté par un autre compte. *Ajouté par T1a.*

> **Les deux derniers ne sont jamais un refus de schéma.** Un `Authorization` absent, illisible,
> expiré ou révoqué est un `401` sur **toute** route protégée, jamais un `400` ni un `422` : le
> middleware de session tranche avant d'atteindre le routeur ([§ 1.2](#12-authentification)).

> `AUT_NUMERO_INCONNU` **n'est jamais renvoyé sur `/auth/otp`** : la route répond `204` quel que soit
> le numéro, et l'OTP ne part que si le compte existe. Publier l'existence d'un compte à partir d'un
> numéro est une fuite.

### 2.2 Moi

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `GET` | `/moi/capacites` | Le contexte de composition ([§ 1.9](#19-le-contexte--ce-qui-compose-linterface)) | — |
| `GET` | `/moi/profil` | Nom, langue, coordonnées | — |
| `PATCH` | `/moi/profil` | Langue, coordonnées | — |
| `GET` | `/moi/enfants` | Les élèves dont je suis responsable, et mes rubriques | — |
| `GET` | `/moi/notifications` | Filtrables par domaine et urgence | — |
| `POST` | `/moi/telephone` | Demander le changement de son numéro : un code part vers le **nouveau** | — |
| `POST` | `/moi/telephone/verification` | Vérifier ce code ; l'identifiant change, l'ancien numéro est informé | — |

### 2.3 Tenant, établissements, country pack

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `GET` | `/etablissements` | Ceux où j'ai une affectation | — |
| `GET` | `/etablissements/{id}` | Fiche | — |
| `PATCH` | `/etablissements/{id}` | Coordonnées, agrément, tutelle | `tenant.etablissement.gerer` |
| `GET` | `/etablissements/{id}/sites` | | — |
| `POST` | `/etablissements/{id}/sites` | | `tenant.site.creer` |
| `GET` | `/country-pack` | Le pack actif, en lecture | — |
| `GET` | `/parametres` | Paramètres effectifs, portée résolue | — |
| `PUT` | `/parametres/{cle}` | Poser une valeur à une portée | `tenant.parametre.definir` |

`TEN_PARAMETRE_INCONNU` (`422`), `TEN_PORTEE_INVALIDE` (`422`), `TEN_VALEUR_INVALIDE` (`422`,
`details.type_attendu` — clé connue, valeur d'un autre type que celui du catalogue),
`TEN_COUNTRY_PACK_FIGE` (`409`), `TEN_ETABLISSEMENT_REQUIS` (`400`), `TEN_RESSOURCE_INTROUVABLE` (`404`),
`TEN_RESSOURCE_DEJA_EXISTANTE` (`409`).

> **Une clé hors catalogue et une portée invalide sont des règles métier, pas des refus de schéma** :
> le corps est valide, `422` avec un code de domaine — c'est le `code`, jamais le statut seul, qui les
> distingue de `VAL_SCHEMA_INVALIDE` ([§ 1.8](#18-codes-http)).
>
> **`TEN_RESSOURCE_INTROUVABLE` est le refus par défaut de tout le socle** : une ressource hors du
> périmètre du tenant répond `404`, jamais `403` — un statut ne dit pas si la ligne d'un autre
> établissement existe. **L'unique exception est l'en-tête `X-Nelo-Etablissement`**, où le refus porte
> sur l'affectation du compte et non sur l'existence d'une ressource : `403 TEN_ETABLISSEMENT_NON_AUTORISE`
> ([§ 1.2](#12-authentification)).
>
> **`TEN_RESSOURCE_DEJA_EXISTANTE`** — le même identifiant fourni par le client, présenté avec une
> **autre** clé de requête. Un rejeu porte la même clé et renvoie la même réponse
> ([§ 1.3](#13-idempotence)) ; deux créations distinctes du même identifiant sont une erreur de
> client, et le contrat la nomme plutôt que de l'écraser. Un module qui a mieux à dire le dit sous son
> propre préfixe — `SCO_MATRICULE_DEJA_PRIS` en est le cas nommé.

### 2.4 Personnes, foyers, responsabilités

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `GET` | `/personnes` | Recherche par nom ou téléphone, bornée au périmètre | `personnes.annuaire.consulter` |
| `POST` | `/personnes` | | `personnes.personne.creer` |
| `GET` | `/personnes/{id}` | | `personnes.annuaire.consulter` |
| `PATCH` | `/personnes/{id}` | | `personnes.personne.modifier` |
| `GET` | `/foyers/{id}` | Membres, adresse, solde consolidé | `personnes.foyer.consulter` |
| `POST` | `/foyers` | | `personnes.foyer.creer` |
| `GET` | `/eleves/{id}/responsables` | Liens qualifiés, rangs, quotes-parts | `scolarite.dossier.consulter` |
| `POST` | `/eleves/{id}/responsables` | Créer un lien | `personnes.lien.gerer` |
| `PATCH` | `/liens/{id}` | Nature, rangs, quote-part, rubriques | `personnes.lien.gerer` |
| `POST` | `/liens/{id}/cloture` | Clore un lien — **jamais de `DELETE`** | `personnes.lien.gerer` |
| `GET` | `/eleves/{id}/personnes-autorisees` | Avec photo et pièce | `vie_scolaire.sortie.controler` |
| `GET` | `/classes/{id}/personnes-autorisees.pdf` | **Imprimable par classe** | `vie_scolaire.sortie.controler` |

`PER_QUOTE_PART_INCOMPLETE` (la somme n'atteint pas 100 %), `PER_CONTACT_RANG_1_MANQUANT`,
`PER_TROIS_FOYERS_REFUSE`, `PER_LIEN_DEJA_CLOS`.

### 2.5 Capacités, rôles, affectations

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `GET` | `/capacites` | Le référentiel, avec `cloisonnee` | `habilitations.role.gerer` |
| `GET` | `/modeles-role` | Livrés par l'éditeur + clonés par l'établissement | `habilitations.role.gerer` |
| `POST` | `/modeles-role` | Cloner et ajuster | `habilitations.role.gerer` |
| `GET` | `/affectations` | Filtrable par personne, année, périmètre | `habilitations.affectation.gerer` |
| `POST` | `/affectations` | Personne + rôle + **périmètre** + année | `habilitations.affectation.gerer` |
| `POST` | `/affectations/{id}/fin` | Fin à date, ou immédiate | `habilitations.affectation.gerer` |
| `POST` | `/affectations/delegation` | Intérim borné — **date de fin obligatoire** | `habilitations.delegation.accorder` |
| `POST` | `/acces-nominatifs` | Accorder une capacité **cloisonnée**, avec motif et fin | ▣ `habilitations.acces_nominatif.accorder` |
| `GET` | `/revue-acces` | Comptes actifs et périmètres, exportable | `habilitations.revue.consulter` |
| `GET` | `/journal-acces` | Lectures de données cloisonnées | ▣ `habilitations.journal.consulter` |
| `POST` | `/comptes/{id}/suspension` | Immédiate, révoque les sessions | `habilitations.compte.suspendre` |
| `POST` | `/comptes` | Créer le compte d'une personne et envoyer son lien d'activation ; un second compte sur un numéro exige la **déclaration de partage familial** | `habilitations.compte.gerer` |
| `POST` | `/comptes/{id}/invitation` | Renvoyer un lien d'activation ; le précédent est invalidé | `habilitations.compte.gerer` |
| `POST` | `/comptes/{id}/telephone` | Changer le numéro d'une personne qui n'a plus l'ancien ; révoque les sessions, oublie les appareils | `habilitations.compte.gerer` |

`HAB_CAPACITE_CLOISONNEE_NON_ROLABLE`, `HAB_DELEGATION_SANS_FIN`, `HAB_PERIMETRE_HORS_AFFECTATION`,
`HAB_ACCES_NOMINATIF_REQUIS`, `HAB_CAPACITE_NON_RECONDUITE`.

> **`HAB_CAPACITE_CLOISONNEE_NON_ROLABLE` est un refus de conception, pas de configuration.** Il ne
> se contourne par aucun réglage. C'est la garantie de [02-domaine § 3.5](02-domaine.md#35-le-cloisonnement--hors-du-système-de-rôles).

### 2.6 Années et périodes

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `GET` | `/annees` | Avec leur état | — |
| `POST` | `/annees` | Ouvrir N+1 en `preparation` | `annees.annee.ouvrir` |
| `POST` | `/annees/{id}/duplication` | Structure, matières, coefficients, tarifs — paramétrable | `annees.annee.dupliquer` |
| `POST` | `/annees/{id}/activation` | | `annees.annee.activer` |
| `POST` | `/annees/{id}/cloture` | **Refusable**, avec la liste des blocages | `annees.annee.cloturer` |
| `GET` | `/annees/{id}/cloture/verification` | **Le pendant : ce qui bloquerait, avant de tenter** | `annees.annee.cloturer` |
| `GET` | `/periodes` | | — |
| `POST` | `/periodes/{id}/cloture` | Gèle les notes de la période | `annees.periode.cloturer` |

`ANN_DEUX_ANNEES_ACTIVES`, `ANN_ANNEE_CLOTUREE`, `ANN_PERIODES_CHEVAUCHANTES`,
`ANN_CLOTURE_BLOQUEE` (`details.blocages[]` : notes non saisies, bulletins non publiés, échéances
ouvertes).

### 2.7 Structure pédagogique

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `GET` | `/niveaux` · `/series` · `/matieres` | Référentiels de l'année | — |
| `GET` | `/classes` | Filtrable par niveau, série, site | — |
| `POST` | `/classes` | | `pedagogie.classe.creer` |
| `GET` | `/classes/{id}/eleves` | | `scolarite.dossier.consulter` |
| `GET` | `/groupes` · `POST` `/groupes` | Options, langues, TP, soutien | `pedagogie.groupe.gerer` |
| `POST` | `/groupes/{id}/membres` | | `pedagogie.groupe.gerer` |
| `GET` | `/enseignements` | Matière × niveau × série, avec coefficient | — |
| `POST` | `/enseignements` | | `pedagogie.enseignement.gerer` |
| `POST` | `/services-enseignants` | Rattacher un enseignant à un enseignement et une classe | `pedagogie.service.gerer` |
| `PUT` | `/classes/{id}/professeur-principal` | | `pedagogie.classe.creer` |
| `GET` | `/edt` | Emploi du temps, filtrable | — |
| `PUT` | `/edt/seances` | Saisie manuelle au MVP | `pedagogie.edt.publier` |

`STR_ELEVE_DEUX_CLASSES`, `STR_EFFECTIF_DEPASSE` (**avertissement, `200` avec `alertes[]`**, pas un
refus), `STR_STRUCTURE_FIGEE_NOTES_SAISIES` (`409`), `STR_COEFFICIENT_SUR_MATIERE_REFUSE`.

> **Au primaire — le segment du MVP** : `/series` répond une collection vide, `serie_code` est absent
> partout, et le même enseignant porte autant de `services-enseignants` qu'il enseigne de matières sur
> sa classe. **Aucune route ne change** ; c'est la démonstration que la structure était bien
> agnostique ([ADR 018](adr/018-le-mvp-commence-par-le-primaire.md)).

### 2.8 Scolarité

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `GET` | `/eleves` | Recherche, bornée au périmètre | `scolarite.dossier.consulter` |
| `POST` | `/eleves` | | `scolarite.eleve.creer` |
| `GET` | `/eleves/{id}` | **La fiche unique** — les blocs varient selon les capacités | `scolarite.dossier.consulter` |
| `GET` | `/inscriptions` | Filtrable par année, classe, état | `scolarite.dossier.consulter` |
| `POST` | `/inscriptions` | Ouvrir une candidature | `scolarite.inscription.creer` |
| `GET` | `/inscriptions/{id}/pieces` | Complétude du dossier | `scolarite.dossier.consulter` |
| `POST` | `/inscriptions/{id}/pieces` | Déposer une pièce | `scolarite.dossier.completer` |
| `POST` | `/inscriptions/{id}/validation` | | `scolarite.inscription.valider` |
| `GET` | `/inscriptions/{id}/validation/verification` | **Le pendant : ce qui manque, avant de tenter** | `scolarite.inscription.valider` |
| `POST` | `/inscriptions/{id}/derogation` | Valider malgré un dossier incomplet — motif obligatoire | `scolarite.derogation.accorder` |
| `POST` | `/inscriptions/{id}/affectation-etat` | Rattacher à une décision d'affectation | `scolarite.affectation_etat.gerer` |
| `POST` | `/transferts` | Arrivée, départ, radiation | `scolarite.transfert.prononcer` |
| `GET` | `/eleves/{id}/carte.pdf` | Carte scolaire avec QR | `scolarite.dossier.consulter` |
| `GET` | `/eleves/{id}/fratrie` | Détectée, pas déclarée | `scolarite.dossier.consulter` |

`SCO_MATRICULE_DEJA_PRIS`, `SCO_DOSSIER_INCOMPLET` (`details.pieces_manquantes[]`),
`SCO_DEJA_INSCRIT_ANNEE_ACTIVE`, `SCO_ANNEE_NON_OUVERTE`.

### 2.9 Évaluation

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `GET` | `/referentiels-evaluation` | Versions, échelle, conversions, formules | — |
| `POST` | `/referentiels-evaluation` | Nouvelle version — **jamais de modification en place** | `evaluation.referentiel.publier` |
| `POST` | `/referentiels-evaluation/{id}/simulation` | Rejouer une formule sur un jeu d'essai | `evaluation.referentiel.publier` |
| `GET` | `/evaluations` | Filtrable par période, enseignement, classe | `evaluation.note.saisir` |
| `POST` | `/evaluations` | Devoir, composition, contrôle continu | `evaluation.evaluation.creer` |
| `GET` | `/evaluations/{id}/notes` | La grille de saisie | `evaluation.note.saisir` |
| `PUT` | `/evaluations/{id}/notes` | **Saisie par lot** — voir ci-dessous | `evaluation.note.saisir` |
| `GET` | `/eleves/{id}/moyennes` | Par période, avec la version du référentiel | `evaluation.note.saisir` |
| `POST` | `/appreciations` | Origine `HUMAINE` ou `IA_VALIDEE` + validateur | `evaluation.appreciation.rediger` |
| `POST` | `/bulletins/calcul` | Sur une classe et une période | `evaluation.bulletin.calculer` |
| `POST` | `/bulletins/{id}/publication` | | `evaluation.bulletin.publier` |
| `GET` | `/bulletins/{id}.pdf` | Porte l'empreinte ; réédition à l'identique | `evaluation.bulletin.calculer` |

**La saisie de notes par lot** — c'est l'écran le plus contraint avec l'appel :

```http
PUT /api/v1/evaluations/{id}/notes
X-Nelo-Requete: 01936b7e-…
{ "lot": [ { "eleve_id": "…", "valeur": "14.25" },
           { "eleve_id": "…", "absent": true } ] }
```

- **Un lot, une clé d'idempotence, une réponse.** Le client envoie des lots de quelques élèves au fil
  de la saisie, pas quarante notes en fin de séance.
- La réponse porte l'état de chaque ligne. **Le client affiche « enregistré » ou « en attente » par
  ligne** — jamais un état global ambigu.
- Un rejeu du même lot ne crée rien et renvoie la même réponse.

`EVA_NOTE_HORS_BORNES`, `EVA_NOTE_VERROUILLEE`, `EVA_ABSENT_AVEC_VALEUR`, `EVA_REFERENTIEL_FIGE` (`409`),
`EVA_FORMULE_INVALIDE`, `EVA_BULLETIN_DEJA_PUBLIE`, `EVA_PERIODE_CLOTUREE`.

> **`EVA_ABSENT_AVEC_VALEUR`** : une absence n'est pas un zéro. Envoyer `absent: true` **et** une
> valeur est une erreur de conception côté client, refusée explicitement.

### 2.10 Vie scolaire

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `GET` | `/seances/du-jour` | **La route d'entrée de l'enseignant** — ses séances, allégée | `vie_scolaire.appel.faire` |
| `GET` | `/seances/{id}/presences` | La grille d'appel | `vie_scolaire.appel.faire` |
| `PUT` | `/seances/{id}/presences` | **Appel par lot**, même contrat que la saisie de notes | `vie_scolaire.appel.faire` |
| `GET` | `/classes/{id}/appel.pdf` | **Liste imprimable à l'avance** | `vie_scolaire.appel.faire` |
| `GET` | `/absences` | Filtrable par élève, classe, état | `vie_scolaire.absence.consulter` |
| `POST` | `/absences/{id}/justificatif` | Déposé par le responsable ou la vie scolaire | — |
| `POST` | `/justificatifs/{id}/traitement` | Accepter ou refuser | `vie_scolaire.justificatif.traiter` |
| `POST` | `/incidents` | | `vie_scolaire.incident.signaler` |
| `POST` | `/sanctions` | | `vie_scolaire.sanction.poser` |
| `POST` | `/autorisations-sortie` | | `vie_scolaire.sortie.autoriser` |
| `POST` | `/controles-sortie` | Vérification de la personne autorisée | `vie_scolaire.sortie.controler` |
| `GET` | `/statistiques/assiduite` | Par classe, niveau, période | `vie_scolaire.absence.consulter` |

`VIE_SEANCE_DEJA_APPELEE`, `VIE_ELEVE_HORS_CLASSE`, `VIE_PERSONNE_NON_AUTORISEE`,
`VIE_JUSTIFICATIF_HORS_DELAI`.

> **`PUT /seances/{id}/presences` émet l'événement d'absence non justifiée dans sa transaction.** Le
> SMS part de l'outbox, pas du handler. Une transaction qui échoue n'envoie rien ; une transaction
> qui réussit envoie toujours.

### 2.11 Conseil de classe et passage

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `POST` | `/conseils` | Convoquer : date, participants, ordre du jour | `conseil.conseil.convoquer` |
| `GET` | `/conseils/{id}/dossier` | **Préparé automatiquement** : moyennes, rang, assiduité, incidents | `conseil.conseil.convoquer` |
| `PUT` | `/conseils/{id}/deliberations` | Appréciation générale, mention, sanction positive | `conseil.deliberation.saisir` |
| `POST` | `/conseils/{id}/cloture` | Produit le PV | `conseil.conseil.convoquer` |
| `POST` | `/decisions-passage` | Par élève | `conseil.decision.arreter` |
| `POST` | `/decisions-passage/{id}/notification` | **Verrouille après notification** | `conseil.decision.notifier` |
| `POST` | `/decisions-passage/{id}/recours` | Dépôt par le responsable | — |
| `GET` | `/conseils/{id}/pv.pdf` | Signé, empreinte | `conseil.conseil.convoquer` |

`CON_QUORUM_NON_ATTEINT`, `CON_DECISION_VERROUILLEE`, `CON_SERIE_CIBLE_MANQUANTE`,
`CON_RECOURS_HORS_DELAI`.

> **Au primaire** : l'instance est le **conseil des maîtres** — le libellé vient du pack, les routes
> ne bougent pas. La composition n'a ni délégué élève ni délégué parent, et
> `CON_SERIE_CIBLE_MANQUANTE` ne se produit pas, faute de série au niveau cible.

### 2.12 Finance

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `GET` | `/grilles-tarifaires` | Versions par année et niveau | — |
| `POST` | `/grilles-tarifaires` | Nouvelle version | `finance.tarif.publier` |
| `POST` | `/factures/generation` | Sur une campagne : un foyer, une facture, lignes par élève | `finance.facture.emettre` |
| `GET` | `/factures/{id}` | Avec échéancier et quotes-parts | `finance.facture.consulter` |
| `GET` | `/foyers/{id}/solde` | Facturé, encaissé, restant dû, par payeur | `finance.facture.consulter` |
| `POST` | `/remises` | **Motif obligatoire** | `finance.remise.accorder` |
| `POST` | `/encaissements` | Espèces ou mobile money | `finance.encaissement.saisir` |
| `GET` | `/encaissements/{id}/recu.pdf` | Numéroté séquentiel par caisse | `finance.encaissement.saisir` |
| `POST` | `/paiements/initiation` | Mobile money, côté famille | — |
| `POST` | `/paiements/webhook/{agregateur}` | **Idempotent**, signature vérifiée | *(externe)* |
| `POST` | `/caisses/{id}/arrete` | Arrêté quotidien, écart expliqué | `finance.caisse.arreter` |
| `GET` | `/caisses/{id}/arrete/verification` | **Le pendant : ce qui bloquerait** | `finance.caisse.arreter` |
| `GET` | `/creances-etat` | Par année de rattachement, avec ancienneté | `finance.creance.consulter` |
| `POST` | `/creances-etat/{id}/attestation-effectif` | La pièce qui déclenche le paiement | `finance.creance.attester` |
| `GET` | `/tableau-bord/tresorerie` | **Facturé, encaissé, encaissable à court terme** | `finance.pilotage.consulter` |
| `POST` | `/relances` | Multicanales, soumises au budget SMS | `finance.relance.envoyer` |
| `GET` | `/reconciliation/{date}` | Écart journal plateforme / relevé opérateur | `finance.reconciliation.consulter` |

`FIN_QUOTE_PART_INCOMPLETE`, `FIN_PAIEMENT_NON_SUPPRIMABLE`, `FIN_RECU_SEQUENCE_TROUEE`,
`FIN_ARRETE_ECART_NON_EXPLIQUE`, `FIN_WEBHOOK_SIGNATURE_INVALIDE`, `FIN_MONTANT_FLOTTANT_REFUSE`,
`FIN_REMISE_SANS_MOTIF`.

> **`FIN_PAIEMENT_NON_SUPPRIMABLE`** : il n'existe aucune route `DELETE` sur un paiement. Le
> remboursement est une écriture inverse, avec sa propre référence.

### 2.13 Communication

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `GET` | `/types-message` | Le référentiel, avec criticité | `communication.routage.gerer` |
| `GET` | `/modeles-message` | Par type, canal et langue | `communication.modele.rediger` |
| `PUT` | `/modeles-message/{id}` | **Variante par canal, rédigée** | `communication.modele.rediger` |
| `GET` | `/politique-routage` | Quel événement, quel canal, quel profil | `communication.routage.gerer` |
| `PUT` | `/politique-routage` | | `communication.routage.gerer` |
| `GET` | `/budget-sms` | Plafond, consommé, seuil d'alerte | `communication.budget.consulter` |
| `POST` | `/circulaires` | Avec périmètre | `communication.circulaire.envoyer` |
| `POST` | `/circulaires/{id}/estimation` | **Le pendant : coût et volume, avant d'envoyer** | `communication.circulaire.envoyer` |
| `GET` | `/envois` | Journal, avec accusés | `communication.envoi.consulter` |
| `GET` | `/conversations` · `POST` `/conversations/{id}/messages` | **Journalisées, non supprimables** | `communication.message.echanger` |
| `POST` | `/rendez-vous` | Parent ↔ enseignant | — |

`COM_BUDGET_SMS_EPUISE`, `COM_HORS_FENETRE_ENVOI`, `COM_MODELE_SMS_TROP_LONG`,
`COM_MESSAGE_NON_SUPPRIMABLE`, `COM_DESTINATAIRE_NON_INSCRIT_RUBRIQUE`.

> **`COM_MODELE_SMS_TROP_LONG` est vérifié à l'enregistrement du modèle, pas à l'envoi.** Découvrir
> à 7 h du matin qu'un modèle dépasse 160 caractères coûte deux SMS par famille.
>
> **Il n'y a pas de route `DELETE` sur un message.** `COM_MESSAGE_NON_SUPPRIMABLE` est le refus
> explicite qui rend la règle testable.

### 2.14 Protection de l'enfance et santé — **cloisonné**

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `POST` | `/signalements` | **`auteur_id` peut être absent** — le signalement confidentiel existe | — |
| `GET` | `/signalements` | | ▣ `protection.signalement.consulter` |
| `POST` | `/signalements/{id}/etapes` | Circuit de traitement | ▣ `protection.signalement.traiter` |
| `POST` | `/signalements/{id}/escalade` | Direction, puis autorité | ▣ `protection.signalement.traiter` |
| `GET` | `/eleves/{id}/dossier-medical` | | ▣ `sante.dossier.consulter` |
| `GET` | `/eleves/{id}/fiche-urgence` | **Non cloisonné** — allergies et protocole | `vie_scolaire.appel.faire` |
| `GET` | `/classes/{id}/fiches-urgence.pdf` | **Imprimable par classe** | `vie_scolaire.appel.faire` |
| `POST` | `/passages-infirmerie` | | ▣ `sante.infirmerie.saisir` |

`HAB_ACCES_NOMINATIF_REQUIS`, `PRO_MOTIF_OBLIGATOIRE`, `PRO_REFERENT_NON_DESIGNE`,
`PRO_ETAPE_NON_MODIFIABLE`.

> **Toute route de ce bloc écrit dans `journal_acces`, y compris en lecture, y compris en cas de
> refus.** C'est la seule famille de routes où le refus lui-même est une donnée.
>
> **`POST /signalements` n'exige aucune capacité** : tout membre du personnel peut signaler. C'est
> délibéré, et c'est la raison d'être du registre.
>
> **Ces routes sont les seules à atteindre `modules/metier/protection/`.** Aucun autre paquet ne
> l'importe : le cloisonnement est une **frontière d'import**, tenue par trois verrous — déclaration
> de dépendances, graphe d'imports, surface de l'`__init__.py` (porte **P-11**). Un compilateur
> refusait, un test signale ; **c'est plus faible, et c'est écrit**
> ([ADR 017](adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md)). En pratique : **aucune route
> hors de ce bloc ne renvoie un champ issu du schéma `protection`**, agrégat compris.

### 2.15 Import et migration

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `POST` | `/imports` | Déposer un fichier Excel ou CSV | `import.fichier.deposer` |
| `GET` | `/imports/{id}/correspondances` | **Proposition de correspondance de colonnes** (C5) | `import.fichier.deposer` |
| `PUT` | `/imports/{id}/correspondances` | Corriger la correspondance | `import.fichier.deposer` |
| `POST` | `/imports/{id}/simulation` | **Ce qui serait créé, modifié, rejeté — sans rien écrire** | `import.fichier.deposer` |
| `POST` | `/imports/{id}/execution` | | `import.execution.lancer` |
| `GET` | `/imports/{id}/rapport` | Lignes rejetées et pourquoi | `import.fichier.deposer` |

`IMP_COLONNE_NON_RECONNUE`, `IMP_LIGNES_REJETEES`, `IMP_SOLDE_REPRISE_DESEQUILIBRE`,
`IMP_ANNEE_TRANSITION_REQUISE`.

> **La simulation est obligatoire avant l'exécution.** Une reprise de soldes de scolarité qui se
> découvre fausse après écriture est le pire scénario de mise en service.

### 2.16 Pilotage et console éditeur

| Méthode | Route | Rôle | Cap. |
|---|---|---|---|
| `GET` | `/tableau-bord` | Effectifs, assiduité, réussite, trésorerie, créance État | `pilotage.tableau_bord.consulter` |
| `GET` | `/journal-audit` | Filtrable, en lecture seule | `pilotage.audit.consulter` |
| `GET` | `/journal-ia` | Capacité, modèle, données, sortie, validateur | `pilotage.audit.consulter` |
| `GET` | `/export-etablissement` | **Export complet, format ouvert, à tout moment** | `tenant.export.demander` |
| `GET` | `/sante` | Sonde | *(publique)* |
| `GET` | `/editeur/tenants` · `/editeur/consommations` | Console éditeur, hors tenant | *(console)* |

> **`/export-etablissement` n'est pas une fonction de confort.** C'est l'argument de vente contre la
> peur de l'enfermement, et c'est la raison pour laquelle il est dans le MVP.

---

## 3. Règles de conception opposables

1. **Toute route d'écriture émet un événement outbox dans sa transaction.** Une route qui n'en émet
   pas doit dire pourquoi dans sa documentation.
2. **Toute route qui refuse pour une raison métier renvoie de quoi construire l'issue** dans
   `details` — pas seulement un code.
3. **Toute route dont le refus est prévisible expose son pendant de vérification.**
   `/inscriptions/{id}/validation/verification`, `/annees/{id}/cloture/verification`,
   `/caisses/{id}/arrete/verification`, `/circulaires/{id}/estimation`, `/imports/{id}/simulation`.
   *Un refus est annoncé avant la saisie, jamais après — et il dit son versant positif.*
4. **Aucune route ne renvoie un secret déjà écrit** : PIN, clé d'agrégateur, jeton d'invitation
   consommé. On répond « présent » ou « absent ».
5. **Aucune route ne renvoie de donnée personnelle sans capacité explicite.** Le numéro de pièce
   d'identité, la date de naissance complète et le téléphone ne sont **jamais dans une liste**,
   seulement dans un détail.
6. **Aucune route ne renvoie un libellé métier en dur.** Elle renvoie un code et une clé i18n ; le
   country pack et le lexique décident du mot affiché.
7. **Toute route pédagogique exige `X-Nelo-Annee`.** Pas de repli implicite.
8. **Une route neuve entre dans ce fichier dans le même changement** que son handler.

---

**Suite** → [04-roadmap.md](04-roadmap.md) — l'ordre de construction.
