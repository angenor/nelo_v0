# Feature Specification: Le socle d'interface (T0b)

**Feature Branch**: `002-socle-interface`

**Created**: 2026-09-15

**Status**: Draft

**Input**: User description: le prompt **T0b — Le socle d'interface** de
[docs/04-roadmap.md](../../docs/04-roadmap.md#t0b--le-socle-dinterface), collé tel quel. Il tient
en une phrase : poser la coquille de l'application et sa bibliothèque de composants, **pour que
toutes les tranches suivantes assemblent au lieu de dessiner** — sur le téléphone d'entrée de gamme
d'une enseignante en classe, sur une tablette de saisie, sur un poste partagé de secrétariat et sur
le téléphone d'un parent au forfait compté.

> **Exception de rédaction assumée** ([04-roadmap.md § T0](../../docs/04-roadmap.md#t0--fondations)) :
> les deux tranches de l'epic T0 nomment la pile technique, parce qu'ici la pile *est* le sujet.
> Ce que la pile impose est isolé dans la section « Contraintes de pile » ; le reste décrit des
> comportements qu'une personne ou une porte de vérification peut observer.

**Sources qui font foi** : [docs/05-design.md](../../docs/05-design.md) en entier,
`docs/design/theme.css` (la seule source des valeurs de couleur),
`docs/design/ecrans/13_systeme-de-design.html` (les quatorze composants et leurs états),
`docs/design/ecrans/06_navigation-composee.html` (le shell composé, quatre rattachements),
[docs/03-api.md](../../docs/03-api.md) § 1.2 (en-têtes), § 1.4 (formats — un libellé visible est
une clé, jamais une littérale) et **§ 1.9** (le contexte qui compose l'interface),
[docs/02-domaine.md](../../docs/02-domaine.md) § 0, § 3.4 (les règles de composition) et § 15
(les codes neutres), [docs/01-stack.md](../../docs/01-stack.md) § 7 (P-05, P-06, P-10), § 8.3 et
§ 9, [ADR 002](../../docs/adr/002-web-d-abord-capacitor-plus-tard.md) (la PWA est la cible),
[ADR 001](../../docs/adr/001-hors-connexion-differe.md), [ADR 014](../../docs/adr/014-la-localisation-passe-par-le-country-pack.md),
[ADR 015](../../docs/adr/015-l-interface-se-compose-a-partir-des-capacites.md), et la
[constitution](../../.specify/memory/constitution.md) v1.0.0 — principes I, II, V, IX et XV.

## User Scenarios & Testing *(mandatory)*

**Acteurs.** Cette tranche produit des écrans qu'une personne regarde, mais **aucune donnée réelle,
aucune règle métier, aucune persistance** : tout s'affiche sur des données de démonstration.
Ses acteurs sont donc de deux natures.

- **Les personnes qui regarderont ces écrans dans les tranches suivantes**, et pour qui chaque
  contrainte est écrite : **l'enseignante en classe**, debout, téléphone d'entrée de gamme à
  390 px, en plein soleil, une craie dans l'autre main ; **la secrétaire sur un poste partagé**,
  clavier et tabulation, écran parfois réglé à 125 % ; **le responsable légal au forfait data
  compté**, qui ne revient pas si un écran lui coûte 5 Mo ; **l'économe ou le censeur** qui cumule
  des domaines et ne veut ni menu grisé, ni tableau de bord presque vide.
- **L'auteur de chaque tranche suivante**, qui doit trouver le composant dont il a besoin dans
  tous ses états et ne jamais en dessiner un ; et **la commande de vérification**, qui doit
  distinguer un écran atteignable d'un écran cassé, un écran sous budget d'un écran trop lourd,
  une chaîne externalisée d'une chaîne en dur — sans qu'une personne relise quoi que ce soit.

Les user stories sont ordonnées par ce qu'elles débloquent : les trois premières sont les trois
critères de fin de la roadmap et le composant nommé « le plus important » ; les quatre suivantes
sont les garanties mécaniques que toutes les tranches hériteront ; la dernière est la discipline
de disposition qui ne se rattrape pas après coup.

---

### User Story 1 - La page de style montre les quatorze composants, tous états, clair et sombre côte à côte (Priority: P1)

L'auteur d'une tranche ouvre, en développement, une page de style. Elle affiche les **quatorze
composants canoniques** — bouton, champ, interrupteur, pastille d'état, pastille de canal,
recherche, avatar, fil d'Ariane, onglets, carte d'indicateur, alerte, ligne de tableau, ruban
d'état de saisie, coquille d'application — **dans chacun de leurs états**, sur des données de
démonstration, **en clair et en sombre côte à côte** sur la même page. Le fichier de thème est
celui des actifs de design, **copié tel quel** ; aucun composant ne porte une valeur de couleur.

**Why this priority**: c'est le premier critère de fin de la roadmap, et la règle du système de
design veut qu'un composant manquant **arrête** un cycle. Six composants sur quatorze garantissent
un arrêt à la deuxième tranche métier.

**Independent Test**: lancer l'application en développement, ouvrir la page de style, compter les
composants et leurs états dans les deux thèmes, comparer le fichier de thème embarqué à celui des
actifs de design, chercher une valeur de couleur hors de ce fichier. Aucune autre story n'est
nécessaire.

**Acceptance Scenarios**:

1. **Given** l'application lancée en développement, **When** on ouvre la page de style, **Then**
   les quatorze composants sont présents, chacun nommé, chacun dans tous les états que
   `docs/design/composants.md` lui attribue, et **chaque état apparaît deux fois** : une fois sur
   un conteneur en thème clair, une fois sur un conteneur en thème sombre, l'un à côté de l'autre.
2. **Given** le fichier de thème embarqué dans l'application, **When** on le compare octet à octet
   à `docs/design/theme.css`, **Then** ils sont identiques.
3. **Given** l'ensemble du code de l'interface hors le fichier de thème et les fichiers qui en
   sont **dérivés mécaniquement** (manifeste, icônes), **When** on y cherche une valeur littérale
   de couleur, **Then** il n'y en a **aucune** : chaque couleur est un jeton nommé du thème.
4. **Given** un composant rendu avec les jetons du thème, **When** le conteneur passe en sombre,
   **Then** le composant bascule sans règle propre — sauf ce qu'une couleur ne peut pas porter :
   une ombre remplacée par une bordure, une opacité, une épaisseur.
5. **Given** une pastille d'état, une alerte ou le ruban dans n'importe quel état, **When** on
   retire la couleur (impression noir et blanc, ou simulation de daltonisme), **Then** l'état se
   lit encore : il porte une **forme** et un **mot**.
6. **Given** un état d'attente ou d'échéance (dossier incomplet, échéance proche, envoi en cours,
   proposé non validé), **When** il s'affiche, **Then** il est porté par la voix ocre ; **et**
   l'impayé et l'absence non justifiée sont les **seuls** états portés par la voix rouge.
7. **Given** l'application construite pour la production, **When** on demande la page de style,
   **Then** elle n'existe pas : elle est servie en développement seulement et ne pèse rien pour
   un utilisateur.

---

### User Story 2 - Le ruban d'état de saisie dit trois choses et ne bloque jamais la saisie (Priority: P1)

Une enseignante saisit sur un écran qui porte le ruban, ancré en bas. Le ruban dit **l'heure du
dernier enregistrement**, **le nombre de saisies en attente** et **la qualité du lien** — en trois
états, chacun avec **sa forme et son mot** : « Tout est enregistré » (coche, voix de réussite),
« Envoi en cours » (point qui pulse, voix de la marque), « Hors ligne » (icône de lien barré, voix
ocre — **jamais rouge** : une coupure n'est pas une faute). Quand le lien tombe, **elle continue de
saisir** ; quand il revient, le compte descend et le ruban repasse au vert **sans qu'elle fasse
quoi que ce soit**.

**Why this priority**: c'est le composant que la roadmap nomme « le plus important de la
tranche », et la contrepartie visible de [ADR 001](../../docs/adr/001-hors-connexion-differe.md) :
sans mode hors connexion, la confiance ne peut venir que de l'explicite. *L'ambiguïté sur ce point
est exactement là où se perd la confiance.*

**Independent Test**: sur un écran de démonstration portant le ruban et un champ de saisie, faire
varier l'état du réseau par l'interface de plateforme (bon, faible, absent, retour), saisir pendant
chaque état, observer le ruban. Ne dépend que de l'existence des composants (US1).

**Acceptance Scenarios**:

1. **Given** un écran de saisie de démonstration, lien bon, une saisie enregistrée à 10:42,
   **When** on regarde le ruban, **Then** il dit « Tout est enregistré », « Dernier enregistrement à
   10:42 », « Aucune saisie en attente », « Lien bon », avec la coche et la voix de réussite.
2. **Given** deux saisies en cours d'envoi sur un lien faible, **When** on regarde le ruban,
   **Then** il dit « Envoi de 2 saisies », l'heure du dernier enregistrement, « Vous pouvez
   continuer à saisir », « Lien faible », avec le point qui pulse.
3. **Given** le lien perdu et quatre saisies conservées, **When** on regarde le ruban, **Then** il
   dit « Hors ligne », « 4 saisies conservées, envoi à la reconnexion », « Continuez, rien ne sera
   perdu », « Pas de lien », en ocre avec l'icône de lien barré — et **rien ne clignote**.
4. **Given** le lien perdu, **When** l'utilisatrice continue de saisir, **Then** chaque saisie est
   acceptée par le champ, le compte de saisies en attente **monte**, et **aucun élément d'écran
   n'est bloqué, masqué ou grisé** par le ruban.
5. **Given** des saisies en attente et le lien qui revient, **When** l'utilisatrice ne fait rien,
   **Then** le compte descend jusqu'à zéro et le ruban repasse à « Tout est enregistré » sans
   aucune action de sa part.
6. **Given** le ruban ancré, **When** le contenu de l'écran défile, **Then** le ruban ne défile
   pas avec lui et ne recouvre jamais l'action principale de l'écran.
7. **Given** la préférence système « réduire les animations », **When** le ruban est en « Envoi en
   cours », **Then** le point ne pulse plus mais **la forme et le mot restent**.
8. **Given** un écran de saisie où rien n'a encore été enregistré, **When** on regarde le ruban,
   **Then** il le dit en toutes lettres plutôt que d'afficher une heure vide.

---

### User Story 3 - La coquille se compose depuis le contexte, jamais depuis un rôle (Priority: P1)

Une personne ouvre l'application. La coquille reçoit un **contexte** de la forme que le contrat
définit — compte, établissements, année, capacités, pack de pays, alertes — et **se compose** à
partir des capacités : une personne **mono-domaine** atterrit **dans son domaine** ; une personne
**multi-domaines** reçoit un **tableau composé** d'un bloc par domaine et une navigation à plat
jusqu'à cinq domaines, regroupée par famille au-delà ; une personne **sans capacité** voit un
message qui **nomme l'administrateur de son établissement** et dit quoi faire — ni page vide, ni
erreur technique. **Aucune liste de rôles n'existe dans le code de l'interface.**

**Why this priority**: c'est le troisième livrable nommé par la roadmap et le principe II de la
constitution — un système de rôles fixes ne se transforme pas en autorisation contextuelle par
ajout, il se remplace. Une coquille qui saurait ce qu'est « un censeur » serait à refaire à T1b.

**Independent Test**: fournir à la coquille, par le point d'entrée de contexte, des contextes de
démonstration ne différant que par leur liste de capacités — une, cinq, sept domaines, zéro
capacité — et observer ce qui se compose. Ne dépend que de US1.

**Acceptance Scenarios**:

1. **Given** un contexte dont toutes les capacités relèvent d'un seul domaine, **When** la coquille
   se compose, **Then** l'écran d'accueil **est** ce domaine — pas un tableau de bord — et la
   navigation porte ses seules entrées, à plat.
2. **Given** un contexte à cinq domaines, **When** la coquille se compose, **Then** l'accueil est
   un tableau composé d'un bloc par domaine, et la navigation liste les cinq domaines **à plat**.
3. **Given** un contexte à sept domaines, **When** la coquille se compose, **Then** la navigation
   les regroupe par famille ; **une famille sans domaine n'apparaît pas**, et une famille n'est
   jamais une page.
4. **Given** un contexte sans aucune capacité, **When** la coquille se compose, **Then** il n'y a
   pas de navigation, et l'écran dit que le compte est bien connecté, que l'administrateur de
   l'établissement doit attribuer les domaines, **nomme cet administrateur** avec son moyen de
   contact, et propose une action pour demander ses accès.
5. **Given** un domaine dans lequel la personne ne détient aucune capacité, **When** on cherche ce
   domaine dans la navigation, l'accueil et toute action de la coquille, **Then** il est
   **absent** — jamais grisé, jamais verrouillé, jamais listé.
6. **Given** l'ensemble du code de l'interface, **When** on y cherche une énumération de rôles ou
   un écran « du censeur », « de l'économe », **Then** il n'y en a aucune ; les contextes de
   démonstration sont décrits par leurs **capacités**, jamais par un nom de rôle.
7. **Given** un contexte portant une alerte (par exemple un budget de messages bas), **When** la
   coquille se compose, **Then** l'alerte s'affiche par le composant alerte, au niveau que sa
   gravité commande, jamais en rouge sauf impayé ou absence non justifiée.
8. **Given** la coquille composée, **When** on regarde son en-tête, **Then** il dit l'établissement
   actif et son site, l'année de travail, la langue courante avec le moyen de la changer, et
   l'identité de la personne par son avatar.

---

### User Story 4 - L'application s'installe, s'ouvre sans barre d'adresse et ne demande jamais de rechargement (Priority: P2)

Depuis Chromium et depuis WebKit, une personne installe l'application sur son écran d'accueil.
Elle s'ouvre en **affichage autonome**, sans barre d'adresse ni bouton de rechargement, avec son
nom et son icône. Toute navigation et toute reprise passent par l'application elle-même. Les
**capacités de plateforme** — état du réseau, stockage, caméra, notifications — passent par **une
interface unique côté client, à une seule implémentation, web** ; aucun écran n'appelle
directement le navigateur. Le service worker est **mince** : ni logique métier, ni cache
d'écriture, ni file de synchronisation.

**Why this priority**: la PWA est **la cible**, pas un confort
([ADR 002](../../docs/adr/002-web-d-abord-capacitor-plus-tard.md)) ; c'est elle que Capacitor et
Tauri empaquetteront plus tard **sans réécriture**, à condition que les provisions soient posées
maintenant.

**Independent Test**: construire l'application, la servir, l'installer depuis chacun des deux
moteurs, l'ouvrir depuis l'écran d'accueil, parcourir les trois situations de la coquille sans
rechargement ; lire le manifeste ; inspecter le service worker ; chercher un appel direct à une
API de plateforme hors de l'implémentation web de l'interface. Ne dépend que de US3.

**Acceptance Scenarios**:

1. **Given** l'application servie, **When** un navigateur Chromium l'évalue, **Then** il la
   reconnaît installable — manifeste valide, icônes aux tailles requises, affichage autonome — et
   l'installation aboutit à une ouverture **sans barre d'adresse**.
2. **Given** l'application servie, **When** un navigateur WebKit l'ajoute à l'écran d'accueil,
   **Then** elle s'ouvre en affichage autonome, avec son nom et son icône.
3. **Given** l'application ouverte en autonome, **When** la personne parcourt l'accueil, un
   domaine, la fiche « à propos » et revient, **Then** tout passe par la navigation de
   l'application — retour compris — et **aucun rechargement manuel** n'est nécessaire ni possible.
4. **Given** une nouvelle version publiée pendant qu'une instance est ouverte, **When** la personne
   revient à l'application, **Then** la nouvelle version s'applique d'elle-même, sans qu'un
   rechargement lui soit demandé, et **sans perdre une saisie en cours**.
5. **Given** l'interface unique de plateforme, **When** on énumère ses implémentations, **Then**
   il y en a **une** — web — et chaque capacité y sait répondre « indisponible » sans lever
   d'erreur vers l'écran : un appareil sans caméra, un navigateur sans notifications.
6. **Given** l'ensemble du code des écrans et des composants, **When** on y cherche un appel direct
   à l'état du réseau, au stockage, à la caméra ou aux notifications du navigateur, **Then** il
   n'y en a aucun hors de l'implémentation web de l'interface.
7. **Given** le service worker, **When** on lit ce qu'il fait, **Then** il ne conserve que les
   fichiers statiques immuables de l'application elle-même ; **aucune réponse portant une
   donnée**, **aucune écriture**, **aucune file** ne le traverse.
8. **Given** un lien profond vers un écran de l'application, **When** on l'ouvre directement,
   **Then** il se résout dans la coquille composée, jamais hors d'elle.

---

### User Story 5 - Les mots viennent des clés et du pack de pays, jamais du code (Priority: P2)

Chaque libellé d'interface est une **clé** dont les valeurs `fr` et `en` **naissent ensemble** ;
chaque libellé **métier** — classe, période, bulletin, responsable — est un **code neutre** résolu
par le **pack de pays**, jamais une littérale. La personne change de langue depuis la coquille et
**tout** ce qui est visible suit, libellés métier compris. Le vocabulaire visible est figé dans
`docs/design/lexique.md`, qui prime sur les clés.

**Why this priority**: le bilinguisme est dans le socle parce qu'il ne se rattrape pas après
(principe XV) ; et le passage au monde anglophone n'est pas une traduction mais un changement de
vocabulaire que seul le pack peut porter
([ADR 014](../../docs/adr/014-la-localisation-passe-par-le-country-pack.md)). Une clé écrite en `fr`
seul se découvre au premier client anglophone, c'est-à-dire trop tard.

**Independent Test**: parcourir la page de style et la coquille en `fr` puis en `en` ; remplacer
le pack de démonstration par un pack fictif au vocabulaire différent et constater que les libellés
métier suivent sans qu'une ligne de code change ; retirer une clé `en` et voir la porte échouer.
Ne dépend que de US1 et US3.

**Acceptance Scenarios**:

1. **Given** la coquille en `fr`, **When** la personne choisit `en`, **Then** chaque libellé
   d'interface change, sans rechargement, et la langue choisie est celle du contexte du compte
   pour la suite de la session.
2. **Given** un libellé métier — le nom d'un domaine pédagogique, le mot pour « classe », celui pour
   « responsable légal » —, **When** on cherche d'où vient le mot affiché, **Then** il vient du pack
   de pays par un code neutre, et **jamais** d'une chaîne du code.
3. **Given** un pack de démonstration fictif où « classe » se dit autrement, **When** on le
   substitue au pack courant, **Then** l'écran affiche le nouveau mot **sans qu'une ligne de code
   ait changé**.
4. **Given** une clé présente en `fr` et absente en `en`, **When** la vérification tourne,
   **Then** elle échoue en nommant la clé.
5. **Given** une chaîne d'interface écrite en dur dans un composant, **When** la vérification
   tourne, **Then** elle échoue en nommant le fichier et la chaîne.
6. **Given** une clé absente à l'exécution, quelle qu'en soit la cause, **When** l'écran se rend,
   **Then** il n'affiche **jamais** une clé brute à la personne ; le repli est visible en
   développement seulement.
7. **Given** un montant et une note de démonstration, **When** ils s'affichent, **Then** le montant
   porte l'espace fine insécable et le symbole de la devise du pack, la note sa virgule et son
   barème, et les chiffres qui s'empilent sont tabulaires — le client **affiche**, il ne calcule
   rien.
8. **Given** la langue du compte absente des langues du pack, **When** la coquille se compose,
   **Then** elle prend la première langue du pack, jamais une clé brute.

---

### User Story 6 - Le poids de chaque écran est déclaré, mesuré, et le dépassement refuse (Priority: P2)

Chaque écran budgété **déclare** son plafond en octets transférés. La vérification ouvre l'écran
dans un vrai navigateur, **mesure** ce qui a été transféré et **échoue** au dépassement en nommant
l'écran, le plafond et la mesure. Dans cette tranche, l'écran d'atterrissage de la coquille est
budgété au plafond **le plus serré du corpus**, parce que l'appel de séance s'y assemblera : si la
coquille seule dépasse, aucun écran d'appel ne tiendra jamais.

**Why this priority**: le poids est l'indicateur d'adoption, pas un détail de performance ; un
budget dépassé est un **refus de fusion**, pas une dette (principe XV, porte P-10). Dans une base
unique, rien n'empêche mécaniquement une dépendance du back-office d'atterrir dans l'écran d'appel
— c'est ce que la porte mesure.

**Independent Test**: lancer la vérification sur le dépôt conforme ; ajouter une image de 300 Ko à
l'écran budgété le plus serré ; relancer ; retirer l'image ; relancer. Ne dépend que de US3 et de
US7 pour l'enchaînement.

**Acceptance Scenarios**:

1. **Given** le dépôt conforme, **When** la vérification mesure les écrans budgétés, **Then** chaque
   écran est sous son plafond et le rapport dit, pour chacun, plafond et mesure.
2. **Given** une image de 300 Ko ajoutée à l'écran budgété le plus serré, **When** la vérification
   tourne, **Then** elle **échoue** en nommant l'écran, le plafond et la mesure — et le dépôt est
   restitué intact après le test négatif.
3. **Given** un écran qui ne déclare aucun budget, **When** la vérification tourne, **Then** il
   n'est pas mesuré, et le rapport le liste comme **non budgété** pour que l'oubli se voie.
4. **Given** l'écran d'atterrissage de la coquille sur une connexion 3G lente simulée, **When** on
   l'ouvre, **Then** le premier affichage utile — la coquille et son ruban — arrive en moins de
   deux secondes.
5. **Given** le chemin du premier affichage, **When** on liste les ressources chargées, **Then**
   **aucune** ne vient d'un service distant : les trois polices du système de design sont servies
   par l'application, avec leur licence et leur attribution atteignables depuis l'écran « à propos ».

---

### User Story 7 - Chaque écran s'atteint dans un vrai navigateur, et les trois portes d'interface prouvent qu'elles mordent (Priority: P2)

La commande de vérification unique du projet enchaîne désormais **les trois portes d'interface** :
chaque écran s'atteint dans un navigateur réel, en clair **et** en sombre, sur **deux moteurs de
rendu** (P-05) ; aucune chaîne d'interface en dur (P-06) ; aucun écran budgété ne dépasse son
plafond (P-10). Chacune a **son test négatif**, et la suite des tests négatifs restaure le dépôt à
l'identique. Monter un composant dans un test ne prouve pas qu'une page s'atteint : **la porte
ouvre un vrai navigateur.**

**Why this priority**: une porte qui ne trouve jamais rien est indistinguable d'une porte qui n'a
rien à trouver. Les sept portes serveur de T0a tiennent ; les trois d'interface sont ce que T0a a
explicitement renvoyé à T0b, et toute tranche suivante les héritera.

**Independent Test**: lancer la commande de vérification ; lancer la suite des tests négatifs ;
constater trois échecs attendus sur les trois portes d'interface, dépôt intact. Ne dépend que de
l'existence des écrans (US1, US3).

**Acceptance Scenarios**:

1. **Given** le dépôt conforme, **When** on lance la commande de vérification, **Then** elle passe
   en **une** invocation, sept portes serveur et trois portes d'interface comprises.
2. **Given** chaque écran de l'application — accueil dans ses trois situations, domaine, « à
   propos », page de style en développement —, **When** P-05 tourne, **Then** chacun est ouvert
   dans un navigateur Chromium **et** dans un navigateur WebKit, en clair **et** en sombre, rend
   son contenu principal et ne lève aucune erreur.
3. **Given** un écran rendu inatteignable — une route cassée, un rendu qui lève —, **When** P-05
   tourne, **Then** elle échoue en nommant l'écran, le moteur et le thème.
4. **Given** une chaîne en dur ou une clé orpheline introduite, **When** P-06 tourne, **Then** elle
   échoue en nommant le fichier.
5. **Given** la suite des tests négatifs, **When** elle s'exécute, **Then** chacune des **dix**
   portes échoue exactement une fois quand on la casse, et le dépôt est identique à la fin —
   un test négatif qui laisse une trace est lui-même un échec.
6. **Given** l'espace de travail de l'interface, **When** P-02 et P-07 tournent, **Then** son
   fichier de verrouillage est commité, aucune dépendance n'est en intervalle, et aucune n'est
   sous licence copyleft fort — les polices sous OFL 1.1 sont acceptées.

---

### User Story 8 - Tout se construit à 390 px et s'élargit ; rien ne se cache, rien n'est trop petit (Priority: P3)

Chaque composant et chaque écran de la coquille se conçoivent à **390 px** de large, une colonne ;
deux colonnes à partir de 768 px, trois à partir de 1200 px. **Un tableau ne se réduit pas, il se
transforme** : sur mobile, une ligne devient une carte avec le libellé au-dessus de la valeur.
Toute cible interactive fait **52 px en contexte de classe, 48 ailleurs, jamais moins de 44** —
nulle part, sur aucun gabarit. **Rien n'est masqué derrière un survol.** Le contraste est AA dans
les deux thèmes, la disposition tient à 125 %, le clavier parcourt tout sur poste, et la préférence
« réduire les animations » est respectée.

**Why this priority**: ces règles ne se rattrapent pas après coup — un composant dessiné pour le
poste et « adapté » au mobile est à refaire — et un appel raté parce que la case voisine a été
cochée coûte un SMS envoyé à tort à une famille. Elles viennent en dernier parce qu'elles
qualifient les stories précédentes plus qu'elles ne livrent quelque chose de nouveau.

**Independent Test**: ouvrir la page de style et la coquille à 390, 768 et 1200 px ; mesurer
chaque cible interactive ; chercher un défilement horizontal ; désactiver le survol ; vérifier le
contraste des deux thèmes ; régler le zoom à 125 %. Ne dépend que de US1 et US3.

**Acceptance Scenarios**:

1. **Given** n'importe quel écran à 390 px, **When** on le parcourt, **Then** il tient en une
   colonne, **sans défilement horizontal**, et l'action principale est atteignable au pouce, en
   bas, sur toute la largeur si elle est unique.
2. **Given** la ligne de tableau à 390 px, **When** elle se rend, **Then** elle devient une carte
   avec chaque libellé de colonne au-dessus de sa valeur ; à 768 px et au-delà elle redevient une
   ligne.
3. **Given** un composant en contexte de classe, **When** on mesure sa cible interactive, **Then**
   elle fait au moins 52 px ; 48 px en contexte standard ; et **aucune** cible d'aucun écran, sur
   aucun gabarit, ne fait moins de 44 px — un contrôle de poste dessiné plus bas garde une zone
   interactive d'au moins 44 px.
4. **Given** n'importe quelle action ou information, **When** le pointeur est un doigt, **Then**
   elle est atteignable sans survol ; le survol peut souligner, il ne révèle jamais.
5. **Given** chaque état de chaque composant, **When** on mesure le contraste texte / fond dans les
   deux thèmes, **Then** il atteint AA.
6. **Given** un poste réglé à 125 %, **When** on ouvre la coquille, **Then** la disposition tient,
   sans chevauchement ni défilement horizontal.
7. **Given** un poste au clavier, **When** on tabule, **Then** chaque action de la coquille et de
   la page de style se rejoint dans l'ordre de lecture, avec un focus visible.

---

### Edge Cases

- **Quatre ou cinq domaines.** Le domaine projet dit « deux ou trois à plat, au-delà de cinq
  regroupés » ; la planche dit « en dessous de quatre à plat ». **Le domaine gagne** : à plat
  jusqu'à cinq inclus, regroupé dès six. La maquette de navigation composée le confirme
  (« 5 entrées, encore à plat »). L'écart est documenté ici et dans `composants.md`.
- **Une capacité dont le domaine est inconnu de l'interface.** Un module livré côté serveur avant
  son écran : le domaine n'est **pas** rendu, l'écran ne casse pas, et le développement le signale
  dans sa console. Jamais un menu vers nulle part.
- **Un contexte à plusieurs établissements ou plusieurs années.** La coquille affiche
  l'établissement actif et l'année de travail que le contexte désigne ; **le changement** est un
  parcours de T1a, pas de cette tranche.
- **Une alerte de contexte de gravité inconnue.** Elle s'affiche en information, jamais en danger :
  le rouge est réservé.
- **Le ruban avant tout enregistrement.** Il dit qu'aucun enregistrement n'a encore eu lieu ; il
  n'affiche jamais une heure vide ni « 00:00 ».
- **Un grand nombre de saisies en attente.** Le compte exact s'affiche ; jamais « 99+ ».
- **Lien perdu et zéro saisie en attente.** Le ruban dit « Hors ligne » et « Aucune saisie en
  attente » : l'état du lien et le compte sont deux informations distinctes.
- **Une capacité de plateforme absente de l'appareil.** L'interface répond « indisponible » ;
  l'écran qui l'appelle le sait et ne montre pas l'action — absente, jamais grisée.
- **Une nouvelle version pendant une saisie.** Elle ne s'applique qu'à la prochaine ouverture ou
  après que la saisie en cours est enregistrée ; jamais au milieu d'un champ.
- **Un fichier dérivé qui porte des couleurs.** Le manifeste et les icônes contiennent
  nécessairement des valeurs de couleur : ils sont **générés** depuis le thème à la construction,
  jamais écrits à la main, et le contrôle des littérales les exempte parce qu'il sait d'où ils
  viennent.
- **Un écran de développement.** La page de style n'est ni budgétée ni livrée en production ; P-05
  l'atteint en développement.
- **La langue change pendant qu'un formulaire est rempli.** Les libellés changent, les valeurs
  saisies restent.
- **Le thème change au milieu d'un écran.** Tout bascule par les jetons ; aucun composant ne garde
  une couleur de l'autre thème.
- **Deux niveaux dans une même alerte.** Impossible par construction : une alerte porte un niveau,
  et un seul.

## Requirements *(mandatory)*

### Contraintes de pile — l'exception assumée

Elles font foi par [docs/01-stack.md § 1 et § 2.3](../../docs/01-stack.md) et
[ADR 002](../../docs/adr/002-web-d-abord-capacitor-plus-tard.md) ; elles ne se rediscutent pas ici.

- **CP-01** : l'interface est une application **Nuxt 4**, dans `web/`, avec `app/` organisé en
  `components/`, `composables/`, `core/`, `pages/`, `assets/` — une seule base de code pour le
  back-office, le portail parent et le portail élève.
- **CP-02** : `pnpm` pour les dépendances de l'espace de travail, verrouillage commité
  (`pnpm-lock.yaml`), aucune dépendance en intervalle.
- **CP-03** : la vérification s'intègre à `scripts/verifier.sh` et à `scripts/tests-negatifs.sh`,
  sans créer une seconde commande.
- **CP-04** : les deux moteurs de rendu de la porte P-05 sont **Chromium** et **WebKit**.
- **CP-05** : le client typé de `contrat/client.d.ts` est la seule description du contrat que
  l'interface consomme ; elle n'en réécrit aucune forme à la main.
- **CP-06** : la stratégie de rendu par surface de [01-stack.md § 1.2](../../docs/01-stack.md)
  est une **hypothèse de travail** (Q4 du journal) ; cette spécification ne la tranche pas, le plan
  la retient ou la réexamine **et le dit**, sous la contrainte des critères de poids ci-dessous.

### Functional Requirements

**Le thème et les composants**

- **FR-001** : L'application embarque `docs/design/theme.css` **copié tel quel**, sans réécriture,
  et une vérification compare les deux fichiers à l'identique.
- **FR-002** : Aucune valeur littérale de couleur n'existe hors du fichier de thème ; les seuls
  fichiers qui en portent sont **dérivés mécaniquement** du thème à la construction (manifeste,
  icônes), jamais écrits à la main, et le contrôle sait les reconnaître.
- **FR-003** : Les quatorze composants canoniques existent, chacun sous **un nom unique** que les
  tranches suivantes réutilisent, avec les états que `docs/design/composants.md` leur attribue :
  - **bouton** : principal, secondaire, discret, danger ; chacun au repos, au focus, pressé,
    **inactif avec sa raison dite** (« Inactif : aucun élève sélectionné ») — un seul principal par
    écran ;
  - **champ** : repos, focus, erreur avec son message, désactivé, avec aide, avec unité ; en
    variantes texte, numérique, liste de choix, case à cocher ;
  - **interrupteur** : activé, désactivé, inactif — un état binaire immédiat, jamais un formulaire
    à valider ;
  - **pastille d'état** : voix de réussite, ocre, rouge, neutre, et **contour ouvert** pour
    « proposé — non validé » ; toujours ronde ou capsule, **toujours avec son mot** ;
  - **pastille de canal** : en ligne, WhatsApp, SMS, papier ; le SMS mis en avant, son coût écrit
    à côté de l'action qui l'engage ;
  - **recherche** : repos, focus, saisie, résultats, aucun résultat ; **avec son indication de
    portée** et, sur poste, son raccourci ;
  - **avatar** : initiales ou photo, jamais une couleur seule ; deux tailles ;
  - **fil d'Ariane** : la position dans une hiérarchie profonde, la dernière entrée non
    cliquable ;
  - **onglets** : actif, inactif, avec compte ; les vues d'une même fiche, pas une navigation ;
  - **carte d'indicateur** : chiffre clé tabulaire, libellé, variation positive, négative ou
    neutre ;
  - **alerte** : information, attente (ocre), danger (rouge), confirmation d'enregistrement (voix
    de réussite) ; avec ou sans action ; **un seul niveau par bloc** ;
  - **ligne de tableau** : en-tête, ligne, ligne avec pastille ; **carte sur mobile** ;
  - **ruban d'état de saisie** : FR-010 à FR-016 ;
  - **coquille d'application** : FR-020 à FR-031.
- **FR-004** : Tout état de tout composant est porté par **une couleur, une forme et un mot** ; la
  couleur seule n'est jamais l'unique porteur.
- **FR-005** : La voix ocre porte l'attente et l'échéance, jamais l'erreur ; la voix rouge est
  réservée à l'impayé et à l'absence non justifiée ; le vert profond ne porte aucun état.
- **FR-006** : Les rayons, hauteurs, bordures et espacements sont ceux de
  [05-design.md § 3](../../docs/05-design.md) et de la planche ; bordures de 1 px, aucune ombre hors
  popover et modale, et en sombre une séparation par bordure et contraste, jamais par ombre.
- **FR-007** : Les chiffres qui s'empilent sont tabulaires ; un montant porte l'espace fine
  insécable et le symbole de devise du pack ; une note s'écrit avec sa virgule et son barème ;
  matricule, reçu, montant, identifiant et code de classe sont en famille mono, et nulle part
  ailleurs.
- **FR-008** : Les trois familles typographiques sont **servies par l'application**, jamais
  chargées depuis un service distant, avec leur licence et leur attribution atteignables depuis un
  écran « à propos ».
- **FR-009** : Un bouton inactif dit **pourquoi** il l'est, avec son versant positif ; un bouton
  **non autorisé** n'existe pas à l'écran.

**Le ruban d'état de saisie**

- **FR-010** : Le ruban est ancré en bas de tout écran de saisie, ne défile pas avec le contenu et
  ne recouvre jamais l'action principale.
- **FR-011** : Il dit trois choses et rien d'autre : l'heure du dernier enregistrement, le nombre
  de saisies en attente, la qualité du lien.
- **FR-012** : Il a trois états, chacun avec sa voix, sa forme et son mot : **« Tout est
  enregistré »** (réussite, coche), **« Envoi en cours »** (marque, point qui pulse), **« Hors
  ligne »** (ocre, lien barré). Il n'est jamais rouge.
- **FR-013** : Il **ne bloque jamais la saisie** : aucun de ses états ne désactive, ne masque ni ne
  grise un contrôle de l'écran ; le champ accepte la saisie sous les trois états.
- **FR-014** : Au retour du lien, le compte de saisies en attente descend et l'état repasse à
  « Tout est enregistré » sans action de la personne.
- **FR-015** : Sous la préférence « réduire les animations », rien ne pulse ; forme et mot
  restent. Rien ne clignote sous aucun état.
- **FR-016** : Le ruban lit l'état du réseau par l'interface unique de plateforme, et **par elle
  seule** ; dans cette tranche, le compte de saisies et l'heure d'enregistrement viennent d'une
  source de démonstration que les tranches de saisie remplaceront.

**La coquille composée**

- **FR-020** : La coquille reçoit un **contexte** dont la forme est **exactement** celle de
  [03-api.md § 1.9](../../docs/03-api.md) — compte, établissements avec leur administrateur, année,
  capacités et périmètres, accès nominatifs, pack de pays, paramètres effectifs, alertes — par **un
  point d'entrée unique** côté client. Dans cette tranche ce point d'entrée est servi par des
  contextes de démonstration ; T1a y branche la requête réelle sans toucher à la coquille.
- **FR-021** : Le **domaine** d'une capacité est le premier segment de son code
  (`vie_scolaire.appel.faire` relève de `vie_scolaire`). La coquille ne connaît **que** des
  domaines et des familles, avec leur clé de libellé, leur ordre et leurs écrans ; elle ne connaît
  **aucun rôle**, et aucun contexte de démonstration n'est défini par un nom de rôle.
- **FR-022** : Un domaine apparaît si et seulement si la personne y détient au moins une capacité ;
  un domaine sans capacité est **absent** — jamais grisé, jamais verrouillé.
- **FR-023** : Une personne mono-domaine atterrit **dans son domaine** ; sa navigation porte les
  entrées de ce domaine, à plat.
- **FR-024** : Une personne multi-domaines atterrit sur un **tableau composé** d'un bloc par
  domaine, dans l'ordre du registre des domaines.
- **FR-025** : La navigation est à plat jusqu'à **cinq** domaines inclus, regroupée par
  **famille** à partir de six ; une famille est une étiquette de lecture, jamais une page, et une
  famille sans domaine n'apparaît pas.
- **FR-026** : Une personne sans capacité voit un écran, **sans navigation**, qui dit que le compte
  est connecté, que l'administrateur doit attribuer les domaines, **nomme l'administrateur de
  l'établissement** avec son moyen de contact, et propose une action de demande d'accès. Ce n'est
  ni une page vide, ni une erreur technique.
- **FR-027** : L'en-tête de la coquille dit l'établissement actif et son site, l'année de travail,
  la langue courante et le moyen d'en changer, et l'avatar de la personne ; le compte des éléments
  d'un domaine (« Absences et retards 12 ») s'affiche quand le contexte le porte.
- **FR-028** : Les alertes du contexte s'affichent par le composant alerte, au niveau que leur
  gravité commande, information par défaut.
- **FR-029** : La coquille fournit sa propre navigation arrière et son fil d'Ariane ; **aucune
  navigation ni reprise ne dépend de la barre d'adresse** ni d'un rechargement manuel. Un lien
  profond se résout dans la coquille.
- **FR-030** : Le choix du thème suit la préférence de l'appareil par défaut, se force depuis la
  coquille, et se mémorise sur l'appareil par l'interface de plateforme — jamais côté serveur dans
  cette tranche.
- **FR-031** : La coquille propose un écran « à propos » qui porte le nom du produit, la version,
  et les attributions des polices et icônes redistribuées.

**L'installation et la plateforme**

- **FR-040** : L'application est **installable** depuis Chromium et depuis WebKit : manifeste
  valide, nom, icônes aux tailles requises, affichage **autonome**, couleurs dérivées du thème.
- **FR-041** : Ouverte depuis l'écran d'accueil, elle n'affiche ni barre d'adresse ni bouton de
  rechargement, et son parcours complet s'effectue sans l'un ni l'autre.
- **FR-042** : Une nouvelle version s'applique **d'elle-même** à la prochaine ouverture ou après la
  saisie en cours, jamais par un rechargement demandé à la personne, jamais au milieu d'une saisie.
- **FR-043** : Les capacités de plateforme — état du réseau, stockage, caméra, notifications —
  passent par **une interface unique** côté client, à **une seule implémentation, web** ; chaque
  capacité sait dire « indisponible » sans lever d'erreur vers l'écran.
- **FR-044** : Aucun composant ni écran n'appelle directement une API de plateforme du navigateur ;
  un contrôle mécanique le vérifie.
- **FR-045** : Le service worker est **mince** : il ne conserve que les fichiers statiques
  immuables et versionnés de l'application ; aucune réponse portant une donnée, aucune écriture,
  aucune file de synchronisation ne le traverse.
- **FR-046** : Aucune capacité employée n'est absente d'un WebView ; la session, quand T1a la
  livrera, tiendra en cookie non lisible par script — la coquille n'y prévoit aucun stockage de
  jeton.

**La langue**

- **FR-050** : Aucune chaîne d'interface n'est en dur ; chaque libellé est une clé, et les valeurs
  `fr` et `en` de chaque clé **existent toutes les deux** — une clé orpheline échoue la porte P-06.
- **FR-051** : Tout libellé **métier** est un **code neutre** résolu par le pack de pays, en
  respectant le glossaire de [02-domaine.md § 15](../../docs/02-domaine.md) ; aucune littérale de
  pays, de devise ni de vocabulaire métier n'existe dans le code de l'interface.
- **FR-052** : La personne change de langue depuis la coquille ; tout ce qui est visible suit sans
  rechargement, libellés métier compris ; la langue initiale est celle du compte dans le contexte,
  repliée sur la première langue du pack si elle n'y figure pas.
- **FR-053** : Le pack de démonstration est une **donnée**, jamais du code ; un test substitue un
  pack fictif au vocabulaire différent et constate que les libellés suivent sans changement de
  code.
- **FR-054** : Une clé introuvable à l'exécution n'est jamais affichée brute à la personne.
- **FR-055** : `docs/design/lexique.md` est créé avec le vocabulaire visible de cette tranche —
  les mots des états, du ruban, de la coquille et des composants — à partir de
  [05-design.md § 8.1](../../docs/05-design.md) et de la planche ; il prime sur les clés, et chaque
  tranche l'étend.
- **FR-056** : Le refus s'annonce avant la saisie et dit son versant positif ; un message dit un
  fait, jamais un jugement.

**Le poids**

- **FR-060** : Chaque écran budgété **déclare** son plafond en octets transférés, en un seul
  endroit ; un écran sans déclaration est listé comme non budgété par le rapport.
- **FR-061** : La vérification ouvre chaque écran budgété dans un vrai navigateur, mesure le poids
  transféré et **échoue** au dépassement en nommant l'écran, le plafond et la mesure.
- **FR-062** : L'écran d'atterrissage de la coquille est budgété au plafond **le plus serré du
  corpus** — celui de l'appel de séance, **120 Ko** — parce que l'appel s'y assemblera.
- **FR-063** : Sur le chemin du premier affichage, aucune ressource ne vient d'un service distant.
- **FR-064** : La page de style n'est pas budgétée et n'existe pas dans la construction de
  production.

**Les portes**

- **FR-070** : P-05 ouvre chaque écran dans un navigateur Chromium et un navigateur WebKit, en
  clair et en sombre, et échoue si un écran ne rend pas son contenu principal ou lève une erreur —
  en nommant l'écran, le moteur et le thème.
- **FR-071** : P-06 échoue sur toute chaîne d'interface en dur et sur toute clé absente d'une des
  deux langues, en nommant le fichier.
- **FR-072** : P-10 est FR-061.
- **FR-073** : Chaque porte d'interface a **son test négatif** dans la suite existante ; la suite
  couvre désormais dix portes et restitue le dépôt intact.
- **FR-074** : P-02 et P-07 couvrent l'espace de travail de l'interface : verrouillage commité,
  aucune dépendance en intervalle, aucune licence copyleft fort, OFL 1.1 acceptée pour les polices.
- **FR-075** : La vérification reste **une commande**, et son temps total est mesuré et rapporté.

**La disposition et l'accessibilité**

- **FR-080** : Tout se conçoit à 390 px, une colonne ; deux colonnes à partir de 768 px, trois à
  partir de 1200 px ; aucun écran ne défile horizontalement.
- **FR-081** : La ligne de tableau devient une carte sur mobile, libellé au-dessus de la valeur.
- **FR-082** : Toute cible interactive fait au moins 52 px en contexte de classe, 48 px en contexte
  standard, et **jamais moins de 44 px** nulle part ; un contrôle de poste peut se dessiner plus
  bas si sa zone interactive garde 44 px. Le contexte est une propriété que l'écran donne au
  composant, jamais une déduction du gabarit.
- **FR-083** : L'action principale est atteignable au pouce, en bas, sur toute la largeur si elle
  est unique.
- **FR-084** : Rien n'est masqué derrière un survol ; le survol souligne, il ne révèle jamais.
- **FR-085** : Contraste AA dans les deux thèmes pour chaque état de chaque composant ; disposition
  tenue à 125 % ; navigation clavier complète avec focus visible ; `prefers-reduced-motion`
  respecté.

**La page de style et les documents de design**

- **FR-090** : Une page de style, servie en développement seulement, montre les quatorze composants
  dans tous leurs états, chaque état **deux fois côte à côte** — conteneur clair, conteneur sombre —
  sur des données de démonstration.
- **FR-091** : Les données de démonstration sont celles du **primaire** — CM2, maître titulaire,
  conseil des maîtres — et des noms fictifs ; jamais une donnée réelle.
- **FR-092** : `docs/design/composants.md` est créé : les quatorze composants, leurs états, leurs
  formes et leurs mots ; la page de style et ce document se correspondent exactement, et une
  vérification compte les états des deux côtés.
- **FR-093** : `docs/design/mouvement.md` est créé : il documente le seul mouvement que le système
  connaît aujourd'hui — la pulsation du point « envoi en cours » — et la règle
  `prefers-reduced-motion` ; **aucune durée nouvelle** n'est inventée hors du thème.

### Key Entities *(include if data involved)*

Aucune entité n'est persistée. Les notions que la coquille manipule sont des **formes** :

- **Contexte de composition** : la réponse de [03-api.md § 1.9](../../docs/03-api.md) — compte
  et langue, établissements (nom, sites, cycles et modules actifs, administrateur), établissement
  actif, années et année active, capacités avec périmètre, accès nominatifs, pack de pays, paramètres
  effectifs, alertes. Servi en démonstration ici, par T1a ensuite.
- **Domaine** : le premier segment d'un code de capacité ; porte une clé de libellé, une famille,
  un ordre, ses écrans. Connu de l'interface par un registre — **pas un rôle**.
- **Famille** : une étiquette de lecture qui regroupe des domaines ; n'apparaît qu'à partir de six
  domaines et seulement si elle en contient.
- **Situation de coquille** : mono-domaine, multi-domaines à plat, multi-domaines regroupés,
  aucune capacité — dérivée du contexte, jamais choisie.
- **État du ruban** : enregistré, envoi en cours, hors ligne ; avec heure du dernier
  enregistrement et compte de saisies en attente.
- **Capacité de plateforme** : réseau, stockage, caméra, notifications ; chacune disponible ou
  indisponible ; une interface, une implémentation web.
- **Budget d'écran** : un écran, un plafond en octets transférés, une mesure.
- **Clé de libellé** : une clé d'interface avec ses valeurs `fr` et `en`, ou un code neutre résolu
  par le pack de pays.
- **Pack de démonstration** : une donnée qui porte devise et exposant, langues, vocabulaire
  métier `fr`/`en` ; substituable par un pack fictif dans les tests.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** : La page de style montre **quatorze** composants, et pour chacun **cent pour cent**
  des états listés dans `composants.md`, chaque état rendu **deux fois** — clair et sombre — sur la
  même page ; une vérification compte les deux côtés et ils sont égaux.
- **SC-002** : Le fichier de thème embarqué est identique octet à octet aux actifs de design, et le
  nombre de valeurs littérales de couleur hors thème et fichiers dérivés est **zéro**.
- **SC-003** : L'application s'installe depuis Chromium **et** depuis WebKit et s'ouvre en
  affichage autonome dans les deux cas ; le parcours complet — trois situations de la coquille,
  domaine, « à propos », retour — se fait **sans un seul rechargement**.
- **SC-004** : Sous lien perdu simulé, **cent pour cent** des saisies sont acceptées par le champ,
  le compte de saisies en attente reflète chacune, et au retour du lien il revient à zéro **sans
  action** de la personne, en moins de deux secondes après le retour.
- **SC-005** : La commande de vérification passe en **une** invocation, dix portes comprises, et
  la suite des tests négatifs produit **dix échecs sur dix** — un par porte — avec un dépôt
  identique à la fin.
- **SC-006** : Ajouter une image de 300 Ko à l'écran budgété le plus serré fait **échouer** la
  vérification ; la retirer la fait repasser ; l'écran d'atterrissage de la coquille pèse
  **moins de 120 Ko** transférés et son premier affichage utile arrive en **moins de deux
  secondes** sur une 3G lente simulée.
- **SC-007** : Le nombre de chaînes d'interface en dur détectées est **zéro** ; **cent pour cent**
  des clés existent en `fr` et en `en` ; changer de langue change **cent pour cent** des libellés
  visibles, métier compris ; substituer un pack fictif change les libellés métier avec **zéro**
  ligne de code modifiée.
- **SC-008** : Le nombre de requêtes vers un service distant sur le chemin du premier affichage
  est **zéro**.
- **SC-009** : À 390 px, **aucun** écran ne défile horizontalement ; **cent pour cent** des cibles
  interactives mesurent au moins 44 px, 52 px en contexte de classe ; **cent pour cent** des états
  de composants atteignent le contraste AA dans les deux thèmes.
- **SC-010** : Le code de l'interface contient **zéro** énumération de rôles et **zéro** appel
  direct à une API de plateforme hors de l'implémentation web ; la vérification le constate
  mécaniquement.
- **SC-011** : La commande de vérification complète, portes d'interface comprises, tient **sous
  trois minutes** sur le poste — le seuil de [01-stack.md § 7.5](../../docs/01-stack.md) ; si les
  navigateurs réels l'en empêchent, le plan le dit et propose le découpage.
- **SC-012** : Pour l'auteur de la tranche suivante, assembler l'écran de T1a ne demande **aucun
  composant nouveau** hors les quatorze : la revue visuelle de T1a le constate.

## Assumptions

- **Diff appliqué sur `docs/03-api.md` § 1.9 — l'administrateur de l'établissement.** La
  constitution (II) et [02-domaine.md § 3.4](../../docs/02-domaine.md) exigent que l'écran « aucune
  capacité » **nomme** l'administrateur ; la planche le montre avec son téléphone ; le contexte de
  § 1.9 ne le portait pas. Chaque établissement du contexte porte désormais
  `"administrateur": { "nom", "prenoms", "telephone" }`. C'est une dérivation directe du corpus,
  pas un choix produit : elle est appliquée, tracée ici et dans le journal, et T1a la sert.
  Le téléphone est celui d'un membre du personnel, montré à un collègue du même établissement
  dans le détail de son propre contexte — pas dans une liste ([03-api.md § 3, R5](../../docs/03-api.md)).
- **Le point d'entrée de contexte est servi par des contextes de démonstration.** La requête
  réelle `GET /moi/capacites` arrive avec T1a ; la coquille lit **la forme** du contrat, et T1a
  branche la source sans toucher à la coquille. Les personas de démonstration — un domaine, cinq,
  sept, aucune capacité — sont définis par des listes de capacités, jamais par un nom de rôle ; le
  choix du persona est un réglage de développement.
- **Seuil de regroupement : à plat jusqu'à cinq, regroupé dès six.** Le domaine dit « au-delà de
  cinq », la planche « en dessous de quatre » : le domaine gagne, l'écart est documenté
  ([05-design.md § 9.1](../../docs/05-design.md)).
- **Les blocs du tableau composé sont réordonnables** selon [02-domaine.md § 3.4](../../docs/02-domaine.md) ;
  le réordonnancement par la personne est **différé** à la tranche qui donne aux blocs un contenu
  réel (T10b), parce qu'il exige une préférence persistée — hors périmètre ici. L'ordre est celui du
  registre des domaines.
- **Le registre des domaines et des familles est une donnée de l'interface, pas une liste de
  rôles.** L'interface doit savoir quels écrans elle possède par domaine ; ce registre porte des
  clés de libellé, jamais un mot. Ses entrées de cette tranche sont celles de la planche ; chaque
  tranche métier ajoute la sienne.
- **L'alerte a quatre niveaux, pas trois.** [05-design.md § 5](../../docs/05-design.md) en liste
  trois (information, attente, danger) ; la planche montre aussi une confirmation d'enregistrement
  en voix de réussite. Les quatre sont retenus ; « un seul niveau par bloc » tient.
- **Le plancher de 44 px prime sur le contrôle de poste à 36 px.** [05-design.md § 3.1](../../docs/05-design.md)
  liste les deux ; le prompt dit « jamais moins de 44, nulle part ». Un contrôle de poste peut se
  **dessiner** à 36 px si sa **zone interactive** garde 44 px.
- **Le contexte tactile est une propriété donnée par l'écran** (classe, standard, poste), jamais
  déduite du gabarit : une tablette en classe reste en classe.
- **Le nom « Nelo » et une icône typographique provisoire** servent le manifeste. Q2 du journal
  est ouverte et ne bloque rien ; le nom est porté en **un seul endroit** pour qu'un renommage
  reste trivial, et l'icône est **générée** depuis les jetons du thème.
- **Q1 du journal se tranche dans le plan, sous contrainte** : les trois polices sont servies
  localement, en sous-ensemble latin, sous OFL 1.1 avec attribution atteignable depuis l'écran « à
  propos » ([01-stack.md § 9](../../docs/01-stack.md)). Le plan nomme les versions.
- **Q3 (mode sombre au portail parent) n'est pas tranchée ici** : cette tranche livre les deux
  thèmes pour tout ; le portail parent n'existe pas encore.
- **Q4 (stratégie de rendu) reste une hypothèse** que le plan retient ou réexamine sous les
  critères de poids, et le dit (CP-06).
- **Le thème suit la préférence de l'appareil, se force depuis la coquille, et se mémorise sur
  l'appareil.** Le corpus définit la bascule par attribut sans dire qui la commande ; un poste
  partagé ne doit pas imposer un thème à la personne suivante, d'où une mémoire locale et non un
  réglage de compte. Le stockage de plateforme ne porte, dans cette tranche, que ce genre de
  préférence d'appareil — **aucune donnée métier, aucune saisie**.
- **Le service worker conserve les fichiers statiques immuables de l'application, et rien
  d'autre.** C'est le minimum de l'installabilité et le contraire d'un cache de données ; le
  hors-connexion reste différé ([ADR 001](../../docs/adr/001-hors-connexion-differe.md)).
- **« Se déconnecter » et le changement d'établissement ou d'année sont des parcours de T1a** ;
  la coquille leur réserve leur place dans l'en-tête sans les livrer.
- **La caméra et les notifications n'ont aucun consommateur dans cette tranche** ; leur place dans
  l'interface unique est livrée et exercée par un test qui vérifie la réponse « indisponible ».
- **Le lexique naît ici, borné au vocabulaire de la tranche.** [05-design.md § 0.1](../../docs/05-design.md)
  le veut « avant le premier écran » ; le premier écran est ici. Il est semé depuis § 8.1 et la
  planche, et chaque tranche l'étend.
- **Aucune durée nouvelle.** Le thème ne porte pas de jeton de mouvement et se copie tel quel ; la
  seule animation connue est la pulsation de la planche. Si une tranche exige une durée, elle
  entre d'abord dans les actifs de design par un diff, jamais dans un composant.
- **Les espacements, rayons et hauteurs viennent de [05-design.md § 3](../../docs/05-design.md) et
  de la planche** ; ils ne sont pas des couleurs et le thème n'en porte pas ; ils ne sont pas
  inventés.
- **Les tests négatifs des portes d'interface suivent le mécanisme de T0a** — copie de travail ou
  mutation restaurée ; la propriété, le dépôt intact, est celle de cette spécification.

## Hors périmètre

- Toute donnée réelle, toute règle métier, toute persistance — les composants s'affichent sur des
  données de démonstration ; aucun calcul côté client, jamais.
- L'authentification, la session, la déconnexion, le changement d'établissement ou d'année, et
  la requête réelle de contexte — T1a.
- Les capacités, rôles, périmètres réels — T1b ; cette tranche ne connaît que la forme.
- Tout écran de travail : appel, notes, portail, fiche — chacun arrive avec sa tranche et
  **s'assemble** à partir des quatorze composants.
- Le réordonnancement des blocs du tableau composé — T10b.
- Le hors-connexion, le cache de données, la file de synchronisation
  ([ADR 001](../../docs/adr/001-hors-connexion-differe.md)).
- Capacitor, Tauri, toute chaîne native, tout magasin
  ([ADR 002](../../docs/adr/002-web-d-abord-capacitor-plus-tard.md)).
- Les portes P-08 et P-09 côté serveur — T2a et T6a ; la disparition du pays hors du pack côté
  interface est couverte ici par FR-051 et FR-053.
- Le serveur d'intégration continue, tout déploiement.
- Tout ce que [docs/06-apres-mvp.md](../../docs/06-apres-mvp.md) décrit ; ce document ne s'ouvre
  pas pour cette tranche.

## Revue visuelle

Cette tranche produit des écrans qu'une personne regarde : la revue prend la **forme A** de
[docs/05-design.md](../../docs/05-design.md#forme-a--la-tranche-a-des-écrans) — un canvas `/design`,
**un artboard par user story**, en session dédiée après cette spécification et avant le plan. Le
prompt prêt à coller est dans [design/prompt-design.md](design/prompt-design.md). L'artboard de la
page de style (US1) est la **planche de style transverse** : ses sources vont dans
`docs/design/canvas/` ; les sept autres dans `specs/002-socle-interface/design/`. L'adresse du
canvas publié sera reportée ici à la validation.
