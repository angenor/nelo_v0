# Journal

*Le pont entre deux sessions. On l'ouvre en arrivant, on l'écrit en partant.*

---

## Comment le tenir

**Une entrée par session de travail**, en tête de la section « Journal », la plus récente en haut.
Format court, quatre lignes maximum :

```
## 2026-08-21 — Titre de ce qui a avancé
**Fait** : ce qui existe maintenant et n'existait pas avant.
**Décidé** : les arbitrages pris, avec leur motif en une phrase.
**Bloqué / à faire ensuite** : la première chose à reprendre.
```

Trois règles :

1. **On écrit ce qui a changé dans le produit, pas ce qu'on a essayé.** Une exploration qui n'aboutit
   pas se note en une ligne, avec ce qu'elle a éliminé.
2. **Une décision qui survit à la session part dans un ADR**, et le journal n'en garde que le renvoi.
   Le journal raconte, l'ADR fait foi.
3. **Une question qu'on ne peut pas trancher soi-même monte dans « Ce qui attend une réponse »**, avec
   qui doit répondre et ce que ça bloque.

---

## État courant

| | |
|---|---|
| **Segment** | **Le primaire, et lui seul** — CP1 à CM2, maître polyvalent, appel par demi-journée, aucune série ([ADR 018](adr/018-le-mvp-commence-par-le-primaire.md)) |
| **Tranche en cours** | Aucune — le corpus documentaire vient d'être posé |
| **Prochaine** | **Étape 0 — la constitution**, puis **T0a — Le socle serveur** |
| **Code existant** | Aucun |
| **Pile serveur** | **FastAPI + Pydantic**, SQLAlchemy Core + `asyncpg`, Alembic par module, `uv` / `ruff` / `pytest` — [ADR 017](adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md) |
| **Outillage** | **Spec Kit 0.16.5 initialisé** — `.specify/` et les dix skills `.claude/skills/speckit-*`. La constitution est encore le gabarit vide |
| **Design** | Le système est arrêté sur la couleur, la typographie et les composants. Douze écrans maquettés dans `design/ecrans/`, plus la planche du système. **Leurs jeux de données sont du secondaire** : ils se reprennent écran par écran aux revues visuelles, pas en une passe ([05-design.md § 6](05-design.md)) |

---

## Ce qui attend une réponse

Rien ici ne bloque le démarrage. Chaque ligne dit ce qu'elle bloquera, et quand.

### Décisions internes — elles se tranchent seul

| # | Question | Ce que ça bloque |
|---|---|---|
| **Q1** | **Les trois polices sont chargées depuis un service distant.** Elles doivent être servies localement : quelle version, quels sous-ensembles de glyphes, sous quelle licence redistribuable ? | **T0b.** Une dépendance réseau sur le chemin du premier affichage contredit le budget de poids, et le pilote est en Côte d'Ivoire |
| **Q2** | **Le produit n'a pas de marque** — ni logo, ni nom affiché, ni favicon. « Nelo » vient du nom du dépôt : est-ce le nom du produit ? | Rien. Un renommage global est trivial tant qu'aucune marque n'est déposée |
| **Q3** | **Le mode sombre est-il proposé au portail parent ?** Il est défini dans les jetons. Sur ce portail, il double la surface de test pour un gain incertain — l'usage est court et diurne | **T0b**, marginalement |
| **Q4** | **La stratégie de rendu par surface** — statique pour le public, serveur pour les portails, client pour le back-office. Retenue par défaut parce qu'elle découle du critère de poids ([01-stack.md § 1.2](01-stack.md)) | **T0b.** Se réexamine si la mesure la contredit |
| **Q5** | **La granularité des capacités** : cinq à douze par service est l'ordre de grandeur visé. Trop fines, l'administration devient illisible pour un censeur ; trop grossières, la séparation scolarité / pédagogie devient impossible | **T1b.** *Après, c'est une reprise de toutes les affectations* |
| **Q6** | **Un agrégateur de paiement ou deux dès le départ ?** L'abstraction est posée quoi qu'il arrive ([ADR 009](adr/009-agregateur-de-paiement-derriere-une-interface.md)) | Les **valeurs par défaut** de T8b, pas son modèle |

### Ce qui exige un conseil juridique local — avant tout engagement contractuel

| # | Question | Ce que ça bloque |
|---|---|---|
| **Q7** | **État exact du droit de la protection des données en Côte d'Ivoire.** La loi n° 2013-450 a fait l'objet de travaux de révision. Quelles **formalités ARTCI** pour un éditeur traitant des données de mineurs — déclaration, autorisation préalable, ou les deux ? | Rien techniquement. **La mise en service d'un pilote payant**, oui |
| **Q8** | **Localisation des données** : le stockage hors du territoire national est-il autorisé, et sous quelles conditions ? | Le choix d'hébergement. À documenter et encadrer, ou à faire changer |
| **Q9** | **Convention État – établissements privés** : contenu à jour, montants, calendrier, pièces exigées pour le contrôle d'effectif, format de remontée | Les **valeurs par défaut** de T8c, pas son modèle |
| **Q10** | **Format réglementaire du bulletin DU PRIMAIRE** et des documents officiels, s'il en existe un imposé | Le gabarit de T6c |
| **Q11** | **Obligations en matière de protection de l'enfance** : le signalement est-il obligatoire ? Quelle autorité destinataire, quels délais ? | Les délais du circuit de T9 |
| **Q12** | **Dénominations et attributions ministérielles à jour** — elles changent fréquemment — et format officiel des remontées statistiques | Le pack de pays complet, reporté après le MVP |
| **Q13** | **Conditions de l'agrégateur SMS** : obtention d'un numéro long virtuel pour l'entrant, tarif unitaire, couverture des quatre opérateurs, accusés de réception | Les **valeurs par défaut** de T4a, et le chiffrage du modèle économique |
| **Q14** | **Obligations comptables et fiscales** d'un établissement privé et d'un éditeur SaaS : SYSCOHADA révisé, TVA, facturation normalisée éventuelle | Rien au MVP. L'export comptable, reporté |

### Ce qu'on ne saura qu'en allant voir — les treize questions aux pilotes

Elles valent plus que n'importe quelle spécification, et **trois d'entre elles peuvent changer
l'architecture** (marquées ⚠).

| # | Question | Ce que ça décide |
|---|---|---|
| **Q15** ⚠ | **Quelle est la couverture réseau réelle dans les salles de classe**, aux étages, dans les bâtiments en dur ? | **La seule mesure qui pourrait rouvrir [ADR 001](adr/001-hors-connexion-differe.md).** Seuil : plus d'un pilote sur trois sans réseau utilisable en classe |
| **Q16** ⚠ | **Quelle proportion de parents a un smartphone avec data active ? Quelle proportion sait lire couramment ?** | Le poids du canal SMS dans le modèle économique, et l'urgence du SMS entrant |
| **Q17** ⚠ | **Qui fait quoi, nommément ?** Combien de personnes à l'administration, quelles fonctions chacune cumule-t-elle réellement ? | Les **modèles de rôles livrés** et les personas sur lesquels les cumuls seront testés (T1b) |
| **Q18** | Combien d'élèves, de sites, de cycles ? Combien de responsables légaux par élève en moyenne ? | Le dimensionnement, et la validation du modèle de foyer |
| **Q19** | **L'école primaire pilote est-elle conventionnée ?** Quelle subvention perçoit-elle, sur quel calendrier, quel est l'encours ? *(L'affectation d'élèves par l'État est un dispositif du secondaire : elle ne se pose pas ici — [ADR 018](adr/018-le-mvp-commence-par-le-primaire.md))* | Les valeurs par défaut de T8c, et sa priorité relative |
| **Q20** | Combien de temps prend aujourd'hui l'édition des bulletins d'un trimestre ? Combien de personnes y travaillent ? | La ligne de base de l'indicateur qui vend le produit |
| **Q21** | Quelle proportion des paiements se fait en espèces ? | L'équilibre entre l'écran de caisse et le parcours en ligne (T8b) |
| **Q22** | Que se passe-t-il aujourd'hui quand un élève est absent ? Combien de temps avant que la famille le sache ? | La ligne de base de l'indicateur le plus visible |
| **Q23** | Comment sont constituées les classes de l'année suivante, et par qui ? | La priorité de la capacité de planification, après le MVP |
| **Q24** | Où sont les données aujourd'hui, et dans quel état ? | Le dimensionnement de T10a |
| **Q25** | Quel est le budget annuel actuel consacré aux outils, et **qui décide de la dépense** ? Que s'est-il passé la dernière fois qu'un outil informatique a été introduit ? | Le prix, et le canal de vente |
| **Q26** | **Comment le primaire pilote évalue-t-il ?** Barème sur dix ou sur vingt ; une échelle d'acquisition par compétence sur le bulletin, ou seulement des moyennes ; le suivi des acquis fondamentaux d'une période à l'autre est-il attendu ? | **Le contenu du pack de T6a et le gabarit de T6c — jamais le moteur.** Le suivi longitudinal est hors MVP : si le pilote l'exige, c'est un arbitrage de périmètre, pas une ligne de code |
| **Q27** | **Le groupe scolaire pilote accepte-t-il d'entrer par son école primaire seule**, ses collège et lycée restant au classeur pendant la première année ? | La vente du pilote. C'est le prix de [ADR 018](adr/018-le-mvp-commence-par-le-primaire.md), et il se pose au premier rendez-vous |

---

## Journal

## 2026-09-05 — La PWA est la cible, Tauri et Capacitor l'empaqueteront

**Fait** : trois ajustements arbitrés sur le projet frère Kaya ont été confrontés au corpus. Deux
étaient déjà en place — le hors-connexion est « différé, pas exclu » avec ses quatre fondations
([ADR 001](adr/001-hors-connexion-differe.md)) ; l'exposant est porté par la devise du country pack
(R2), et aucun écran n'impose un appareil au personnel. Le troisième manquait : **l'ADR 002 est
amendé** — la PWA est la cible, pas un confort, et **Tauri n'est plus écarté, il est différé comme
Capacitor** ([ADR 002](adr/002-web-d-abord-capacitor-plus-tard.md)).

**Décidé** : Capacitor empaquettera la PWA pour le mobile (l'enseignant, le parent), Tauri pour le
poste du back-office (le censeur, l'économe), sans réécriture, le jour où un besoin le justifiera —
aucune chaîne native au MVP. Le MVP livre quatre provisions : PWA installable sur Chromium et WebKit,
aucune dépendance à la barre d'adresse, capacités de plateforme derrière une interface unique à une
seule implémentation web, service worker mince sans logique métier. **La constitution v1.0.0 n'est pas
amendée** : « web et installable, sans Capacitor » reste vrai au MVP.

**Touché** : `00-brief.md § 6` (ligne « L'application native »), `CLAUDE.md` (ce que le produit ne
fait pas), `01-stack.md § 10`, le prompt de **T0b** dans `04-roadmap.md` — la coquille installable et
l'interface de plateforme y sont livrées, et l'ADR 002 entre dans son contexte de lecture.

**Bloqué / à faire ensuite** : rien de nouveau — **Q28** précède toujours `/speckit-plan` sur T0a.

---

## 2026-09-03 — Le MVP change de segment : le primaire d'abord

**Fait** : le corpus bascule du **secondaire général** au **primaire** comme seul segment du MVP.
Onze fichiers touchés, **aucune tranche ajoutée, retirée ni déplacée** : `segments/secondaire/` devient
`segments/primaire/` dans l'arborescence, le modèle et le contrat gagnent leurs notes de segment — la
série reste nullable et vide, `affectation_etat` reste vide, le conseil devient le conseil des maîtres
par un libellé de pack — et six blocs `/speckit-specify` changent d'hypothèses de travail : T2b (pas
de série, maître polyvalent), T5 (appel par demi-journée), T6a (le pack primaire, et l'échelle
d'acquisition traitée comme une échelle de plus), T6b (changement de matière sans quitter la grille),
T6c (le niveau atteint par compétence au bulletin), T7 (conseil des maîtres, sans délégué).
**T8c change de cas nominal** : la subvention à l'établissement conventionné remplace l'élève affecté.

**Décidé** — un ADR, et quatre conséquences nommées :

- **[ADR 018](adr/018-le-mvp-commence-par-le-primaire.md)** porte la décision et son prix. Le motif
  était déjà écrit dans [06-apres-mvp.md § 4](06-apres-mvp.md) — *le primaire est le moins cher parce
  que le socle a été conçu pour lui* — et il se retourne : **si le segment le moins cher est celui que
  le socle absorbe le mieux, c'est par lui qu'on éprouve le socle.**
- **L'ordre des segments devient** primaire *(MVP)* → préscolaire → secondaire général → technique →
  supérieur. La file d'après-MVP est renumérotée en conséquence.
- **Le principe 5 de la constitution s'élargit** : le pack ne porte plus seulement le pays, il porte
  aussi le segment. Aucune branche conditionnée par le cycle, aucune composition d'instance en dur.
- **Une seule perte, et elle est nommée** : au primaire, l'État ne finance pas un élève affecté mais un
  effectif conventionné. T8c garde tout son modèle — `creance_etat` le portait déjà — et perd son
  argument de vente le plus direct jusqu'au segment secondaire.
- **Les treize maquettes portent encore des données de secondaire.** Le système de design ne bouge
  pas ; les jeux de données se reprennent **écran par écran aux revues visuelles**, pas en une passe.

**Bloqué / à faire ensuite** : inchangé — **l'étape 0, la constitution** (son prompt est à jour :
principe 5 élargi, dix-neuf fichiers d'ADR à lire). Deux questions nouvelles pour le premier
rendez-vous pilote : **Q26**, comment le primaire évalue-t-il, et **Q27**, le groupe accepte-t-il
d'entrer par son école primaire seule.

---

## 2026-08-21 — La pile serveur passe de Rust à FastAPI

**Fait** : tout le corpus bascule de **Rust/Actix + sidecar IA** vers **FastAPI + Pydantic**, avec
SQLAlchemy Core et `asyncpg` — jamais l'ORM —, Alembic à un dossier par module, et `uv` / `ruff` /
`pytest` pour l'outillage. **Le sidecar disparaît** : les deux capacités IA du MVP deviennent
`modules/socle/assistance/`, et `compose.yml` passe de quatre services à trois. La famille métier est
renommée `modules/metier/`, parce qu'elle vit désormais dans `modules/`. Le domaine, le contrat, le
design et les vingt-et-une tranches sont **inchangés** — seule la pile serveur bouge.

**Décidé** — un ADR, et sept notes d'amendement :

- **[ADR 017](adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md)** porte la décision et son
  prix. Le motif n'est pas une mesure qui aurait changé : c'est **une seule langue de serveur pour
  les quatre projets du portefeuille**, pour un développeur seul.
- **Quatre pertes sont nommées, aucune n'est édulcorée** : l'empreinte mémoire et la latence · la
  vérification SQL à la compilation que faisait `sqlx`, sans équivalent Python · la hiérarchie de
  paquets que cargo donnait gratuitement · **et le cloisonnement de `protection`, qui perd sa
  garantie de compilation.**
- **Le cloisonnement devient une frontière d'import** tenue par **trois verrous** — déclaration de
  dépendances, graphe d'imports, surface de l'`__init__.py`. *Un compilateur refusait, un test
  signale.* [ADR 012](adr/012-le-cloisonnement-est-une-frontiere-de-compilation.md) est **amendé, pas
  supprimé** : son raisonnement reste, sa garantie faiblit, et c'est écrit.
- **Une porte naît, P-12** : toute requête SQL du produit s'exécute contre une base fraîchement
  migrée. Elle remplace ce que la compilation donnait.
- **La propriété « le produit tourne sans IA » change de forme, pas de nature** : ce n'est plus un
  conteneur qu'on arrête, c'est un **réglage serveur** du catalogue de paramètres. **C'est toujours
  un test.**
- [ADR 004](adr/004-rust-en-facade-python-au-sidecar.md) devient **sans objet** — il justifiait un
  sidecar par le fait que la façade était en Rust. Son corps n'est pas corrigé : un journal de
  décisions ne se réécrit pas.

**Bloqué / à faire ensuite** : inchangé — **l'étape 0, la constitution**. Son prompt a été mis à jour
(principes 3 et 14, et le nombre de fichiers d'ADR à lire) ; il reste à le lancer.

---

## 2026-08-21 — Le corpus est posé

**Fait** : le dépôt passe d'un document de conception unique de 988 lignes à un corpus structuré —
`CLAUDE.md`, sept documents dans `docs/`, seize ADR, et le système de design déplacé dans
`docs/design/` avec ses chemins relatifs corrigés. Spec Kit 0.16.5 initialisé. L'ancien document est
conservé dans `ancien_docs/`, à supprimer quand l'utilisateur le décidera.

**Décidé** — six arbitrages, chacun dans son ADR :

- **Le périmètre.** Le document d'origine décrivait 55 services, six segments et trois vagues de
  pays. Le MVP en garde le socle et douze modules ; les quarante-trois autres sont **datés** dans
  [06-apres-mvp.md](06-apres-mvp.md), qui est fermé pendant le MVP.
- **Le hors-connexion est différé, pas exclu** ([ADR 001](adr/001-hors-connexion-differe.md)), et
  quatre fondations se posent maintenant parce qu'elles ne se rattrapent pas.
- **Le cloisonnement est une frontière de compilation**, pas une convention d'accès
  ([ADR 012](adr/012-le-cloisonnement-est-une-frontiere-de-compilation.md)) — porte **P-11**.
- **Le pays ne vit que dans le country pack** ([ADR 014](adr/014-la-localisation-passe-par-le-country-pack.md))
  — porte **P-09**, mécanique, parce que la discipline seule ne tient pas trois ans.
- **Le budget de poids par écran est une porte de vérification**, pas un objectif — porte **P-10**.
  L'écran d'appel tient sous 120 Ko.
- **Le moteur de messages précède l'appel**
  ([ADR 016](adr/016-le-moteur-de-messages-precede-l-appel.md)). C'est la seule décision d'ordre qui
  ne va pas de soi : un appel sans SMS n'est pas un demi-produit, c'est un autre produit.

**Bloqué / à faire ensuite** : **l'étape 0, la constitution.** `.specify/memory/constitution.md` porte
encore ses jetons `[PRINCIPLE_N_NAME]` : tant qu'elle est vide, aucun `plan` n'est contrôlé. Le prompt
est en tête de [04-roadmap.md](04-roadmap.md#étape-0--la-constitution) — quinze principes, tous
dérivés du corpus, aucun neuf.

---

**Retour** → [CLAUDE.md](../CLAUDE.md) pour l'index, [04-roadmap.md](04-roadmap.md) pour la suite.
