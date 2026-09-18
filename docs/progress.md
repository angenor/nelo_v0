# Journal

*Le pont entre deux sessions. On l'ouvre en arrivant, on l'écrit en partant.*

---

## Comment le tenir

**Une entrée par session de travail**, en tête de la section « Journal », la plus récente en haut.
Format court, quatre lignes maximum :

```

## 2026-09-17 : T1a, la revue visuelle est publiée
**Fait** : huit artboards `US1..US8.dc.html` + `canvas.json` dans `specs/003-connexion-contexte/design/`, générés à partir de `theme.css` (aucune couleur retapée), page assemblée publiée et adresse reportée dans le spec sous « Revue visuelle ». Données du primaire (CM1 B, maîtresse titulaire, famille Koné).
**Décidé** : rien n'est tranché ; la planche rend visibles sept écarts (tenant inconnu avant la session et numéro du secrétariat, cases et pavé d'A1 refusés par R-21, trois états sans code ni mot, refus « déjà utilisé » non prévisible sans route `/verification`, geste de fermeture à 390 px, « SMS » ou « message court », mot d'écran du compte suspendu).
**Bloqué / à faire ensuite** : planche validée le jour même ; arbitrage des sept écarts, puis `/speckit-tasks`.

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
| **Tranche en cours** | **T1a, se connecter et savoir où l'on est**, rang 3, risque élevé : **implémentée le 2026-09-18**, spécifiée et planifiée le 2026-09-17 sur la branche `003-connexion-contexte` ([spec.md](../specs/003-connexion-contexte/spec.md), [plan.md](../specs/003-connexion-contexte/plan.md)). **Revue visuelle publiée et validée le 2026-09-17** ([spec.md § Revue visuelle](../specs/003-connexion-contexte/spec.md#revue-visuelle)). T0a et T0b sont fusionnées dans `main` (2026-09-15 et 2026-09-17) |
| **Prochaine** | La relecture de T1a, puis sa fusion dans `main` ; ensuite T1b (les capacités). **Q30** (les valeurs par défaut de l'authentification) reste à confirmer : elle ne touche que `politique.py` et la migration `0002`. **Q29** attend toujours son ADR, sans bloquer |
| **Code existant** | Le socle serveur de T0a, le socle d'interface de T0b et la connexion de T1a (**430 tests Python, 268 Vitest, 78 de bout en bout (dont l'ouverture de la session semée)**, dix portes) : `web/` (Nuxt 4.5.2, quatorze composants, coquille composée, PWA), `modules/shared/contexte.py`, `scripts/` (**dix portes** et treize mutations négatives), `tests/` (module doré, isolation, idempotence, outbox, frontières, simulations, assistance, authentification, en-têtes, contexte), `web/tests/` (unitaires, bout en bout et portes P-05 et P-10 sur Chromium et WebKit, avec une session semée), `contrat/` avec ses **dix-neuf routes** ([01-stack.md § 2.1](01-stack.md)) |
| **Pile serveur** | **FastAPI + Pydantic**, SQLAlchemy Core + `asyncpg`, Alembic par module, `uv` / `ruff` / `pytest` — [ADR 017](adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md) |
| **Outillage** | **Spec Kit 0.16.5 initialisé** — `.specify/` et les dix skills `.claude/skills/speckit-*`. **La constitution est écrite** : `.specify/memory/constitution.md`, v1.0.0, quinze principes |
| **Design** | Le système est arrêté sur la couleur, la typographie et les composants. Douze écrans maquettés dans `design/ecrans/`, plus la planche du système. **Leurs jeux de données sont du secondaire** : ils se reprennent écran par écran aux revues visuelles, pas en une passe ([05-design.md § 6](05-design.md)) |

---

## Ce qui attend une réponse

Rien ici ne bloque le démarrage. Chaque ligne dit ce qu'elle bloquera, et quand.

### Décisions internes — elles se tranchent seul

| # | Question | Ce que ça bloque |
|---|---|---|
| **Q1** | ~~Les trois polices sont chargées depuis un service distant.~~ **Tranchée le 2026-09-17** ([T0b, research R-07](../specs/002-socle-interface/research.md)) : servies par l'application depuis les paquets Fontsource 5.3.0, sous-ensemble latin, OFL 1.1 avec attribution sur « à propos » ; graisses fixes du premier affichage seulement (Public Sans 400 et 500, Archivo 700), IBM Plex Mono 500 à la demande ; Public Sans 600, Archivo 500 et 600 retirées par la mesure de P-10 (écart E-23) | Rien |
| **Q2** | **Le produit n'a pas de marque** — ni logo, ni nom affiché, ni favicon. « Nelo » vient du nom du dépôt : est-ce le nom du produit ? *T0b emploie « Nelo » et une icône typographique générée depuis les jetons, à titre provisoire, portés en un seul endroit (`web/app/core/produit.ts`)* | Rien. Un renommage global touche une ligne |
| **Q3** | **Le mode sombre est-il proposé au portail parent ?** Il est défini dans les jetons. Sur ce portail, il double la surface de test pour un gain incertain — l'usage est court et diurne | **T0b**, marginalement |
| **Q4** | ~~La stratégie de rendu par surface.~~ **Tranchée le 2026-09-17** ([T0b, research R-06](../specs/002-socle-interface/research.md)) : la mesure a contredit « back-office en rendu client » ; rendu serveur par défaut, rendu client écran par écran par règle de route quand P-10 le permet ([01-stack.md § 1.2](01-stack.md)) | Rien |
| **Q5** | **La granularité des capacités** : cinq à douze par service est l'ordre de grandeur visé. Trop fines, l'administration devient illisible pour un censeur ; trop grossières, la séparation scolarité / pédagogie devient impossible | **T1b.** *Après, c'est une reprise de toutes les affectations* |
| **Q6** | **Un agrégateur de paiement ou deux dès le départ ?** L'abstraction est posée quoi qu'il arrive ([ADR 009](adr/009-agregateur-de-paiement-derriere-une-interface.md)) | Les **valeurs par défaut** de T8b, pas son modèle |
| **Q29** | **Le plafond de 120 Ko de l'accueil et de l'appel contient-il les polices ?** Mesuré en bac à sable ([T0b, research R-16](../specs/002-socle-interface/research.md)), puis **par P-10 sur l'application réelle le 2026-09-17** : accueil **103 à 109 Ko** d'application, polices **43,6 Ko**, total **147 à 153 Ko**. Trois issues : **A** polices système sur les écrans budgétés ; **B** 120 Ko pour l'application et 45 Ko à part pour les polices, immuables et précachées (recommandée, **appliquée**) ; **C** relever à 170 Ko. Tenir B a demandé de ramener le premier affichage à trois fichiers de police (écart E-23 : plus de graisse 600). Le principe XV nomme le chiffre : la réponse entre dans un ADR | T0b, fusionnée, applique B. Changer d'issue touche une ligne de `web/ecrans.json` et une règle de P-10 |
| **Q30** | **Les valeurs par défaut de l'authentification**, posées à titre provisoire par la spec de T1a ([Assumptions](../specs/003-connexion-contexte/spec.md#assumptions)) : code reçu à **six chiffres**, valable **dix minutes**, **cinq** tentatives, renvoi après **soixante secondes**, **cinq** demandes par heure et par numéro ; code personnel à **quatre chiffres**, **cinq** tentatives ; appareil connu **90 jours** ; invitation **7 jours**. La maquette A1 donne les trois premières ; les autres sont des pratiques courantes. Les seuils qui dépendent du tenant sont des clés du catalogue (`securite.*`, [02-domaine.md § 17](02-domaine.md)) ; ceux évalués avant qu'un compte soit connu sont des constantes du produit, en un seul endroit | **Rien avant `implement` de T1a.** Changer une valeur touche une clé ou une constante nommée, jamais un écran |

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

## 2026-09-18 : T1a, la première frontière de sécurité est implémentée

**Fait** : `/speckit-implement` sur les 88 tâches. Quatre schémas migrés sous RLS activée et
forcée (`tenants` étendu, et les noyaux `personnes`, `annees`, plus `habilitations`), dix-neuf
routes servies et au contrat, quatre middlewares ASGI (session, établissement, année,
idempotence) qui rendent vraie la table de refus de [03-api.md § 1.2](03-api.md), le tenant
provisoire de T0a supprimé avec sa fonction `SECURITY DEFINER`. Une personne ouvre sa session par
un code reçu par SMS, puis par un code personnel sur un appareil connu ; elle peut être invitée
par lien, suspendue, changer de numéro, et partager son téléphone avec un autre parent. Côté
interface, un relais Nitro met l'API sous l'origine de Nuxt et garde tout jeton hors de portée du
script, la coquille de T0b vit sur le contexte réel, et six écrans s'assemblent sans composant
neuf. Le pack de pays a sa table et deux packs semés, dont un fictif qui fait tourner le test
d'agnosticité.

**Décidé** : quatre écarts d'implémentation, tous tracés ici et dans le code. (1) `compter()` de
la limitation reste dans `api/` et est **injectée** au service : un module du socle ne remonte pas
vers `api/`, et la hiérarchie d'imports le refuserait (P-04). (2) Le retrait de
`tenants.tenant_de_etablissement` est passé dans une migration `0003` au lieu de la `0002` :
le tenant provisoire s'en servait encore pendant US1, et `verifier.sh` devait rester vert à chaque
point de contrôle. (3) Chaque entrée du catalogue de paramètres porte désormais la révision qui
l'introduit (`entrees_de("0002")`) : sans cela, la migration `0001`, qui lit le catalogue à
l'exécution, aurait réinséré les clés neuves. (4) L'appareil connu et son cookie sont livrés dès
US1 plutôt qu'en US3, parce que le test de la vérification du code les exigeait déjà. La licence
`MIT-0` entre dans la liste autorisée de P-07 : elle arrive avec `cffi`, transitive d'`argon2-cffi`,
et elle est plus permissive que `MIT`, déjà autorisée.

**Mesuré** : SC-003, l'écart des médianes entre un numéro connu et un inconnu, **2,8 ms** sur un
plafond de 50 (cent demandes alternées) ; SC-009, les six écrans de la tranche entre **110,4 et
118,6 Ko** sur 120, polices comptées à part ; SC-012, `scripts/verifier.sh` en **4 min 16 s** sur
cinq minutes, dix portes vertes ; `scripts/tests-negatifs.sh` en **10 min 53 s**, treize mutations
et treize échecs obtenus. SC-006 est prouvé dans un navigateur réel : aucun jeton ne se lit d'un
script. Le détail est dans [quickstart.md](../specs/003-connexion-contexte/quickstart.md).

**La définition de terminé** ([01-stack.md § 8.3](01-stack.md)), point par point : les critères
sont couverts (430 tests Python, 268 Vitest, 78 de bout en bout (dont l'ouverture de la session semée)) ; le client TypeScript est
régénéré sans retouche (P-03) ; les migrations sont réversibles, appliquées sur base vierge, et
chaque requête est exercée (P-01, P-12) ; la RLS est activée et forcée sur les treize tables, avec
le test d'isolation étendu aux quatre schémas ; chaque changement d'état écrit son événement ;
les clés `fr` et `en` sont nées ensemble (P-06) ; les écrans sont vérifiés en clair et en sombre
sur Chromium et WebKit (P-05) et budgétés (P-10) ; les trois clés de sécurité sont au catalogue ;
toute écriture porte sa clé d'idempotence, et le rejeu est testé. **Points hors périmètre** :
aucun document imprimé, et P-08 n'existe pas encore (elle attend la tranche qui lui donnera
quelque chose à vérifier).

**Le contrôle de constitution du [plan](../specs/003-connexion-contexte/plan.md) relu contre le
code livré** : les deux écarts nommés sont toujours les seuls, et le premier est désormais couvert
par un test. (1) La révocation des sessions et l'oubli des appareils restent des effets sur
l'éphémère, faits après le `COMMIT` de la suspension, parce que Valkey ne participe pas à la
transaction : `session_valide` relit donc le statut du compte à chaque requête, et une panne entre
les deux ne sert plus rien à un compte suspendu. (2) La vivacité d'une affectation s'évalue en UTC,
pas dans le fuseau de l'établissement. Rien d'autre n'a bougé : aucune règle côté client, aucun
rôle nulle part, aucune littérale de pays hors des lignes semées, une transaction par module, la
RLS partout, l'outbox dans la transaction, le SMS rédigé pour le SMS, six écrans budgétés.

**Bloqué / à faire ensuite** : Q30 (les valeurs par défaut de l'authentification) reste à
confirmer ; elle ne touche que `politique.py` et la migration `0002`. **SC-001 et SC-002**
demandent un chronomètre sur un vrai téléphone en 3G : le parcours passe de bout en bout, la
mesure au chronomètre reste à faire avec l'utilisateur. **Deux fronts à arbitrer**, nés de cette
tranche : le plafond de 120 Ko ne tient plus qu'à 0,2 Ko sur l'accueil, parce que `fr.json` et
`en.json` sont importés en entier par chaque écran (découpage à trancher, décision de T0b) ; et
l'établissement devrait porter un téléphone, faute de quoi l'écran « aucun domaine » nomme l'école
sans pouvoir donner de numéro. La tranche n'est pas fusionnée : elle attend la relecture.


## 2026-09-17 : T1a, les tâches sont écrites

**Fait** : `/speckit-tasks` : [tasks.md](../specs/003-connexion-contexte/tasks.md), **88 tâches**
en onze phases : mise en place (6), fondations (18 : quatre schémas migrés sous RLS, noyaux,
outbox générique, simulation qui garde ses messages, fixtures, relais Nitro, client, source,
garde, serveur d'API sous les e2e), puis une phase par story (US1 19, US2 7, US3 5, US4 8, US5 7,
US6 5, US7 4, US8 4), finition (4). Les tests précèdent l'implémentation dans chaque story ; les
sept écarts de la revue ont chacun leur tâche.
**Décidé** : la session (US1) est le socle de toutes les stories, puis les en-têtes (US2) ; le
provisoire de T0a est supprimé en US2, pas avant ; les trois mutations négatives des règles de
sécurité entrent dans `tests-negatifs.sh` sous P-12, celle du cookie sous P-05 ; un diff de plus
attend `implement` (T060, T085) : `TEN_ETABLISSEMENT_REQUIS` porte les établissements rattachés
du compte authentifié, pour que la source de contexte sache par où commencer.
**Bloqué / à faire ensuite** : `/speckit-implement`. Q30 se confirme avant, ou reste provisoire.

## 2026-09-17 : T1a, les sept écarts de la planche sont tranchés

**Fait** : la maquette validée par l'utilisateur, le rangement était déjà en place (sources dans
`specs/003-connexion-contexte/design/`, adresse dans le spec) ; il est commité. Les sept écarts
que la planche avait rendus visibles sont tranchés (E-01 à E-07,
[research.md](../specs/003-connexion-contexte/research.md)) et reportés dans la spec (FR-015,
FR-036, FR-057 reformulées ; FR-063 à FR-065 ajoutées), le plan, le contrat.
**Décidé**, dérivé du corpus, sans question à l'utilisateur : avant la session le tenant n'est pas
connu, donc l'écran du numéro porte le nom du produit et la carte du code oriente vers le
secrétariat sans numéro · les cases et le pavé d'A1 sont refusés, le champ nombre du canon suffit ·
deux états d'année entrent aux pastilles et au lexique, les états de compte attendent T1b · en
libre-service, « numéro déjà utilisé » se refuse **après** la vérification du code, jamais à la
demande, pour ne pas faire de la route un oracle sur les numéros ; pour le secrétariat, le contrat
gagne `POST /comptes/verification` (règle 3 de [03-api.md § 3](03-api.md), diff appliqué) ·
l'avatar ouvre le menu de compte, « Fermer la session » y est en un geste, et directement dans
l'en-tête dès `md` · le mot visible est **SMS** · un compte suspendu lit « Votre accès est fermé »
avec l'administrateur nommé, une session révoquée « Votre session est terminée ».
**Bloqué / à faire ensuite** : `/speckit-tasks`.

## 2026-09-17 : le travailleur s'arrête proprement, le test instable de T0a ne l'est plus

**Fait** : `scripts/verifier.sh` rouge une troisième fois sur
`tests/outbox/test_travailleur.py::test_arrete_accumule_relance_consomme` (P-12), sans qu'aucun
code ait changé. Cause lue, pas devinée : `Travailleur.arreter()` **annulait** la tâche ; tombée
entre l'appel du consommateur et le marquage `traite` (deux transactions), l'annulation laissait
l'événement `pris`, orphelin jusqu'au délai de reprise. Le test observait exactement cela
(`{'pris', 'traite'}`), trois échecs sur six passages. C'était un défaut du serveur, pas du test :
un arrêt du processus aurait produit le même orphelin.
**Décidé** : l'arrêt est un signal (`asyncio.Event`), le tour en cours se termine, et l'annulation
n'intervient qu'au-delà de `NELO_TRAVAILLEUR_DELAI_ARRET_MS` (10 s, `.env.exemple`). Vingt
exécutions vertes d'affilée ; `scripts/verifier.sh` : 10 portes vertes en 1 min 13 s. Corrigé sur
`003-connexion-contexte`, comme écart d'implémentation de T0a repris par la première tranche qui
le rencontre.
**Bloqué / à faire ensuite** : rien de nouveau ; `/speckit-tasks` sur T1a.

## 2026-09-17 : T1a, le plan est écrit, la première frontière de sécurité est dessinée

**Fait** : `/speckit-plan` sur `003-connexion-contexte`, lancé directement après `specify`, sans
revue visuelle (choix de l'utilisateur ; le prompt reste prêt). [plan.md](../specs/003-connexion-contexte/plan.md)
avec son contrôle des quinze principes (passe, deux écarts nommés), [research.md](../specs/003-connexion-contexte/research.md)
(R-01 à R-22), [data-model.md](../specs/003-connexion-contexte/data-model.md) (quatre schémas,
Valkey, jeton, cookies), [contracts/openapi-attendu.yaml](../specs/003-connexion-contexte/contracts/openapi-attendu.yaml)
(quinze routes), [contracts/interfaces-python.md](../specs/003-connexion-contexte/contracts/interfaces-python.md),
[quickstart.md](../specs/003-connexion-contexte/quickstart.md). Deux explorations du dépôt ont
précédé, par sous-agents, sur le socle serveur et le socle d'interface.
**Décidé**, dérivé du corpus, tracé, selon l'arbitrage délégué du 2026-09-14 :
- **Trois paquets neufs dans `socle/`** : `habilitations` (le module de la tranche), et les noyaux
  `personnes` et `annees`, chacun avec son schéma, sa migration, son outbox ; T3a et T2a complètent
  sans renommer ni retirer. La table `country_pack` naît dans `tenants` avec deux packs semés, dont
  le fictif.
- **Quatre middlewares ASGI** (session, établissement, année, idempotence) remplacent le tenant
  provisoire de T0a, supprimé ; la fonction `SECURITY DEFINER` provisoire est retirée par une
  migration, trois nouvelles sont nommées. La liste de révocation est l'absence de la session en
  Valkey, lue à chaque requête.
- **Le code à usage unique part par l'outbox du tenant du premier compte trouvé**, son texte en
  clair ne transite que par Valkey, jamais par une table conservée ; le travailleur gagne un
  aiguillage par type d'événement et reçoit la passerelle par fermeture.
- **Un relais Nitro met l'API sous l'origine de Nuxt** et range le jeton d'accès dans un cookie
  non lisible par script : aucun jeton n'est jamais visible d'un script, ni en stockage ni en
  mémoire ; le rendu serveur de la coquille garde ses cookies.
- **La source de démonstration ne vit que dans les constructions d'essai** ; les portes ouvrent
  une session semée par un `globalSetup` qui lit le code dans le journal des messages simulés.
- **Deux diffs de plus** : `affectation.etablissement_id` ([02-domaine.md § 3.2](02-domaine.md)),
  copié de l'année pour vérifier l'en-tête sans traverser un module ; `GET /auth/appareil`
  ([03-api.md § 2.1](03-api.md)), sans lequel l'écran du code personnel ne peut nommer personne.
- **Deux écarts nommés** au contrôle de constitution : les effets éphémères d'une suspension
  (révocation, oubli des appareils) s'exécutent après le `COMMIT`, couverts par la vérification du
  statut à la requête suivante ; la vivacité d'une affectation est calculée en UTC, le fuseau
  attend T1b.
- **Trois bibliothèques** : `phonenumbers` 9.0.39, `PyJWT` 2.14.0, `argon2-cffi` 25.1.0.
**Bloqué / à faire ensuite** : `/speckit-tasks`. Q30 se confirme avant `implement` ; la revue
visuelle peut encore se tenir avant.

## 2026-09-17 : T1a, se connecter et savoir où l'on est, est spécifiée

**Fait** : `/speckit-specify` sur la branche `003-connexion-contexte`, créée depuis `main`.
[spec.md](../specs/003-connexion-contexte/spec.md) : huit user stories, soixante scénarios, FR-001 à
FR-062, SC-001 à SC-012, treize cas limites, checklist de qualité verte en une itération. Le prompt
de revue visuelle est prêt en **forme A**
([prompt-design.md](../specs/003-connexion-contexte/design/prompt-design.md)) : un artboard par
story, la maquette A1 comme référence de facture, trois de ses éléments à encadrer parce que le
corpus les contredit (l'écran « numéro inconnu », l'empreinte digitale, l'appel vocal).
**Décidé**, dérivé du corpus, tracé, sans question bloquante, selon l'arbitrage délégué du 2026-09-14 :
- **Sept diffs appliqués.** [02-domaine.md](02-domaine.md) : `etablissement.administrateur_compte_id?`
  (le contexte de § 1.9 exigeait un administrateur nommé « que T1a sert ») ; les états du `compte`
  en § 16 (`invite` → `actif` → `suspendu`) ; trois clés `securite.*` en § 17. [03-api.md](03-api.md) :
  le `429` nommé `API_LIMITE_DEBIT` ; neuf codes `AUT_` et la règle « refus de preuve `401`, refus
  de règle `422` » en § 2.1 ; `POST /moi/telephone` et sa vérification en § 2.2 (le changement de
  numéro que le prompt impose et que le contrat ne portait pas) ; `POST /comptes`,
  `/comptes/{id}/invitation`, `/comptes/{id}/telephone` sous `habilitations.compte.gerer` en § 2.5.
- **La dépendance d'ordre est assumée, pas cachée** : T1a vérifie des en-têtes contre des
  affectations (T1b) et des années (T2a), et compose un contexte avec une personne (T3a). La roadmap
  l'accepte déjà (T1b « autorise l'accès à des ressources qui n'existent pas encore »). La spec exige
  le comportement ; le plan pose le socle minimal, colonne pour colonne celles du domaine, que la
  tranche propriétaire complète sans renommer ni retirer. C'est le point d'insertion de T0a, étendu.
- **Une session est pour un seul compte d'un seul tenant** ; un numéro partagé (famille, ou deux
  tenants) conduit à un choix après le code, tracé par l'événement d'ouverture. Le partage se
  déclare explicitement à la création du second compte ; le refus d'un rattachement de personnel sur
  un numéro partagé est laissé à T1b, le fait « partagé » lui est rendu lisible.
- **L'envoi du code est un événement outbox, jamais sur le chemin de la réponse** : sinon une
  passerelle indisponible publierait l'existence des comptes (503 pour les connus, 204 pour les
  autres). Le rejeu d'une demande n'envoie pas un second message.
- **Trois écarts maquette / corpus tranchés par le corpus** : aucun écran ne dit qu'un numéro est
  inconnu (l'orientation vers le secrétariat passe sur l'écran du code) ; aucune biométrie ; l'appel
  vocal est V3.
- **Q30 ouverte** : les valeurs par défaut (durées, tentatives, longueurs) sont provisoires.
**Bloqué / à faire ensuite** : la revue visuelle en session dédiée, puis `/speckit-plan`. Le plan
doit dire comment il pose le socle minimal (compte, rattachement, année, personne, pack de pays que
T0a n'a pas semé) et nommer les constantes de sécurité du produit en un seul endroit.

## 2026-09-17 : T0b est fusionnée dans `main`

**Fait** : `002-socle-interface` fusionnée dans `main` (`--no-ff`), à la demande de l'utilisateur.
`scripts/verifier.sh` : un premier passage rouge sur `test_arrete_accumule_relance_consomme` (P-12),
vert seul trois fois, puis 10 portes vertes en 1 min 40 s. Deuxième échec observé de ce test de T0a :
**instable, à corriger**. **Bloqué / à faire ensuite** : Q29 dans un ADR, puis la tranche suivante.

## 2026-09-17 : T058, le parcours d'installation passe sur Chrome, la tranche est complète

**Fait** : le [quickstart § US4](../specs/002-socle-interface/quickstart.md) déroulé dans Google
Chrome 153 (macOS, profil temporaire, piloté par `agent-browser --headed`), sur le build servi par
`preview` au port 3100 (le 3000 était pris par un autre projet).

| Étape | Résultat |
|---|---|
| Installabilité | `Page.getInstallabilityErrors` vide, manifeste sans erreur, `beforeinstallprompt` émis |
| 1. Installer | boîte d'installation de Chrome acceptée **à la main par l'utilisateur** ; `Nelo.app` créée ; `display-mode: standalone` vrai, 38 px de cadre (barre de titre seule, pas de barre d'adresse) |
| Parcours | accueil (`cinq-domaines`) → Vie scolaire → à propos → Retour → Retour, dans l'onglet puis dans la fenêtre d'application : un marqueur posé sur `window` survit, une seule entrée de navigation |
| 3. Mise à jour | libellé `apropos.description` changé, build, `preview` relancée, application rouverte : la page se recharge d'elle-même en moins de 3 s (`navigation: reload`), aucun worker en attente, précache égal au nouveau build, aucun texte « recharger » ; libellé restauré ensuite |
| Portes | P-05 : 4 écrans, 7 visites × 2 moteurs × 2 thèmes, 0 erreur ; T050, T051, T052 verts |

Icônes 192, 512, 512 maskable et 180 servies ; les trois licences de `/a-propos` répondent.

**Décidé (utilisateur)** : un navigateur suffit pour l'instant ; T058 est cochée. **L'étape 2,
Safari, n'a pas été faite** (agent-browser ne pilote que Chromium, et le WebKit de Playwright
n'est pas Safari) : P-05 couvre WebKit mécaniquement, pas l'ajout au Dock.

**Corrigé** : « Lire la licence de Archivo » manquait l'élision ; le libellé dit « de la police
{nom} ». « Compte de {nom} » aurait buté sur un prénom à voyelle : il dit « Compte : {nom} ». Le
lien de licence portait `lang="en"` sur un texte français (un lecteur d'écran l'aurait lu en
anglais) : il porte `hreflang="en"`. `scripts/verifier.sh` : 10 portes vertes en 1 min 16 s.

## 2026-09-17 : T0b, le socle d'interface est implémenté, dix portes sur dix tiennent

**Fait** : `/speckit-implement`, 82 tâches sur 83, en dix-sept commits sur `002-socle-interface`.
`web/` existe : Nuxt 4.5.2 rendu par le serveur, le thème et les mesures copiés tel quel, quatorze
composants dans tous leurs états et une page de style de développement qui les montre en clair et
en sombre ; le ruban dérivé du réseau de la plateforme, qui ne bloque jamais la saisie ; une
coquille composée par `composer(contexte)` depuis quatre personas du primaire, sans aucun rôle ;
le contexte typé par le contrat (`ContexteCapacites`, schéma Pydantic sans route) ; une PWA
installable au service worker de quinze lignes ; deux langues et un pack fictif ; `composants.md`,
`mouvement.md`, `lexique.md`. Trois portes nouvelles, P-05, P-06, P-10, chacune avec sa mutation.

**Mesures** :

| Quoi | Mesure |
|---|---|
| `scripts/verifier.sh`, dix portes et e2e | **1 min 3 s à 1 min 21 s** sur le poste ; **2 min 19 s sur un clone frais** (caches froids) ; cible 3 min (SC-011) |
| `scripts/tests-negatifs.sh` | **2 min 14 s**, **dix portes cassées, dix échecs, dépôt intact** (SC-003) |
| P-10, accueil (quatre personas) | **102,9 à 109,0 Ko** pour 120 ; polices **43,6 Ko** pour 45 ; total 146,5 à 152,7 Ko |
| P-10, domaine (l'appel) | **108,8 Ko** pour 120 ; polices 43,6 Ko |
| P-10, à propos | **101,7 Ko** pour 150 ; polices 43,6 Ko |
| Premier affichage utile, 3G lente simulée (400 kbit/s, 400 ms) | **622 à 643 ms**, ruban visible, pour 2 000 (SC-006) |
| P-05 | 4 écrans, 7 visites × Chromium et WebKit × clair et sombre, installabilité, et `Page.getInstallabilityErrors` de Chromium **vide** |
| Tests | 181 Vitest, 64 scénarios e2e, 111 tests Python ; clone frais : dépendances en 5 s, `/style` ouverte en 18 s |

**Décidé**, trente écarts d'implémentation tracés en fin de
[research.md](../specs/002-socle-interface/research.md) (E-01 à E-30), aucun ne touche le contrat
hors deux diffs appliqués. Les plus lourds :

- **Diff sur [03-api.md § 1.9](03-api.md)** : la devise du contexte porte son `symbole` (E-10).
- **P-07 admet BlueOak-1.0.0 et CC0-1.0, et CC-BY-4.0 pour `caniuse-lite` seul**, toutes
  permissives et arrivées avec Nuxt ; [01-stack.md § 9](01-stack.md) le dit (E-02). `sharp` est
  écarté (libvips est LGPL) : les icônes sont dessinées depuis la lettre d'Archivo (E-01).
- **Premier affichage à trois fichiers de police** : P-10 mesurait 86,8 Ko de polices ; les
  graisses 600 disparaissent, la mono reste aux données (E-23). **La hiérarchie typographique perd
  un cran** : à regarder à la prochaine revue visuelle.
- **Le mot d'une pastille ocre s'écrit en couleur de texte** : l'ocre sur son fond doux fait 3,2:1,
  sous l'AA que FR-085 exige ; la voix reste portée par le fond, le point, le filet (E-27).
- **« Impayé » ne s'affiche plus**, le lexique le refuse : la pastille `IMPAYE` dit « En retard »
  (E-19). **« Validé » parle en réussite**, le canal se dit « En ligne », un champ en erreur parle
  en rouge (R-19, dans `composants.md`).
- Le HTML rendu part compressé, et plus jamais une page d'erreur à moitié : le test négatif de
  P-05 l'a montré (E-24).

**Définition de terminé ([01-stack.md § 8.3](01-stack.md)), relue point par point** :
1 tenu (les états du ruban, les quatre situations, le thème, en unitaire et en navigateur) ;
2 tenu (P-03, `client.d.ts` régénéré) ; 3, 4 et 5 sans objet (aucune table, aucun changement
d'état métier) ; 6 tenu (P-06 à zéro sur 208 clés, le lexique testé ; la page de style montre les
noms techniques des états en légende) ; 7 tenu (P-05, deux moteurs, deux thèmes) ; 8 tenu (P-10,
issue B de Q29) ; 9 sans objet (aucun paramètre ; les délais de la source de démonstration sont
une simulation) ; 10 et 11 sans objet (aucun document, aucune écriture) ; 12 sans objet (P-08
n'existe pas encore et la tranche ne touche aucune provision) ; 13 tenu.

**Non fait** : **T058, le parcours d'installation à la main** (Chrome, Safari, mise à jour qui
s'applique d'elle-même). Ce qui s'automatise est dans P-05 ; cliquer « Installer » ne l'est pas, et
personne ne l'a fait. **Observé** : un test de T0a, `test_arrete_accumule_relance_consomme`, a
échoué une fois sur une dizaine de vérifications complètes, jamais seul (quinze passages verts) ;
à surveiller, T0b ne touche pas le travailleur.

**Bloqué / à faire ensuite** : T058 à la main, relecture, fusion par l'utilisateur ; Q29 dans un
ADR.

## 2026-09-17 : T0b, le plan est écrit, le bac à sable a mesuré le socle

**Fait** : `/speckit-plan` sur `002-socle-interface`. [plan.md](../specs/002-socle-interface/plan.md),
[research.md](../specs/002-socle-interface/research.md) (R-01 à R-22), [data-model.md](../specs/002-socle-interface/data-model.md),
[contracts/interfaces-client.md](../specs/002-socle-interface/contracts/interfaces-client.md),
[quickstart.md](../specs/002-socle-interface/quickstart.md). Contrôle de constitution : passe, quinze
principes cités. Un bac à sable hors dépôt a construit Nuxt 4.5.2 + Tailwind 4.3.3 + TypeScript 6.0.3
+ `@vite-pwa/nuxt` 1.1.1 et mesuré : **socle Nuxt 76 Ko compressés** (Vue seul 41), HTML minimal
0,7 Ko, service worker 5,6 Ko, polices du premier affichage **44 Ko** en graisses fixes (77 en
variables, un sous-ensemble ne gagne que 12 %).
**Décidé**, dérivé du corpus et tracé dans research.md, appliqué selon l'arbitrage délégué :
- **Q4 tranchée** : rendu serveur par défaut, rendu client écran par écran sur mesure (R-06,
  [01-stack.md § 1.2](01-stack.md)). À 400 kbit/s, 120 Ko font 2,4 s : un rendu client ne peint rien
  avant.
- **Q1 tranchée** : Fontsource 5.3.0, latin, OFL 1.1, graisses fixes du premier affichage (R-07).
- **P-06 devient « aucune littérale d'interface »** en cinq règles : chaînes, clés `fr`/`en`,
  couleurs, appels de plateforme, rôles (R-11, [01-stack.md § 7](01-stack.md)).
- **Le type du contexte vient du contrat** : schéma Pydantic `ContexteCapacites` dans
  `modules/shared/contexte.py`, enregistré dans l'OpenAPI sans route ; T1a y branche sa route (R-05).
  Le contexte porte `country_pack.vocabulaire` ([03-api.md § 1.9](03-api.md)).
- **`docs/design/mesures.css`** : les mesures non colorées, copié tel quel comme `theme.css`
  (R-17) ; [05-design.md](05-design.md) : quatre niveaux d'alerte, 36 px dessinés et 44 px
  interactifs (R-19). Les trois écarts de la revue : « Validé » en voix de réussite, canal
  « En ligne », champ en erreur en voix danger.
- **Q29 posée, issue B appliquée à titre provisoire** : le plafond de 120 Ko ne peut pas contenir
  les polices, mesure faite ; P-10 rapportera deux nombres. La réponse est un ADR (principe XV).
**Puis, même jour** : `/speckit-tasks` : [tasks.md](../specs/002-socle-interface/tasks.md), 83 tâches en
onze phases (mise en place, fondations, huit stories, finition), 48 parallélisables, tests avant
implémentation, portes construites avec ce qu'elles vérifient.
**Bloqué / à faire ensuite** : `/speckit-implement`. Q29 attend l'utilisateur sans bloquer.

## 2026-09-15 : T0b, la revue visuelle est dessinée et validée

**Fait** : `/design` en session dédiée, forme A. Huit artboards, un par user story, publiés sur
<https://claude.ai/artifact/EP7qAMEyWcvgGJ9QvC9tU8> et reportés dans
[spec.md § Revue visuelle](../specs/002-socle-interface/spec.md#revue-visuelle). Les sources sont
versionnables : `docs/design/canvas/US1.dc.html` (la planche de style transverse, quatorze composants,
chaque état deux fois, clair et sombre côte à côte) et `specs/002-socle-interface/design/US2..US8.dc.html`
+ `canvas.json`. Le fichier assemblé reste hors dépôt. Toute couleur vient de `theme.css` recopié
tel quel : un contrôle compte seize lignes de valeurs par artboard, celles du thème, aucune autre.
Données du primaire partout : CM2 A, maître titulaire, conseil des maîtres.
**Décidé**, dérivé du corpus et tracé sur les artboards :
- La navigation à 390 px suit la maquette d'appel (barre basse) jusqu'à cinq domaines ; à sept, la
  même barre latérale s'ouvre en tiroir depuis un bouton menu, sans composant neuf.
- La coquille ne montre ni bouton de déconnexion ni cloche : la session est T1a, les alertes passent
  par le composant alerte (FR-027, FR-028).
- Le nom « Nelo » et la version figurent sur « à propos » à titre provisoire (Q2) ; l'attribution des
  icônes y est un blanc marqué à renseigner par le plan.
- Les montants portent l'espace fine insécable (U+202F) partout, chiffres clés en Archivo compris ;
  elle y mesure 0,1 em, fine comme la règle le dit. Les sous-ensembles de glyphes du plan (Q1)
  doivent la conserver.
**Trois écarts planche / spec, encadrés en pointillé ocre sur US1, à trancher dans `composants.md`
et `lexique.md`** : « Validé » en vert profond sur la planche 13 alors que FR-005 dit qu'il ne porte
aucun état ; le canal nommé « Web » sur la planche, « en ligne » dans FR-003 ; le champ en erreur
bordé de rouge sur la planche alors que FR-005 réserve le rouge à l'impayé et à l'absence non
justifiée ; quelle voix porte une erreur de saisie reste à dire.
**Validé le 2026-09-16** par l'utilisateur (« c'est parfait ») ; rangement appliqué : sources en
place, adresse dans le `spec.md`. La règle « jamais de tiret cadratin » entre dans `CLAUDE.md` le
même jour : les textes antérieurs en portent encore, ils se reprennent au fil des tranches.
**Bloqué / à faire ensuite** : `/speckit-plan` sur T0b.

## 2026-09-15 — T0b : la spécification du socle d'interface est écrite

**Fait** : `/speckit-specify` sur la branche `002-socle-interface`, créée depuis `main`.
[spec.md](../specs/002-socle-interface/spec.md) — huit user stories, cinquante-sept scénarios,
FR-001 à FR-093, SC-001 à SC-012, checklist de qualité verte en une itération. Le prompt de revue
visuelle est prêt en **forme A** ([prompt-design.md](../specs/002-socle-interface/design/prompt-design.md)) :
un artboard par story, celui de la page de style destiné à `docs/design/canvas/`.
**Décidé** — dérivé du corpus, tracé, sans question à l'utilisateur, selon l'arbitrage délégué du 2026-09-14 :
- **Diff appliqué sur [03-api.md § 1.9](03-api.md)** : chaque établissement du contexte porte
  `administrateur { nom, prenoms, telephone }` — la constitution (II) exige que l'écran « aucune
  capacité » **nomme** l'administrateur, la planche le montre, le contrat ne le portait pas. T1a le sert.
- **Seuil de regroupement : à plat jusqu'à cinq domaines, regroupé dès six** — le domaine (§ 3.4)
  gagne sur la planche (« en dessous de quatre »), écart documenté.
- **L'atterrissage de la coquille est budgété à 120 Ko**, le plafond de l'appel : l'appel s'y
  assemblera, si la coquille seule dépasse rien ne tiendra.
- **Q1 (polices) se tranche dans le plan** sous contrainte — servies localement, OFL 1.1,
  attribution sur un écran « à propos » ; **Q2** reçoit un nom et une icône provisoires portés en un
  seul endroit ; **Q3** n'est pas touchée ; **Q4** reste une hypothèse que le plan dit retenir ou non.
- Le thème suit l'appareil et se force depuis la coquille, mémorisé localement (poste partagé) ; le
  service worker ne garde que les fichiers statiques immuables ; le réordonnancement des blocs du
  tableau composé est différé à T10b (préférence persistée, hors périmètre).
**Bloqué / à faire ensuite** : la revue visuelle en session dédiée, puis `/speckit-plan`. Le plan
doit nommer les versions des polices (Q1) et dire ce qu'il fait de la stratégie de rendu (Q4).

## 2026-09-15 — T0a : le socle serveur est implémenté, sept portes sur sept tiennent

**Fait** : `/speckit-implement` — les **95 tâches** de T0a, en douze commits sur `001-socle-serveur`.
Le module doré répond (`GET /parametres`, `PUT /parametres/{cle}`, `/sante`), l'isolation par RLS
forcée est prouvée sur chaque table et sur une connexion réutilisée, le rejeu est mémorisé dans
Valkey et le travailleur consomme l'outbox dans l'ordre par tenant, les trois dépendances externes
sont simulées à cinq modes, l'assistance connaît ses six capacités et aucune n'est livrée.
**Mesures** : `scripts/verifier.sh` **18 s** (SC-010, cible 3 min) ; `scripts/tests-negatifs.sh`
**49 s**, 7 portes cassées, 7 échecs, dépôt intact (SC-003) ; P-12 inspecte **14 fonctions
d'accès**, P-04 **35 modules** ; reparcours sous suspension : **25 tests**, résultat identique
(SC-008) ; clone frais → première réponse du module doré en **14 s** (SC-001) ; 102 tests.

**Décidé** — dix écarts d'implémentation, chacun écrit là où il vit, aucun ne touche le contrat :

- **L'expression de tenant est `NULLIF(current_setting('app.current_tenant', true), '')::uuid`** :
  sur une connexion réutilisée, la variable revient à la chaîne vide et non à `NULL` — sans le
  `NULLIF`, une transaction sans tenant lèverait au lieu de ne rien voir.
- **Le `downgrade` garde le schéma `tenants`** : il porte `tenants.alembic_version`, qu'Alembic doit
  pouvoir mettre à jour (R-08) ; tout le reste est retiré, et P-01 l'exerce.
- **Un second point d'ouverture, `bd.sans_tenant()`**, sert aux deux seules fonctions
  `SECURITY DEFINER` ; sous la RLS forcée il ne voit rien. Le propriétaire des schémas contourne
  la RLS (superutilisateur en développement) — sinon ces fonctions ne rendraient rien.
- **Trois épinglages de plus** : `greenlet` (SQLAlchemy asynchrone l'exige sous 3.14), `pyyaml`
  (le test du contrat attendu), `fastapi-cli` (la commande `uv run fastapi dev` du corpus). P-07
  les accepte.
- **Les règles 2 et 3 du modèle rendent les deux détails** `portee_la_plus_basse` et
  `portees_disponibles` : aucune clé du catalogue n'a de portée plus fine qu'`ÉTABLISSEMENT`, la
  règle 3 seule n'aurait jamais été atteinte.
- **Le travailleur prend les événements un par un et arrête le lot au premier échec** : sinon le
  suivant passerait devant celui qui a échoué, et l'ordre par tenant ne tiendrait plus. **La prise
  est une CTE `MATERIALIZED`** : dans un `IN (SELECT … LIMIT n FOR UPDATE SKIP LOCKED)`, PostgreSQL
  a réévalué la sous-requête sur la base de test chargée et passé à `pris` des événements jamais
  rendus — un test intermittent l'a révélé, un test déterministe le garde.
- **Les ports de la composition se surchargent par `.env`** ; P-01 recrée `nelo_verification`, les
  tests `nelo_test` — la base de développement n'est jamais effacée par la vérification.
- Le test négatif de P-03 **indexe** sa retouche : la régénération écrase la copie de travail, seul
  l'index garde la trace d'une modification à la main. `ruff` ignore `E501` : `ruff format` tient
  la longueur du code. Le journal applicatif `nelo.*` est au niveau INFO.

**Définition de terminé** (01-stack § 8.3), relue point par point : **1** ✓ critères couverts, dont
les transitions de l'outbox · **2** ✓ schémas Pydantic, client régénéré sans retouche (P-03) · **3** ✓
migration dans `migrations/tenants/`, réversible, sur base vierge, toute requête exercée (P-12) ·
**4** ✓ RLS activée et forcée, isolation entre deux tenants · **5** ✓ `tenants.parametre.pose` dans
la transaction · **6, 7, 8, 10** sans objet — aucun écran, aucun document · **9** ✓ la suspension de
l'assistance est une clé du catalogue · **11** ✓ `X-Nelo-Requete` exigée, rejeu testé · **12** ✓
aucune provision touchée · **13** ✓ `scripts/verifier.sh` passe en une commande.

**Bloqué / à faire ensuite** : rien — la branche est **fusionnée dans `main`** le même jour, à la
demande de l'utilisateur, vérification verte après fusion. **T0b**, dont le prompt est dans [04-roadmap.md](04-roadmap.md).

---

## 2026-09-15 — T0a : les tâches sont écrites

**Fait** : `/speckit-tasks` — `specs/001-socle-serveur/tasks.md`, **95 tâches** en dix phases :
mise en place (10), fondations (18), puis une phase par user story dans l'ordre de la spec — US1 le
module doré (17), US2 l'isolation (7), US3 rejeu et événements (8), US4 les frontières (8), US5 la
commande de vérification et les tests négatifs (7), US6 les simulations (9), US7 l'assistance (6) —
et la finition (5). Les tests sont des tâches à part entière, écrites avant l'implémentation de
chaque story, parce que la spec les exige. Chaque porte se construit avec la matière qu'elle
vérifie et entre dans `scripts/verifier.sh` dès qu'elle passe ; son test négatif s'écrit avec elle.

**Décidé** : une correction du modèle — un `portee_id` d'établissement invisible depuis le tenant
courant répond **`404 TEN_RESSOURCE_INTROUVABLE`**, pas `TEN_PORTEE_INVALIDE` : sous RLS,
l'établissement d'un autre tenant et l'établissement inexistant sont indistinguables, et FR-019
l'exige. L'ordre recommandé pour un développeur seul met la chaîne complète en place tôt : Phase 1,
Phase 2, US1, US2, US4, US5, puis US3, US6, US7, finition.

**Bloqué / à faire ensuite** : rien. **`/speckit-implement`** — ou `/speckit-analyze` d'abord,
pour la relecture croisée spec / plan / tâches que 01-stack § 8.1 propose sur une tranche lourde.

---

## 2026-09-14 — T0a : les sept diffs sont tranchés, la tranche a sa branche

**Fait** : les sept diffs proposés par le plan sont **appliqués** aux documents projet, tels que
proposés — `assistance.suspendue` \| ÉTABLISSEMENT \| `false` confirmé (**Q28 close**) ;
`contrat/` et les quatre fichiers d'espace de travail dans la cible de `01-stack.md § 2.3` ; la
commande de lancement depuis la racine (§ 3) ; l'outbox comme table **du schéma de chaque module**
(§ 2.5) ; `API_DEPENDANCE_INDISPONIBLE` sur le `503` (`03-api.md § 1.8`) ; `TEN_VALEUR_INVALIDE`
(§ 2.3) ; `evenement_outbox` dans le schéma `tenants` (`02-domaine.md § 1.2`). Le plan, la
recherche, le modèle et le guide de démarrage disent « appliqué » là où ils disaient « proposé ».

**Décidé** : **une branche par tranche.** `001-socle-serveur` est créée depuis `main` ; la
constitution ratifiée, les amendements du corpus, la spec, la planche et le plan y sont commités.
`main` ne reçoit la tranche qu'à sa fusion, après `scripts/verifier.sh`.

**Bloqué / à faire ensuite** : rien. **`/speckit-tasks`** sur T0a.

---

## 2026-09-10 — T0a : le plan est écrit, sept diffs attendent

**Fait** : `/speckit-plan` sur T0a — `plan.md`, `research.md` (vingt-deux décisions),
`data-model.md` (le schéma `tenants` : cinq tables, deux fonctions, le catalogue seedé depuis § 17),
`contracts/openapi-attendu.yaml` et `contracts/interfaces-python.md`, `quickstart.md`. Le contrôle de
constitution passe sur les quinze principes ; trois choix de complexité sont justifiés (deux
fonctions `SECURITY DEFINER`, deux paquets créés pour une abstraction chacun, un espace de travail
`pnpm` à la racine avant `web/`). La disposition de l'espace de travail `uv` a été **vérifiée dans un
bac à sable** : racine installable, paquets d'espace de noms aux chemins littéraux du corpus,
`pyproject.toml` déclaratif par paquet — c'est ce qui donne au premier verrou de P-11 quelque chose
à inspecter.

**Décidé** : **Q28 appliquée à titre provisoire** — `assistance.suspendue`, `ÉTABLISSEMENT`,
`false`, telle que la spec la proposait — parce que le plan devait dériver d'un catalogue qui porte la
clé. L'idempotence vit dans Valkey (conforme au R11 et au § 1.3 amendés depuis la spec) ; l'outbox
est une table **du schéma de chaque module** ; le client typé vit dans `contrat/` à la racine ;
l'ordre des portes est fixé : ruff, P-02, P-07, P-04, P-11, P-01, P-12, P-03, reparcours sous
suspension.

**Bloqué / à faire ensuite** : **sept diffs** sur les documents projet attendent un arbitrage avant
`/speckit-tasks` — la table est en fin de `plan.md` (Q28 à confirmer, `contrat/` dans 01-stack § 2.3,
la commande de lancement, l'outbox par module, `API_DEPENDANCE_INDISPONIBLE`, `TEN_VALEUR_INVALIDE`,
`evenement_outbox` dans § 1.2). Et une question de méthode : `specs/` n'est pas suivi par git et
aucune branche `001-socle-serveur` n'existe — T0a se construit-elle sur `main` ?

---

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

## 2026-09-03 — T0a : la planche de diagrammes est posée

**Fait** : `specs/001-socle-serveur/design/diagrammes.md` — la revue visuelle de forme B, cinq
blocs Mermaid, chacun rendu sans erreur par `mermaid-cli` : la hiérarchie des paquets et ses deux
arêtes interdites (US4), une écriture sur le module doré jusqu'au rejeu divergent (US1–US3), le
cycle de vie d'un événement (US3), la chaîne `scripts/verifier.sh` avec le test négatif de chaque
porte (US5), les trois dépendances simulées et l'assistance dans le socle (US6, US7).

**Décidé** : rien de neuf. Deux points laissés ouverts au `plan`, et dits dans les phrases
d'introduction : l'ordre d'enchaînement des sept portes n'est pas fixé par le corpus, le diagramme en
propose un du moins coûteux au plus coûteux ; le support de la mémoire des réponses n'est pas nommé
par le corpus, le diagramme le tient hors de la transaction PostgreSQL sans le placer.

**Bloqué / à faire ensuite** : **Q28** reste l'arbitrage qui précède `/speckit-plan`.

---

## 2026-09-03 — T0a : le socle serveur est spécifié

**Fait** : `specs/001-socle-serveur/` existe — le premier dossier de `specs/`. Le `spec.md` porte
sept user stories, trente-huit scénarios d'acceptation, douze cas limites, quarante-neuf exigences,
dix critères mesurables, et la section « Hors périmètre ». La liste de contrôle qualité passe
entièrement, sans marqueur de clarification. Le prompt de revue visuelle est écrit en **forme B**
— une planche de cinq diagrammes Mermaid, pas de `/design` — dans `design/prompt-diagrammes.md`.

**Décidé** : trois défauts raisonnés, exposés dans les hypothèses du spec et révisables. **Le module
doré est le catalogue de paramètres** du paquet `tenants` — il existe au contrat, il porte le
réglage de suspension de l'assistance exigé par la même tranche, et il montre lecture, écriture,
refus de schéma et refus métier. **Les sept portes serveur** sont P-01, P-02, P-03, P-04, P-07,
P-11, P-12 ; P-08 et P-09 attendent T2a et T6a. **Le tenant est résolu provisoirement** depuis
l'en-tête d'établissement jusqu'à T1a, la capacité étant un point d'insertion que T1b remplit.

**Bloqué / à faire ensuite** : **Q28** — la clé du catalogue qui suspend l'assistance n'existe pas
dans `02-domaine.md § 17` ; le diff est proposé, l'arbitrage précède le `plan`. Puis la planche de
diagrammes en session dédiée, puis `/speckit-plan`.

---

## 2026-09-03 — Étape 0 : la constitution est ratifiée

**Fait** : `.specify/memory/constitution.md` passe du gabarit vide à la **version 1.0.0**. Quinze
principes, I à XV, chacun avec sa règle opposable, son motif tiré des ADR et la manière dont un plan
est jugé non conforme ; une table principe → porte de `verifier.sh` ; la méthode et la définition de
terminé ; une gouvernance qui renvoie vers `02-domaine.md`, `03-api.md`, `progress.md` et `adr/`.

**Décidé** : rien de neuf — deux tensions du corpus ont été conciliées sans ADR, parce que la
hiérarchie d'imports les tranchait déjà. Le principe V dit « aucune ligne ne connaît le segment »
alors que `modules/segments/primaire/` existe : la constitution précise que **le socle et `metier/`
n'importent jamais `segments/`**. Le principe XII dit « 404, jamais 403 » alors que `03-api.md`
répond `403 ETB_NON_AUTORISE` à un en-tête d'établissement non affilié : le principe vise **la
ressource, pas l'en-tête**. Un principe se modifie désormais **par un ADR, pas par un commit**, et
les questions ouvertes de ce journal ne sont pas des principes.

**Bloqué / à faire ensuite** : les deux vérifications d'après ratification que la roadmap demande —
relire la constitution contre chaque ADR, et contre « Ce qui attend une réponse » — puis **T0a — Le
socle serveur**, avec son prompt `/speckit-specify` dans [04-roadmap.md](04-roadmap.md).

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
