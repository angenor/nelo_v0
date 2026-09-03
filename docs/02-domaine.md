# 02 — Domaine

*Source de vérité du modèle. Toute phase de planification en dérive ; aucune n'invente.*

> **Si une tranche a besoin d'une entité, d'un état ou d'un champ absent d'ici, elle propose un diff
> explicite sur ce fichier AVANT de continuer.** Elle ne diverge pas localement. Un modèle local qui
> s'écarte de celui-ci n'est pas un raccourci : c'est une deuxième vérité, et elle gagnera.

---

## 0. Les règles qui traversent tout le modèle

| # | Règle | Ce qu'elle empêche |
|---|---|---|
| **R1** | **Toute donnée d'élève est une donnée de mineur.** Base légale, durée de conservation et journal d'accès sont définis pour chaque traitement, dans le modèle | Qu'une catégorie de donnée existe sans qu'on sache qui peut la lire, combien de temps, et à quel titre |
| **R2** | **Tout montant est un entier d'unité mineure**, avec l'exposant porté par la devise du country pack — `0` pour le XOF, `2` pour le GHS. Jamais de flottant | Des arrondis sur des sommes d'argent, et un modèle qui suppose que toute devise a des centimes |
| **R3** | **Toute note est `NUMERIC`.** Jamais un flottant, jamais un entier | Qu'une note de 14,25 devienne 14, et qu'une moyenne devienne indéfendable |
| **R4** | **Toute entité pédagogique est rattachée à une année scolaire.** Rien n'est « global » — ni une classe, ni un coefficient, ni un tarif, ni une affectation de rôle | Que les classes de 2026-2027 écrasent celles de 2025-2026, et qu'un bulletin archivé devienne faux |
| **R5** | **Tout référentiel est versionné.** Un bulletin réédité trois ans plus tard reflète le barème de l'époque, pas le barème courant | Que la réédition d'un document officiel produise un autre résultat que l'original |
| **R6** | **RLS activée et forcée sur chaque table**, `SET LOCAL app.current_tenant` dans chaque transaction — **et vérification applicative en plus**. Double barrière | Qu'un seul oubli, en base ou dans le code, laisse fuir les données d'un établissement vers un autre |
| **R7** | **Les modules ne partagent jamais de transaction de base de données.** `finance` ne fait pas de `SELECT` dans `scolarite.eleve` : il appelle l'interface du module `scolarite` | Que l'extraction future d'un service devienne impossible, quelle que soit la propreté des interfaces |
| **R8** | **Aucune logique métier ne dépend du pays autrement que par le country pack.** Aucun `if pays == "CI"` | Que chaque nouveau pays devienne un déploiement au lieu d'une donnée |
| **R9** | **Le serveur est la seule autorité.** L'interface masque, l'API refuse — chaque appel revérifie la capacité **et** le périmètre | Qu'un élément d'interface masqué soit pris pour une protection |
| **R10** | **Une action non autorisée est absente de l'écran, jamais grisée** | Le bruit, et l'invitation à réclamer des droits |
| **R11** | **Toute écriture porte une clé d'idempotence**, et sa réponse est mémorisée | Qu'une coupure au mauvais moment crée un doublon d'appel, de note ou de paiement |
| **R12** | **Tout changement d'état métier écrit un événement outbox dans la même transaction** | Qu'un SMS parte sans que l'événement soit enregistré, ou l'inverse |
| **R13** | **Un rattachement inter-modules est un IDENTIFIANT, jamais une clé étrangère.** L'intégrité référentielle est portée par l'application et testée, pas par la base | Qu'une contrainte inter-schémas rende l'extraction d'un module impossible — *une clé étrangère ne survit pas à la séparation en deux bases* |

Deux règles de nommage en découlent :

- **Les tables et les colonnes sont en français.** C'est la convention du projet.
- **Le vocabulaire visible ne l'est jamais.** Chaque entité de référentiel porte un `code` neutre et
  stable (`CLASSE`, `PERIODE`, `PROFESSEUR_PRINCIPAL`) ; ses libellés `fr` et `en` viennent du country
  pack. Le glossaire est en [§ 15](#15-glossaire-des-concepts-neutres) ; `docs/design/lexique.md` fait
  foi sur ce qui s'affiche.

---

## 1. Schéma `tenants`

### 1.1 Hiérarchie

```
tenant  (le groupe scolaire ou la fondation qui souscrit)
  └── etablissement  (1..n)  — l'unité pédagogique et juridique
        ├── site            (1..n)  — l'implantation physique
        ├── cycle_actif     (1..n)  — préscolaire, primaire, secondaire 1er/2nd cycle…
        └── module_actif    (0..n)  — ce que l'établissement a souscrit au-delà du socle
```

Le **groupe scolaire multi-cycles** — une même fondation exploitant maternelle, primaire, collège et
lycée, parfois sur plusieurs sites — est le client type. Le modèle le suppose, il ne l'ajoute pas.

**Le MVP n'en sert qu'un cycle : le primaire**
([ADR 018](adr/018-le-mvp-commence-par-le-primaire.md)). Le modèle, lui, ne connaît aucun segment et
n'en connaîtra jamais : `cycle_actif` est une donnée, et c'est tout ce qui distingue une maternelle
d'un lycée dans ces tables.

### 1.2 Entités

| Table | Champs porteurs de sens |
|---|---|
| **`tenant`** | `nom`, `raison_sociale`, `pays_code`, `country_pack_version`, `statut_abonnement`, `branding` |
| **`etablissement`** | `tenant_id`, `nom`, `code_officiel`, `agrement`, `fuseau_horaire`, `telephone`, `direction_regionale` |
| **`site`** | `etablissement_id`, `nom`, `adresse`, `commune`, `latitude`, `longitude` |
| **`cycle_actif`** | `etablissement_id`, `cycle_code`, `actif_depuis` |
| **`module`** | Référentiel : `code`, `libelle_cle`, `implemente` (booléen) |
| **`module_actif`** | `etablissement_id`, `module_code`, `configuration` |
| **`country_pack`** | `pays_code`, `version`, `contenu` (JSONB), `publie_le`. **Versionné, jamais modifié en place** |
| **`parametre_catalogue`** | `cle`, `portee_la_plus_basse`, `type`, `valeur_defaut`, `description_cle` |
| **`parametre_valeur`** | `cle`, `portee` (`TENANT` \| `ETABLISSEMENT` \| `SITE` \| `CYCLE`), `portee_id`, `valeur` |

### 1.3 Ce que porte un country pack

C'est le seul endroit où le pays existe. Contenu, versionné d'un bloc :

structure des cycles et niveaux avec libellés `fr`/`en` · découpage de l'année (trimestres, semestres,
terms) et calendrier type · **référentiel d'évaluation** (échelle, table de conversion, formules,
gabarit de bulletin) · examens officiels et leur calendrier · référentiel des séries et filières ·
plan comptable et régime fiscal · opérateurs de paiement disponibles · autorité de protection des
données et formalités · ministères de tutelle et formats de remontée · devise et son exposant, format
de date, format de numéro de téléphone, langues · **vocabulaire métier** ([§ 15](#15-glossaire-des-concepts-neutres)).

### 1.4 Invariants

- **Un tenant a exactement un pays et une version de country pack active.** Le changement de version
  est une opération explicite, journalisée, jamais implicite au déploiement.
- **Une entité qui existe dans un country pack et pas dans un autre ne crée aucune colonne
  conditionnelle.** Elle vit dans le `contenu` JSONB, ou elle n'existe pas.
- **L'interface ne montre jamais un module ou un cycle inactif.** Pas de grisé, pas de « disponible
  dans votre offre » : absent.
- **La tarification de l'abonnement est indépendante du nombre de sites et d'établissements.** Elle
  se calcule sur l'élève actif ([§ 14](#14-schéma-editeur)).
- Résolution de configuration : `tenant → établissement → site → cycle`, avec surcharge locale. Un
  seul trait la porte, testé y compris sur les surcharges partielles.

### 1.5 Test d'agnosticité — permanent

Un tenant portant un **country pack fictif minimal** — un cycle, un niveau, une échelle de notation
sur 10, un découpage en deux périodes — fonctionne de bout en bout : inscription, appel, note,
bulletin, facture, encaissement.

> C'est la preuve formelle qu'aucune règle ivoirienne n'a fui dans le code.
> **S'il tombe, le pays s'est glissé dans la logique métier sans qu'on le voie.**

---

## 2. Schéma `personnes`

Raisonner en « parents » ne suffit pas, et la réalité n'est pas modélisable a posteriori.

### 2.1 Trois entités distinctes, jamais confondues

| Entité | Ce que c'est | Ce que ce n'est pas |
|---|---|---|
| **`personne`** | Un être humain. **Source de vérité unique** | Un compte, ni un rôle |
| **`foyer`** | Un regroupement d'adressage et de facturation | Une famille au sens biologique |
| **`lien_responsabilite`** | Le rattachement qualifié d'une `personne` à un `eleve` | Une simple étiquette « parent » |

Une même personne peut être **simultanément** parente d'un élève, enseignante vacataire de
l'établissement et membre du bureau de l'APE : **un seul enregistrement, trois rattachements.**

### 2.2 Entités

| Table | Champs porteurs de sens |
|---|---|
| **`personne`** | `nom`, `prenoms`, `date_naissance`, `sexe`, `telephone_principal`, `telephones_secondaires`, `email?`, `piece_identite`, `photo_url?`, `langue_preferee` |
| **`foyer`** | `libelle`, `adresse`, `commune`, `telephone_contact` |
| **`membre_foyer`** | `foyer_id`, `personne_id`, `role_dans_foyer` |
| **`lien_responsabilite`** | `personne_id`, `eleve_id`, `nature`, `autorite_parentale`, `rang_contact`, `quote_part_financiere`, `autorise_a_recuperer`, `actif`, `date_fin?` |
| **`destinataire_communication`** | `lien_id`, `rubrique` (`SCOLAIRE` \| `FINANCIER` \| `DISCIPLINAIRE` \| `SANTE`), `destinataire` (booléen) |
| **`personne_autorisee_recuperation`** | `eleve_id`, `personne_id`, `piece_identite`, `photo_url`, `valide_du`, `valide_au?` |
| **`historique_responsabilite`** | Journal **immuable** de tout changement de lien : `lien_id`, `champ`, `avant`, `apres`, `auteur_id`, `horodatage` |

### 2.3 La typologie des liens — pourquoi chaque attribut est indispensable

| Attribut | Valeurs | Ce qu'il décide |
|---|---|---|
| `nature` | `PERE`, `MERE`, `TUTEUR_LEGAL`, **`TUTEUR_DE_FAIT`**, `GRAND_PARENT`, `ONCLE_TANTE`, `AINE_FRATRIE`, `EMPLOYEUR`, `INSTITUTION` | Le **tuteur de fait** — l'enfant confié à un parent en ville pour la scolarité — est extrêmement fréquent en Afrique de l'Ouest. Il n'est pas un cas limite |
| `autorite_parentale` | `OUI` \| `NON` \| `PARTAGEE` | Qui peut autoriser une sortie, une opération, un changement d'établissement |
| `rang_contact` | `1..n` | L'ordre d'appel en cas d'urgence |
| `destinataire_communication` | par rubrique | Le père reçoit la facture, la mère les absences. Ce n'est pas une préférence : c'est le modèle |
| `quote_part_financiere` | pourcentage | La facturation éclatée entre deux payeurs |
| `autorise_a_recuperer` | booléen + pièce | Sécurité physique, pas confort |
| `actif` + `date_fin` | | Décès, déchéance, changement de tuteur |

### 2.4 Invariants

- **Un élève relève de un ou deux foyers.** Deux est le cas de la garde alternée ; au-delà, c'est une
  erreur de saisie et le modèle la refuse.
- **La somme des `quote_part_financiere` actives d'un élève vaut 100 %**, ou la facturation est
  refusée avec un message explicite. Jamais un arrondi silencieux.
- **Au moins un lien actif porte `rang_contact = 1`.** Un élève sans contact d'urgence ne s'inscrit
  pas.
- **Un lien ne se supprime jamais** : il se clôt par `actif = false` et `date_fin`, et le changement
  s'écrit dans `historique_responsabilite`.
- **La fratrie se détecte, elle ne se déclare pas** : deux élèves partageant un foyer ou un lien de
  responsabilité de nature parentale sont une fratrie. La remise fratrie s'applique dessus.

---

## 3. Schéma `habilitations`

**Le point le plus structurant du modèle avec le référentiel d'évaluation.** Un système de rôles
fixes ne se transforme pas en autorisation contextuelle par ajout : il se remplace, et avec lui
toutes les vérifications d'accès du produit.

### 3.1 Quatre couches, jamais confondues

| Couche | Ce qu'elle décide |
|---|---|
| **Authentification** | Qui est la personne. Téléphone + OTP, PIN pour les usages fréquents |
| **Capacités** | Ce qu'elle peut faire, par verbe métier |
| **Périmètre** | Sur quoi elle peut le faire — site, cycle, classes, matières, année |
| **Cloisonnement** | Ce que personne ne peut faire par simple appartenance à un rôle ([§ 3.5](#35-le-cloisonnement--hors-du-système-de-rôles)) |

### 3.2 Entités

| Table | Champs porteurs de sens |
|---|---|
| **`compte`** | `personne_id`, `identifiant` (téléphone), `pin_hash?`, `statut`, `derniere_connexion`, `invite_le?` |
| **`capacite`** | Référentiel : `code`, `domaine`, `libelle_cle`, `version_introduction`, `cloisonnee` (booléen) |
| **`modele_role`** | `etablissement_id?`, `code`, `libelle_cle`, `segment`, `livre_par_editeur` (booléen) |
| **`modele_role_capacite`** | `modele_role_id`, `capacite_code` |
| **`affectation`** | `compte_id`, `modele_role_id`, `annee_id`, `perimetre`, `debut`, `fin?`, `delegation_de?` |
| **`perimetre`** | `site_ids[]`, `cycle_codes[]`, `classe_ids[]`, `matiere_ids[]` — vide signifie « tout le périmètre du niveau supérieur » |
| **`acces_nominatif`** | `compte_id`, `capacite_code` **cloisonnée**, `motif`, `accorde_par`, `debut`, `fin?` |
| **`journal_acces`** | **Immuable** : `compte_id`, `capacite_code`, `ressource`, `motif?`, `horodatage`, `adresse_ip` |

### 3.3 Le nommage des capacités

**Par verbe métier, jamais par opération technique.** `domaine.objet.verbe` :

```
scolarite.inscription.valider      pedagogie.edt.publier         evaluation.note.saisir
scolarite.dossier.consulter        pedagogie.cahier.rediger      evaluation.bulletin.publier
finance.encaissement.saisir        vie_scolaire.appel.faire      conseil.decision.arreter
finance.remise.accorder            vie_scolaire.sanction.poser   communication.circulaire.envoyer
```

**Ordre de grandeur visé : 5 à 12 capacités par service.** Trop fines, elles rendent l'administration
illisible pour un censeur ; trop grossières, elles empêchent la séparation scolarité / pédagogie.

### 3.4 Composition de l'interface — les règles

Les capacités effectives d'une personne sont l'**union** de ses affectations. L'interface se compose
à partir de cette union, jamais à partir d'une liste de rôles.

| Élément | Règle |
|---|---|
| **Navigation** | Un domaine n'apparaît que si la personne détient au moins une capacité dedans. **Pas de menu grisé** |
| **Densité** | Deux ou trois domaines s'affichent à plat ; au-delà de cinq, regroupement par famille |
| **Écran d'accueil** | Un utilisateur mono-domaine atterrit **dans son domaine**, jamais sur un tableau de bord presque vide. Multi-domaines : un tableau composé des blocs de chaque domaine, réordonnables |
| **Écrans partagés** | **Une fiche élève unique**, dont les onglets varient. L'éducateur y voit la discipline, l'économe le solde, l'enseignant les notes de ses seules matières, l'infirmier rien — sauf accès nominatif. Une fiche, plusieurs vues, jamais quatre écrans concurrents |
| **Recherche et exports** | Ne portent que sur le périmètre autorisé. **Un export n'est jamais une porte dérobée** vers ce que l'écran refuse d'afficher |
| **Notifications** | Une personne ne reçoit que les alertes de ses domaines. Le cumul de rôles ne produit pas un cumul de bruit : regroupement par domaine |
| **Aucune capacité** | Message explicite renvoyant vers l'administrateur de l'établissement. Jamais une page vide, jamais une erreur technique |

### 3.5 Le cloisonnement — hors du système de rôles

Ces capacités portent `cloisonnee = true` et **ne sont pas ajoutables à un modèle de rôle** :

dossier médical et infirmerie · dossier psychosocial · signalements de protection de l'enfance ·
dossier disciplinaire en cours d'instruction · éléments de paie individuels.

Elles s'attribuent **nominativement**, une personne à la fois, avec motif, date de fin et traçabilité.
Sans cette exception, il suffirait d'ajouter une capacité à un rôle largement distribué pour ouvrir
le dossier psychosocial de tous les élèves.

> **Un chef d'établissement n'a pas accès par défaut au contenu d'un signalement qui le concerne.**
> C'est la raison d'être de la couche, et son test.

Le cloisonnement a aussi une forme structurelle, et elle prime sur le système de rôles : **aucun
paquet n'importe `modules/metier/protection/`**. C'est une **frontière d'import**, tenue par trois
verrous — aucune déclaration de dépendance, un test de graphe d'imports, et un `__init__.py` qui
n'expose rien hors de l'interface de service (porte **P-11**,
[01-stack.md § 7.4](01-stack.md)). **Un compilateur refusait, un test signale** : c'est plus
faible que la garantie d'origine, et c'est dit
([ADR 012](adr/012-le-cloisonnement-est-une-frontiere-de-compilation.md),
[ADR 017](adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md)).

### 3.6 Invariants

- **Une affectation est rattachée à une année scolaire.** Elle expire avec elle et se reconduit
  explicitement, jamais par défaut. À la bascule, une personne non reconduite voit un message clair,
  pas une interface vide.
- **Une délégation temporaire porte une date de fin obligatoire** et expire d'elle-même. Le censeur
  qui remplace le proviseur absent ne garde pas ses droits en septembre.
- **Le départ d'un membre du personnel coupe l'accès le jour même** : suspension immédiate,
  révocation des sessions en cours.
- **Une capacité introduite par une mise à jour n'est jamais accordée automatiquement** aux rôles
  existants. Elle est proposée à l'administrateur de l'établissement, qui décide.
- **Toute lecture d'une donnée cloisonnée écrit dans `journal_acces`**, y compris quand elle
  aboutit. Le journal est en insertion seule.
- **Un compte est individuel côté personnel.** Le partage est toléré côté famille, avec traçabilité.

---

## 4. Schéma `annees`

Techniquement le morceau le plus difficile d'un système d'information scolaire, et le plus souvent
traité trop tard.

### 4.1 Entités

| Table | Champs porteurs de sens |
|---|---|
| **`annee_scolaire`** | `etablissement_id`, `libelle`, `debut`, `fin`, `etat`, `annee_precedente_id?` |
| **`periode`** | `annee_id`, `rang`, `code`, `debut`, `fin`, `etat` |
| **`calendrier`** | `annee_id`, `type` (`VACANCES` \| `FERIE` \| `EXAMEN` \| `CONSEIL`), `libelle_cle`, `intervalle` |

### 4.2 Ce qu'une année scolaire porte en propre

Sa structure pédagogique · sa grille tarifaire · son référentiel d'évaluation · son calendrier · ses
affectations de rôles. **Rien de tout cela n'est global.**

### 4.3 Cycle de vie

```
préparation ──► active ──► clôturée ──► archivée
```

| État | Ce qui est permis |
|---|---|
| **`preparation`** | Duplication de la structure, constitution des classes, campagne d'inscription. **Aucune note, aucun appel** |
| **`active`** | Tout le fonctionnement courant |
| **`cloturee`** | Lecture seule sur les notes et les bulletins. Les opérations financières d'apurement restent ouvertes |
| **`archivee`** | Lecture seule intégrale, pour la durée légale de conservation — **y compris après le départ de l'élève** |

### 4.4 La bascule d'année — le processus le plus sous-estimé

**Deux années coexistent** : on ouvre N+1 en préparation pendant que N est encore active, parce qu'on
réinscrit pour septembre alors que le troisième trimestre n'est pas terminé.

1. Ouverture de N+1 en `preparation`, N restant `active`.
2. Duplication paramétrable de la structure — niveaux, matières, coefficients, tarifs — modifiable.
3. Import des décisions de passage issues des conseils de classe ([§ 9](#9-schéma-conseil)).
4. Constitution des classes N+1.
5. Campagne de réinscription et d'inscription.
6. Clôture de N : gel des notes, archivage des bulletins en PDF, calcul des indicateurs, apurement.
7. Archivage.

### 4.5 Invariants — les règles tranchées

- **Une seule année est `active` par établissement à un instant donné.** Une seule peut être en
  `preparation` en même temps.
- **Un élève ne peut pas être inscrit dans deux années `active`.** Il peut l'être dans une année
  active et une année en préparation — c'est exactement la réinscription.
- **Une note saisie après la clôture est refusée.** La correction d'une note d'année clôturée passe
  par une procédure explicite, tracée, produisant un bulletin rectificatif — jamais par une écriture
  silencieuse.
- **Un bulletin réédité reflète le barème de l'époque**, jamais le barème courant. C'est cette règle
  qui impose R5, le versionnage de tous les référentiels.
- **Aucune période ne chevauche une autre** dans la même année.

---

## 5. Schéma `structure`

Classe, niveau et groupe sont trois notions distinctes qu'il ne faut **jamais** confondre.

### 5.1 Hiérarchie

```
etablissement
 └─ cycle          (préscolaire, primaire, secondaire 1er cycle, 2nd cycle, technique, supérieur)
     └─ niveau     (CP1, CM2, 6e, Tle, L1…)
         └─ serie  (A, C, D ; Science/Arts/Business ; Génie civil…)   — facultative
             └─ classe   (CM2 A, 6e A, Form 2 Blue) ── salle + professeur principal
                 └─ groupe  (soutien lecture, LV2 espagnol, groupe TP 1, option EPS)
```

**Au primaire — le seul segment du MVP** : le cycle est `PRIMAIRE`, les niveaux vont du CP1 au CM2,
**la série reste vide**, et le groupe sert le soutien et l'éducation physique, pas les options ni les
travaux pratiques. Rien n'est retiré du modèle pour autant : `serie_code` est nullable parce que le
secondaire la remplira.

### 5.2 Entités

| Table | Champs porteurs de sens |
|---|---|
| **`cycle`** | Référentiel du country pack : `code`, `libelle_cle`, `rang` |
| **`niveau`** | `annee_id`, `cycle_code`, `code`, `libelle_cle`, `rang`, `niveau_suivant_code?` |
| **`serie`** | `annee_id`, `niveau_code`, `code`, `libelle_cle` |
| **`classe`** | `annee_id`, `niveau_code`, `serie_code?`, `libelle`, `effectif_max`, `salle_id?`, `site_id` |
| **`groupe`** | `classe_id?`, `annee_id`, `libelle`, `type` (`OPTION` \| `LANGUE` \| `TP` \| `SOUTIEN` \| `EPS`) |
| **`membre_groupe`** | `groupe_id`, `eleve_id` |
| **`matiere`** | `annee_id`, `code`, `libelle_cle`, `famille` |
| **`enseignement`** | `annee_id`, `matiere_id`, `niveau_code`, `serie_code?`, `coefficient`, `volume_horaire`, `statut` (`OBLIGATOIRE` \| `OPTIONNEL`), `mode_evaluation` |
| **`service_enseignant`** | `annee_id`, `personne_id`, `enseignement_id`, `classe_id?`, `groupe_id?` |
| **`professeur_principal`** | `annee_id`, `classe_id`, `personne_id` |
| **`salle`** | `site_id`, `libelle`, `capacite`, `type` |
| **`seance_edt`** | `annee_id`, `classe_id?`, `groupe_id?`, `enseignement_id`, `personne_id`, `salle_id?`, `creneau` |

### 5.3 Invariants

- **Un élève appartient à exactement une classe et à `n` groupes** pour une année donnée.
- **Le dédoublement se modélise au niveau du groupe**, jamais de la classe. Une classe scindée en deux
  groupes pour les TP a un emploi du temps et un appel corrects seulement à cette condition ; sinon
  les deux sont faux.
- **Le professeur principal est rattaché au couple (classe, année)**, pas à une personne globalement.
  Au primaire, c'est le **maître titulaire** de la classe, et il porte en plus un `service_enseignant`
  par matière : la polyvalence est un cumul d'affectations, jamais un cas particulier du modèle.
- **Un enseignement porte le coefficient**, pas la matière. Le même français n'a pas le même
  coefficient au CP1 et au CM2, ni en série A et en série C.
- **`effectif_max` est un avertissement, pas un refus** : une classe surchargée existe dans la
  réalité et doit pouvoir exister dans le système, avec un signalement visible.
- **La structure d'une année ne se modifie plus après la première note saisie** sur un enseignement,
  sauf procédure explicite.

---

## 6. Schéma `scolarite`

### 6.1 Entités

| Table | Champs porteurs de sens |
|---|---|
| **`eleve`** | `etablissement_id`, `matricule`, `nom`, `prenoms`, `date_naissance`, `lieu_naissance`, `sexe`, `nationalite`, `photo_url?`, `statut` |
| **`inscription`** | `eleve_id`, `annee_id`, `classe_id`, `regime` (`EXTERNE` \| `DEMI_PENSION` \| `INTERNE`), `etat`, `date_inscription`, `redoublant` |
| **`piece_dossier`** | `inscription_id`, `type_code`, `fichier_url?`, `fournie`, `date_reception?` |
| **`affectation_etat`** | `inscription_id`, `decision_reference`, `cohorte`, `montant_pris_en_charge`, `annee_rattachement` |
| **`bourse`** | `eleve_id`, `annee_id`, `bailleur_type`, `bailleur_nom`, `montant`, `conditions`, `etat` |
| **`prise_en_charge_employeur`** | `eleve_id`, `annee_id`, `employeur_nom`, `plafond`, `reference_convention` |
| **`transfert`** | `eleve_id`, `type` (`ARRIVEE` \| `DEPART` \| `RADIATION`), `etablissement_origine?`, `motif`, `date`, `certificat_url?` |

### 6.2 Cycle de vie d'une inscription

```
candidature ──► dossier_incomplet ──► dossier_complet ──► validee ──► active
                       │                                                 │
                       └──► refusee                                      ├──► transferee
                                                                         ├──► radiee
                                                                         └──► terminee   (fin d'année)
```

### 6.3 Invariants

- **Le matricule est unique par établissement et immuable.** Il suit l'élève sur toute sa scolarité,
  y compris en changeant de cycle au sein du groupe.
- **Une inscription `validee` exige un dossier complet**, ou une dérogation explicite tracée avec son
  auteur et son motif.
- **`affectation_etat` reste vide au primaire** — le segment du MVP : l'État y finance un effectif
  conventionné, pas un élève nommé. La table existe, et elle se remplit avec le segment secondaire
  sans migration ([ADR 018](adr/018-le-mvp-commence-par-le-primaire.md)).
- **Un élève affecté par l'État porte une `affectation_etat`.** La séparation entre ce que l'État
  couvre et ce qui est facturable à la famille est stricte : c'est un sujet contrôlé.
- **Une radiation ne supprime rien.** Le dossier reste consultable pour la durée légale de
  conservation.
- **L'inscription en N+1 pendant que N est active est le fonctionnement normal**, pas un cas limite.

### 6.4 Ce qui n'est PAS ici

Le **solde**, l'**échéancier** et la **créance sur l'État** sont dans [`finance`](#10-schéma-finance).
`scolarite` ne connaît pas de montant, sauf `montant_pris_en_charge` qui est une donnée de la décision
d'affectation, pas un poste comptable. R7 s'applique : `finance` interroge `scolarite` par son
interface, jamais par un `SELECT`.

---

## 7. Schéma `evaluation`

**C'est le point qui décide de la viabilité de l'extension anglophone.** Les deux modèles sont
irréconciliables si le calcul est codé en dur.

### 7.1 Les deux modèles, et pourquoi ils ne se réconcilient pas

| Dimension | Francophone (CI, SN, BF…) | Anglophone (GH, NG…) |
|---|---|---|
| Échelle | Note sur 20 | Pourcentage sur 100 |
| Restitution | Moyenne pondérée par coefficient | Grade code A1 (75-100) à F9 (< 40), C4-C6 valant *credit* |
| Découpage | Trimestres ou semestres | Three terms |
| Composition | Devoirs + compositions, pondérations locales | *Continuous assessment* 30 % + examen externe 70 % |
| Classement | Rang dans la classe, moyenne générale | *Position in class*, par matière et globale |
| Document | Bulletin trimestriel | *Terminal report* |

### 7.2 Le référentiel d'évaluation — une donnée versionnée, pas du code

| Table | Champs porteurs de sens |
|---|---|
| **`referentiel_evaluation`** | `pays_code`, `annee_id`, `version`, `echelle_min`, `echelle_max`, `publie_le`, `gel` (booléen) |
| **`table_conversion`** | `referentiel_id`, `borne_min`, `borne_max`, `code_mention`, `libelle_cle`, `credit` (booléen) |
| **`formule_composition`** | `referentiel_id`, `portee` (`PERIODE` \| `ANNUELLE`), `arbre` (JSONB) — **arbre de calcul déclaratif, jamais du code** |
| **`regle_arrondi`** | `referentiel_id`, `objet`, `decimales`, `mode` (`MATH` \| `SUPERIEUR` \| `INFERIEUR`) |
| **`regle_rang`** | `referentiel_id`, `ex_aequo` (`MEME_RANG` \| `RANG_SUIVANT_DECALE`), `portee` |
| **`gabarit_bulletin`** | `referentiel_id`, `format`, `contenu` |

Le moteur de calcul est un **interpréteur de formules déclaratives**, pas une fonction de calcul
écrite par pays. Sans cela, chaque nouveau pays est un déploiement.

> **Les règles d'arrondi sont une source majeure de contestation.** Elles sont une donnée du
> référentiel, écrite et versionnée — pas une convention implicite du langage.

### 7.3 Entités d'évaluation

| Table | Champs porteurs de sens |
|---|---|
| **`evaluation`** | `annee_id`, `periode_id`, `enseignement_id`, `classe_id?`, `groupe_id?`, `type_code`, `libelle`, `bareme`, `poids`, `date`, `etat` |
| **`note`** | `evaluation_id`, `eleve_id`, `valeur` (**`NUMERIC`**), `absent` (booléen), `dispense` (booléen), `saisie_par`, `saisie_le`, `cle_idempotence` |
| **`moyenne_periode`** | `eleve_id`, `periode_id`, `enseignement_id?`, `valeur`, `rang?`, `referentiel_version`, `calculee_le` |
| **`appreciation`** | `eleve_id`, `periode_id`, `enseignement_id?`, `texte`, `auteur_id`, `origine` (`HUMAINE` \| `IA_VALIDEE`), `validee_par?` |
| **`bulletin`** | `eleve_id`, `periode_id`, `etat`, `referentiel_version`, `pdf_url?`, `publie_le?`, `empreinte` |

### 7.4 Cycle de vie d'une note et d'un bulletin

```
note :      brouillon ──► enregistree ──► verrouillee   (à la clôture de la période)
bulletin :  en_preparation ──► calcule ──► arrete (conseil) ──► publie ──► archive
```

### 7.5 Invariants

- **`valeur` est `NUMERIC`** et se situe dans `[echelle_min, echelle_max]` du référentiel de l'année.
  Hors bornes : refus, jamais écrêtage.
- **Une absence n'est pas un zéro.** `absent = true` avec `valeur = NULL` ; la formule décide de son
  traitement, pas le code de saisie.
- **Une moyenne porte la version du référentiel qui l'a produite.** Elle est recalculable à
  l'identique trois ans plus tard.
- **La saisie s'enregistre par petits lots au fil de l'eau**, pas en un envoi unique. Perdre le réseau
  à la dernière ligne ne coûte jamais quarante saisies. Chaque lot porte sa clé d'idempotence.
- **Aucune note n'est modifiable après verrouillage** sans procédure tracée produisant un bulletin
  rectificatif.
- **Un bulletin publié est immuable** et porte une empreinte. Sa réédition produit le même document.
- **L'IA ne produit jamais une note ni une décision** ([§ 13.3](#133-les-trois-niveaux-dautonomie)).

---

## 8. Schéma `vie_scolaire`

### 8.1 Entités

| Table | Champs porteurs de sens |
|---|---|
| **`seance`** | `annee_id`, `seance_edt_id?`, `classe_id?`, `groupe_id?`, `enseignement_id`, `personne_id`, `date`, `creneau`, `etat_appel` |
| **`presence`** | `seance_id`, `eleve_id`, `etat` (`PRESENT` \| `ABSENT` \| `RETARD` \| `EXCUSE`), `minutes_retard?`, `saisie_par`, `saisie_le`, `cle_idempotence` |
| **`absence`** | `eleve_id`, `intervalle`, `origine_seance_id?`, `etat`, `motif_code?` |
| **`justificatif`** | `absence_id`, `depose_par`, `type`, `fichier_url?`, `etat`, `traite_par?`, `traite_le?` |
| **`incident`** | `eleve_id?`, `classe_id?`, `type_code`, `gravite`, `recit`, `auteur_id`, `date`, `etat` |
| **`sanction`** | `incident_id?`, `eleve_id`, `type_code`, `duree?`, `prononcee_par`, `notifiee_le?`, `etat` |
| **`autorisation_sortie`** | `eleve_id`, `motif`, `demandee_par`, `accordee_par?`, `intervalle`, `etat` |
| **`controle_sortie`** | `eleve_id`, `personne_recuperant_id`, `verifie_par`, `horodatage`, `piece_verifiee` |

### 8.2 L'appel — l'écran le plus contraint de la plateforme

C'est celui qui décide de l'adoption. Il se conçoit **pour un appareil d'entrée de gamme et une
connexion lente**, et rien d'autre ne compte devant cette contrainte.

| Règle | Conséquence |
|---|---|
| **Un geste par élève, une page par séance** | Pas de navigation, pas de modale intermédiaire |
| **Enregistrement au fil de l'eau** | Par petits lots, pas en un envoi de fin de séance |
| **État explicite en permanence** | L'utilisateur voit si sa saisie est **sur le serveur** ou **en attente**. Aucune ambiguïté : c'est là que se perd la confiance |
| **Budget de poids** | L'écran d'appel est le plus léger du produit. Aucune dépendance lourde, aucune image, données paginées |
| **Liste imprimable à l'avance** | Le mode dégradé assumé pour la journée où le réseau tombe |

### 8.3 Invariants

- **Une absence est un intervalle `[début, fin)`**, jamais une paire de dates ni un booléen par
  demi-journée. Le primaire appelle par demi-journée, le secondaire par cours, le supérieur par UE :
  l'intervalle absorbe les trois.
- **L'absence non justifiée déclenche un événement outbox dans la même transaction que l'appel**, et
  la politique de routage décide du canal. Le SMS part sans intervention humaine.
- **Un retard n'est pas une absence.** Il porte ses minutes et alimente ses propres statistiques.
- **La sortie d'un élève exige la vérification de la personne autorisée** ([§ 2.2](#22-entités)).
  C'est un contrôle de sécurité physique, et il s'écrit.
- **Un incident et une sanction sont deux entités distinctes.** Un incident peut n'entraîner aucune
  sanction ; une sanction cite son incident quand il existe.
- **Le dossier disciplinaire en cours d'instruction est cloisonné** ([§ 3.5](#35-le-cloisonnement--hors-du-système-de-rôles)).

---

## 9. Schéma `conseil`

Le conseil de **classe** est le rituel central de l'année. Il ne se confond jamais avec le conseil de
**discipline**, qui relève de [`vie_scolaire`](#8-schéma-vie_scolaire).

**`conseil_classe` est un code, pas un libellé.** Au primaire — le segment du MVP — l'instance est le
**conseil des maîtres** : mêmes tables, même circuit, un libellé qui vient du pack. Ce qui change est
la composition : ni délégués élèves, ni délégués parents. Le quorum, lui, est déjà une donnée.

### 9.1 Entités

| Table | Champs porteurs de sens |
|---|---|
| **`conseil_classe`** | `annee_id`, `periode_id`, `classe_id`, `date`, `quorum_atteint`, `etat` |
| **`participant_conseil`** | `conseil_id`, `personne_id`, `qualite`, `present` |
| **`deliberation`** | `conseil_id`, `eleve_id`, `appreciation_generale`, `mention_code?`, `sanction_positive_code?` |
| **`decision_passage`** | `eleve_id`, `annee_id`, `valeur`, `serie_cible_code?`, `prononcee_le`, `notifiee_le?`, `delai_recours`, `etat` |
| **`recours`** | `decision_id`, `depose_par`, `motif`, `depose_le`, `etat`, `decision_finale?` |
| **`proces_verbal`** | `conseil_id`, `contenu`, `signe_par[]`, `pdf_url`, `empreinte` |

### 9.2 La décision de fin d'année — une entité en soi, avec une valeur juridique

| Valeur | |
|---|---|
| `ADMIS` | En classe supérieure |
| `ADMIS_SOUS_CONDITION` | Avec la condition écrite |
| `REDOUBLEMENT` | |
| `REORIENTATION` | Vers une autre série — `serie_cible_code` obligatoire **dès que le pack déclare des séries au niveau cible**. Au primaire, il n'y en a pas : la valeur existe et ne sert pas |
| `ORIENTATION_TECHNIQUE` | Vers l'enseignement technique |
| `EXCLUSION` | |

### 9.3 Invariants

- **Le dossier du conseil se prépare automatiquement** : moyennes, rang, assiduité, incidents,
  appréciations par matière. Le conseil délibère, il ne compile pas.
- **Une décision se verrouille après notification aux familles.** Avant, elle est modifiable ; après,
  elle ne l'est plus que par la voie de recours.
- **Le délai de recours est une donnée du country pack**, pas une constante.
- **L'issue de fin de cycle peut dépendre d'un examen national** — le passage en sixième au primaire,
  par exemple. Cet examen appartient au ministère : le produit enregistre la décision et son
  résultat, il ne les organise pas.
- **Le procès-verbal est immuable et porte une empreinte.**
- **L'IA ne prononce jamais une décision de passage** ([§ 13.3](#133-les-trois-niveaux-dautonomie)).

---

## 10. Schéma `finance`

Le modèle simple « les parents paient l'école » est faux pour une part majeure des effectifs du privé
ivoirien.

### 10.1 Les cinq circuits de financement

| Circuit | Payeur | Ce qui le distingue |
|---|---|---|
| Scolarité classique | Foyer(s) | Échéancier, remise fratrie, remise personnel, pénalités |
| **Élève affecté / subventionné** | État + complément famille | Circuit et pièces distincts, créance sur l'État |
| Bourse | Tiers (État, entreprise, ONG, diaspora) | Convention, conditions de maintien, justificatifs |
| Prise en charge employeur | Entreprise | Facturation à l'employeur, attestation, plafond |
| Parrainage individuel | Personne physique | Reporting au parrain |

### 10.2 Entités

| Table | Champs porteurs de sens |
|---|---|
| **`grille_tarifaire`** | `annee_id`, `niveau_code?`, `regime?`, `version`, `gel` |
| **`ligne_tarif`** | `grille_id`, `poste_code`, `libelle_cle`, `montant`, `exigible_le`, `obligatoire` |
| **`facture`** | `foyer_id`, `annee_id`, `numero`, `emise_le`, `total_ht`, `total_taxes`, `total`, `etat` |
| **`ligne_facture`** | `facture_id`, `eleve_id`, `poste_code`, `montant`, `quote_part_payeur` |
| **`echeance`** | `facture_id`, `rang`, `montant`, `exigible_le`, `etat` |
| **`remise`** | `facture_id?`, `eleve_id?`, `type_code`, `montant?`, `taux?`, `motif`, `accordee_par` |
| **`paiement`** | `facture_id?`, `foyer_id`, `montant`, `moyen`, `reference_externe?`, `etat`, `encaisse_par?`, `cle_idempotence` |
| **`recu`** | `paiement_id`, `numero` **séquentiel par caisse**, `pdf_url`, `empreinte` |
| **`caisse`** | `site_id`, `libelle`, `responsable_id?` |
| **`arrete_caisse`** | `caisse_id`, `date`, `theorique`, `compte`, `ecart`, `arrete_par`, `etat` |
| **`creance_etat`** | `etablissement_id`, `annee_rattachement`, `effectif_declare`, `effectif_controle`, `effectif_paye`, `montant_du`, `montant_encaisse` |
| **`attestation_effectif`** | `creance_id`, `echeance_reglementaire`, `emise_le`, `pdf_url`, `etat` |
| **`relance`** | `echeance_id`, `canal`, `envoyee_le`, `etat` |

### 10.3 Cycle de vie d'un paiement

```
initie ──► en_attente ──► confirme
              ├──► echoue
              ├──► expire
              └──► rembourse   (par écriture inverse, jamais par suppression)
```

### 10.4 Les exigences non négociables du paiement

| Exigence | Raison |
|---|---|
| **Idempotence stricte** des initiations **et des webhooks** | Les confirmations arrivent en retard, en double, ou jamais |
| **Machine à états explicite** | Sans elle, un paiement en attente et un paiement échoué se confondent |
| **Réconciliation quotidienne automatique** | L'écart entre le journal de la plateforme et le relevé de l'opérateur : c'est là que naissent les litiges |
| **Encaissement espèces avec caisse et arrêté quotidien** | Une part majoritaire des paiements reste en espèces |
| **Reçu numéroté, séquentiel, infalsifiable** | Exigence comptable et culturelle |
| **Aucun paiement supprimable** | Annulation par écriture inverse uniquement |
| **Agrégateur derrière une interface interne** | Pouvoir en changer, ou passer en direct sur les gros volumes, sans toucher la logique métier — [ADR 009](adr/009-agregateur-de-paiement-derriere-une-interface.md) |

### 10.5 Invariants

- **La facture est portée par le foyer, pas par l'élève.** Une fratrie de trois élèves sur deux
  cycles produit **une** facture, avec ses lignes par élève.
- **La quote-part éclate la ligne, pas la facture.** Deux payeurs à 60/40 reçoivent chacun leur
  échéancier et leur solde, sur la même facture.
- **Le tableau de bord distingue trois montants** : *facturé*, *encaissé*, *encaissable à court
  terme*. Faute de quoi il est mensonger pour un établissement conventionné.
- **La créance sur l'État porte son ancienneté par année de rattachement.** Un établissement doit
  sortir l'état de ses arriérés par année en un clic.
- **L'effectif déclaré, l'effectif contrôlé et l'effectif payé sont trois nombres distincts**, et
  leur réconciliation est une opération du modèle, pas un tableur.
- **Un reçu est séquentiel par caisse et sans trou.** Une séquence trouée est une anomalie signalée.
- **Toute remise porte son motif et son auteur.** Aucune remise anonyme.

---

## 11. Schéma `communication`

Le point de départ n'est pas la notification push : c'est qu'une part importante des responsables
légaux n'a **ni smartphone ni forfait data actif**.

### 11.1 La hiérarchie des canaux

| Canal | Usage | Coût | Fiabilité |
|---|---|---|---|
| Notification web | Tout | Nul | Moyenne — dépend de la data |
| WhatsApp Business | Notification riche, échanges | Par conversation | Bonne, dépend de la data |
| **SMS sortant** | Absence, convocation, échéance, résultat, urgence | **Poste de coût majeur** | Très bonne |
| **SMS entrant par mot-clé** *(V2)* | Consultation : solde, absences, échéance | Faible | Très bonne, sans data ni smartphone |
| Voix / SVI *(V3)* | Urgence, illettrisme | Élevé | Bonne |
| **Papier** | Bulletin, convocation, avis de situation | Impression | Totale |

### 11.2 Entités

| Table | Champs porteurs de sens |
|---|---|
| **`type_message`** | `code`, `domaine`, `criticite` |
| **`modele_message`** | `type_code`, `canal`, `langue`, `gabarit`, `longueur_max` |
| **`politique_routage`** | `etablissement_id`, `type_code`, `profil_destinataire`, `canaux_ordonnes[]`, `fenetre_envoi` |
| **`budget_sms`** | `etablissement_id`, `periode`, `plafond`, `consomme`, `seuil_alerte` |
| **`envoi`** | `type_code`, `canal`, `destinataire_personne_id`, `contenu`, `etat`, `cout`, `accuse_reception?`, `envoye_le?` |
| **`circulaire`** | `etablissement_id`, `titre`, `contenu`, `perimetre`, `auteur_id`, `publiee_le?` |
| **`conversation`** | `participants[]`, `contexte_eleve_id?`, `journalisee` (**toujours vrai**) |
| **`message`** | `conversation_id`, `auteur_id`, `contenu`, `envoye_le`, `supprime` (**toujours faux**) |
| **`rendez_vous`** | `personne_id`, `enseignant_id`, `eleve_id`, `creneau`, `etat` |

### 11.3 Invariants

- **Un SMS n'est pas un push tronqué.** Chaque `type_message` porte une variante **rédigée** par
  canal, sous 160 caractères pour le SMS.
- **La politique de routage réserve le SMS unitaire aux événements réellement critiques** — absence
  non justifiée, convocation, échéance dépassée. Le reste passe par l'espace en ligne, WhatsApp ou le
  papier.
- **Les notifications non urgentes se regroupent en un récapitulatif périodique.** Un SMS par
  événement rend le modèle économique intenable.
- **Le budget SMS est vérifié avant l'envoi**, avec alerte de dépassement et facturation à
  l'établissement.
- **Les fenêtres d'envoi respectent les heures ouvrables et les jours de repos.**
- **Une conversation adulte-mineur est journalisée, non supprimable, et visible d'un tiers.** Sans
  exception, sans réglage. *Une plateforme scolaire qui offre un canal privé non tracé entre un
  adulte et un mineur crée un risque qu'elle sera tenue de justifier.*

---

## 12. Schéma `protection` *(cloisonné)*

C'est le domaine où une erreur de conception a les conséquences les plus graves, humaines comme
juridiques. Module dédié et cloisonné — **jamais une fonctionnalité annexe d'un autre service.**

### 12.1 Entités

| Table | Champs porteurs de sens |
|---|---|
| **`signalement`** | `etablissement_id`, `eleve_id?`, `recit`, `auteur_id?` (**nullable — le signalement confidentiel existe**), `depose_le`, `etat`, `gravite_declaree` |
| **`referent_protection`** | `etablissement_id`, `personne_id`, `designe_le`, `fin?` |
| **`etape_traitement`** | `signalement_id`, `type`, `acteur_id`, `horodatage`, `note`, `delai_reglementaire?` |
| **`escalade`** | `signalement_id`, `destinataire` (`DIRECTION` \| `AUTORITE`), `transmise_le`, `reference?` |
| **`suivi_psychosocial`** | `eleve_id`, `referent_id`, `notes[]`, `etat` |
| **`dossier_medical`** | `eleve_id`, `allergies`, `traitements`, `vaccinations`, `groupe_sanguin`, `pathologies` |
| **`fiche_urgence`** | `eleve_id`, `protocole`, `personne_a_prevenir_id`, **imprimable par classe** |
| **`passage_infirmerie`** | `eleve_id`, `motif`, `soins`, `horodatage`, `agent_id` |

### 12.2 Invariants

- **Le circuit est humain et nommé.** Un référent désigné, des délais de traitement, une escalade vers
  la direction puis vers les autorités compétentes.
- **La traçabilité est intégrale et non modifiable.** Chaque étape s'écrit, aucune ne s'efface.
- **La politique de conservation est distincte de celle du dossier scolaire.**
- **Toute lecture écrit dans `journal_acces`, avec motif.** Un accès anormal alerte le responsable.
- **Un chef d'établissement n'a pas accès par défaut** au contenu d'un signalement le concernant.
- **La fiche d'urgence et les allergies sont accessibles au personnel encadrant** — c'est le seul
  fragment non cloisonné du schéma, et il est délibéré : un choc anaphylactique ne se traite pas en
  demandant une habilitation.
- **L'IA agrège des signaux et alerte une personne nommée. Rien d'autre.** Pas de qualification, pas
  de score de risque affiché, pas de décision, pas de notification automatique aux familles
  ([§ 13](#13-lia--six-capacités-trois-niveaux)).

---

## 13. L'IA — six capacités, trois niveaux

### 13.1 Pourquoi pas « un agent par service »

Trente-quatre agents autonomes, c'est en réalité **cinq ou six capacités identiques déclinées par
domaine**. Les construire séparément multiplie par trente-quatre le coût de développement,
d'évaluation et de maintenance, pour une valeur ajoutée nulle. La promesse commerciale peut rester un
argument de présentation ; **l'architecture est celle de six capacités.**

### 13.2 Les six capacités

| Capacité | Ce qu'elle fait | Risque | MVP |
|---|---|---|---|
| **C1 · Rédaction assistée** | Appréciations, courriers, circulaires, PV, traduction FR↔EN | Faible — sortie relue | **Oui**, niveau B |
| **C2 · Question-réponse documentaire** | Chatbot parent, assistant règlement intérieur | Faible à moyen — hallucination | Non |
| **C3 · Planification sous contraintes** | Emploi du temps, constitution des classes, salles d'examen. **Ce n'est pas de l'IA générative : c'est un solveur** | Faible | Non |
| **C4 · Analyse et détection de signaux** | Absentéisme, décrochage, anomalies comptables, prévision de trésorerie | **Élevé quand il s'agit d'élèves** | Non |
| **C5 · Extraction documentaire** | Pièces d'inscription, reçus, import de fichiers désordonnés | Moyen | **Oui** |
| **C6 · Assistance à l'apprentissage** | Quiz, fiches de révision, exercices différenciés | Moyen | Non |

Un « agent » commercial est une **composition de ces capacités avec un jeu d'outils et de données
restreint à un domaine**. C'est un profil de configuration, pas un système distinct.

### 13.3 Les trois niveaux d'autonomie

| Niveau | Définition | Domaines |
|---|---|---|
| **A · Autonome** | L'IA exécute et informe | Rappels de paiement, réponses documentaires factuelles, résumés, traduction, propositions d'emploi du temps |
| **B · Proposition validée** | L'IA propose, **un humain nommé valide avant effet** | Appréciations, courriers officiels, relances, plans de remédiation, constitution des classes |
| **C · Interdit à l'IA** | Décision humaine seule ; l'IA peut au mieux préparer un dossier | **Note finale et décision de passage · sanction disciplinaire · qualification d'une situation de protection de l'enfance · diagnostic ou conseil médical · décision RH individuelle · attribution ou retrait d'une bourse · exclusion d'un élève** |

### 13.4 Invariants

- **Toute sortie d'IA est étiquetée comme telle** et porte le nom du validateur humain lorsqu'elle
  produit un effet.
- **Aucun score de risque individuel d'élève n'est affiché.** C4 produit une alerte à destination
  d'une personne nommée, formulée en **faits observables** — « 7 absences en 3 semaines, moyenne en
  baisse de 4 points » — jamais en jugement.
- **`journal_ia`** : quelle capacité, quel modèle, quelles données, quelle sortie, quel validateur.
  Exigence de conformité et de défense.
- **Ce qui ne doit jamais être de l'IA** : calcul de moyennes, application de barèmes, relances
  d'échéance, contrôle de complétude d'un dossier, génération d'un bulletin. Ce sont des règles
  déterministes. Les faire passer par un modèle de langage est plus lent, plus cher, moins fiable —
  et transforme une opération vérifiable en une opération à auditer.
- **Les deux capacités du MVP vivent dans `modules/socle/assistance/`**, appelées comme n'importe quel
  autre paquet du socle. Il n'y a pas de service d'assistance à déployer ; le service d'inférence, lui,
  est une dépendance externe derrière son interface.
- **La plateforme reste pleinement opérationnelle avec l'assistance désactivée.** La désactivation est
  un **paramètre du catalogue**, posé à sa portée. C'est un test, pas une intention : suspendue,
  l'assistance laisse les appréciations se saisir à la main et l'import se faire par correspondance
  manuelle de colonnes, et **l'affordance disparaît de l'écran** — elle n'est pas grisée.

---

## 14. Schéma `editeur`

| Table | Champs porteurs de sens |
|---|---|
| **`abonnement`** | `tenant_id`, `formule`, `prix_unitaire`, `devise`, `echeancier`, `etat` |
| **`releve_eleve_actif`** | `tenant_id`, `periode`, `effectif`, `calcule_le` |
| **`consommation_sms`** | `tenant_id`, `periode`, `volume`, `cout_reel`, `cout_refacture` |
| **`consommation_ia`** | `tenant_id`, `periode`, `capacite`, `jetons`, `cout` |
| **`acces_support`** | `tenant_id`, `agent_id`, `motif`, `consentement_reference`, `debut`, `fin` |

### 14.1 `eleve_actif` — la métrique de facturation

Un élève compte comme actif s'il porte une inscription en état `active` au jour du relevé. Ni le
nombre de sites, ni le nombre d'établissements, ni le nombre de comptes n'entrent dans le calcul.

### 14.2 Invariants

- **Le paquet `editeur` ne référence ni `classe`, ni `note`, ni `bulletin`.** Il compte des élèves
  actifs et facture. Le jour où un client n'a pas de classes — un centre de formation continue — il
  reste facturable.
- **Le coût IA et le coût SMS sont suivis par tenant et par période.** Le prix par élève est un
  budget, pas un résultat.
- **Tout accès support aux données d'un client est tracé et lié à un consentement.**

---

## 15. Glossaire des concepts neutres

Le modèle utilise des codes neutres et stables ; les libellés viennent du country pack.

| Code neutre | Francophone | Anglophone |
|---|---|---|
| `ANNEE` | Année scolaire / universitaire | Academic year / session |
| `PERIODE` | Trimestre / Semestre | Term |
| `CLASSE` | Classe | Class / Form / Stream |
| `PROFESSEUR_PRINCIPAL` | Professeur principal / maître titulaire | Form master / Class teacher |
| `BULLETIN` | Bulletin | Terminal report / Report card |
| `NOTE` | Note — l'échelle vient du référentiel, jamais du code | Score / Mark (%) |
| `MENTION` | Mention | Grade (A1–F9) |
| `RANG` | Rang | Position in class |
| `RESPONSABLE` | Responsable légal | Parent / Guardian |
| `CHEF_ETABLISSEMENT` | Chef d'établissement / Proviseur / Directeur | Headmaster / Head teacher / Principal |
| `CENSEUR` | Censeur / Éducateur | Assistant head (discipline) |
| `ECONOME` | Économe / Intendant | Bursar |
| `INSTANCE_PARENTS` | APE / COGES | PTA |
| `FRAIS_SCOLARITE` | Frais de scolarité / écolage | School fees / levies |
| `EXAMEN_NATIONAL` | Examen national (CEPE, BEPC, BAC) | National examination (BECE, WASSCE) |
| `CONSEIL_ELEVES` | Conseil des élèves / délégués | Prefects / Student council |
| `CONSEIL_CLASSE` | Conseil de classe / conseil des maîtres | Class committee |

---

## 16. Récapitulatif des états

| Entité | États |
|---|---|
| `annee_scolaire` | `preparation` → `active` → `cloturee` → `archivee` |
| `inscription` | `candidature` → `dossier_incomplet` → `dossier_complet` → `validee` → `active` → (`transferee` \| `radiee` \| `terminee`) ; `refusee` |
| `note` | `brouillon` → `enregistree` → `verrouillee` |
| `bulletin` | `en_preparation` → `calcule` → `arrete` → `publie` → `archive` |
| `conseil_classe` | `convoque` → `en_seance` → `clos` |
| `decision_passage` | `projet` → `prononcee` → `notifiee` → `verrouillee` ; `en_recours` |
| `facture` | `brouillon` → `emise` → (`partiellement_reglee` \| `soldee`) ; `annulee` |
| `echeance` | `a_venir` → `exigible` → (`reglee` \| `en_retard`) |
| `paiement` | `initie` → `en_attente` → (`confirme` \| `echoue` \| `expire`) ; `rembourse` |
| `arrete_caisse` | `ouvert` → `compte` → `arrete` |
| `signalement` | `depose` → `pris_en_charge` → `en_traitement` → (`escalade` \| `clos`) |
| `envoi` | `file` → `envoye` → (`recu` \| `echoue`) |
| `absence` | `constatee` → (`justifiee` \| `non_justifiee`) |

---

## 17. Catalogue des paramètres

Chaque paramètre porte sa portée la plus basse, son type et sa valeur par défaut. Aucune constante
métier n'est écrite dans le code.

| Clé | Portée | Défaut |
|---|---|---|
| `absence.delai_notification_minutes` | ÉTABLISSEMENT | `15` |
| `absence.regroupement_recapitulatif` | ÉTABLISSEMENT | `HEBDOMADAIRE` |
| `note.taille_lot_enregistrement` | TENANT | `5` |
| `note.tolerance_hors_bornes` | TENANT | `AUCUNE` |
| `bulletin.publication_apres_conseil` | ÉTABLISSEMENT | `true` |
| `finance.penalite_retard_taux` | ÉTABLISSEMENT | `0` |
| `finance.remise_fratrie_taux` | ÉTABLISSEMENT | `0` |
| `finance.seuil_alerte_impaye_jours` | ÉTABLISSEMENT | `30` |
| `sms.plafond_mensuel` | ÉTABLISSEMENT | *(obligatoire)* |
| `sms.fenetre_envoi` | ÉTABLISSEMENT | `07:00-19:00` |
| `conseil.delai_recours_jours` | *country pack* | — |
| `inscription.derogation_dossier_incomplet` | ÉTABLISSEMENT | `false` |
| `securite.duree_session_minutes` | TENANT | `480` |
| `securite.expiration_delegation_max_jours` | TENANT | `90` |
| `conservation.dossier_eleve_annees` | *country pack* | — |
| `conservation.signalement_annees` | *country pack* | — |

---

**Suite** → [03-api.md](03-api.md) pour le contrat, [01-stack.md](01-stack.md) pour la structure.
