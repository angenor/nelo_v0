<!--
Rapport de synchronisation — 2026-09-03
Version : gabarit vide → 1.0.0 (ratification initiale)
Principes : quinze principes posés, I à XV — aucun renommé, aucun retiré (le gabarit n'en portait
  aucun)
Sections ajoutées : « Périmètre et portes de vérification », « Méthode et définition de terminé »,
  « Gouvernance »
Sections retirées : aucune
Gabarits dépendants : .specify/templates/plan-template.md lit la constitution à l'exécution
  (« Constitution Check ») — aucune modification requise ; spec-template.md et tasks-template.md
  inchangés
Reports : aucun jeton laissé en attente
-->

# Constitution de Nelo

Nelo est une plateforme de gestion pour établissements scolaires. Le pilote est un groupe scolaire
privé d'Abidjan, **par son cycle primaire, seul segment du MVP**. Cette constitution ne décide rien
de neuf : elle rassemble ce que le corpus a déjà tranché et le rend **opposable à chaque plan**.
Un principe sans son motif ne survit pas à la première contrainte de calendrier ; chacun porte donc
sa règle, son pourquoi, et la manière dont un plan est jugé non conforme.

## Principes fondamentaux

### I. Le serveur est la seule autorité

**Règle.** L'interface masque, l'API refuse : chaque appel revérifie la capacité **et** le
périmètre, aucune vérification côté client n'est jamais la seule, et le client n'applique aucune
formule de composition, ne convertit aucune note en mention, ne calcule aucun rang, aucun solde,
aucune pénalité — il affiche ce que le serveur a calculé.

**Motif.** Une moyenne recalculée à la main est un litige en puissance ; une moyenne recalculée par
un navigateur l'est tout autant, et deux implémentations d'une règle finissent par diverger. Le code
servi au navigateur est lisible et modifiable par quiconque l'ouvre : ce qu'il vérifie n'est pas
vérifié ([ADR 005](../../docs/adr/005-isolation-des-tenants-par-rls-et-double-barriere.md),
[ADR 015](../../docs/adr/015-l-interface-se-compose-a-partir-des-capacites.md)).

**Non conforme.** Un plan qui place une formule, une conversion, un rang, un solde ou une pénalité
dans `web/` ; un plan dont une route s'appuie sur le fait que l'écran a déjà filtré ; un plan qui
décrit une vérification de capacité sans sa vérification de périmètre.

### II. L'interface se compose à partir des capacités, jamais des rôles

**Règle.** Les capacités effectives d'une personne sont l'union de ses affectations, chacune liée à
un rôle **et** à un périmètre ; aucune liste de rôles n'est codée en dur côté client ; une action non
autorisée est **absente** de l'écran, jamais grisée ; l'absence de capacité affiche un message qui
nomme l'administrateur de l'établissement, jamais une page vide ni une erreur technique.

**Motif.** La répartition des fonctions varie d'un établissement à l'autre à segment identique :
une personne tient trois services dans une école de 400 élèves, trois personnes dans un groupe de
3 000. Une interface par rôle pousse le petit établissement au partage de mots de passe et le grand à
des droits trop larges. Un système de rôles fixes ne se transforme pas en autorisation contextuelle
par ajout : il se remplace, et avec lui toutes les vérifications d'accès du produit
([ADR 015](../../docs/adr/015-l-interface-se-compose-a-partir-des-capacites.md)).

**Non conforme.** Un plan qui introduit une énumération de rôles côté client ou une page « du
censeur » ; un plan qui prévoit un menu ou un bouton désactivé au lieu d'absent ; un plan dont le
`403` aboutit à un écran vide ; un plan qui accorde automatiquement une capacité neuve à un rôle
existant.

### III. Le cloisonnement prime sur les habilitations, et c'est une frontière d'import

**Règle.** Dossier médical, psychosocial, signalements, disciplinaire en instruction, paie
individuelle : ces capacités ne sont **pas** ajoutables à un modèle de rôle et s'attribuent
nominativement, avec motif et date de fin ; aucun paquet n'importe `modules/metier/protection/`, tenu
par trois verrous — aucune déclaration de dépendance, un test de graphe d'imports qui voit aussi les
imports différés, un `__init__.py` qui n'expose rien hors de son interface de service ; toute lecture
s'écrit dans le journal d'accès, y compris en cas de refus ; un chef d'établissement n'a pas accès
par défaut au contenu d'un signalement qui le concerne.

**Motif.** C'est le domaine où une erreur de conception a les conséquences les plus graves, humaines
comme juridiques : il suffirait qu'un jour quelqu'un ajoute la consultation des signalements au rôle
« Direction » pour dépanner. Un module qui pourrait lire un signalement finirait par le lire. **Un
compilateur refusait, un test signale** : c'est plus faible que la garantie d'origine, c'est écrit,
et le plan qui s'en écarte doit le dire
([ADR 012](../../docs/adr/012-le-cloisonnement-est-une-frontiere-de-compilation.md),
[ADR 017](../../docs/adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md)).

**Non conforme.** Un plan qui fait lire `protection` par un tableau de bord, un export ou un autre
module, même « en lecture seule » ; un plan qui rend une capacité cloisonnée rôlable ; un plan qui
ajoute une route `PRO_` sans écriture dans `journal_acces` ; un plan qui affaiblit l'un des trois
verrous de la porte P-11 sans le nommer explicitement comme un écart.

### IV. Toute donnée d'élève est une donnée de mineur

**Règle.** Base légale, durée de conservation et journal d'accès sont définis pour chaque
traitement, **dans le modèle** ; aucune donnée d'élève n'existe sans qu'on sache qui peut la lire,
combien de temps, et à quel titre.

**Motif.** Le texte applicable au pilote n'est pas le RGPD mais la loi ivoirienne sur la protection
des données, sous le contrôle de son autorité nationale ; les droits d'accès, de rectification et
d'opposition doivent être outillés, pas manuels. Une donnée dont la conservation n'est pas écrite
dans le modèle ne sera jamais purgée, et une catégorie sans journal d'accès ne se défend pas devant
une famille ([docs/01-stack.md § 5.2](../../docs/01-stack.md)).

**Non conforme.** Un plan qui ajoute une table ou une colonne portant une donnée d'élève sans base
légale, durée de conservation et régime de journalisation ; un plan qui réutilise des données
d'élèves pour entraîner ou affiner un modèle sans traitement distinct et consentement propre.

### V. Le pays ne vit que dans le country pack, et le segment non plus

**Règle.** Aucune littérale de pays, de devise, d'examen, de découpage d'année ou d'échelle de
notation hors du pack ; aucun cycle, aucun niveau, aucune série, aucune composition d'instance
écrits dans le code ; aucune branche conditionnée par le pays ni par le segment — le MVP sert le
primaire, et aucune ligne du socle ni de `metier/` ne le sait ; le test d'agnosticité — un pack
fictif à échelle sur 10 et deux périodes fonctionnant de bout en bout — est permanent.

**Motif.** Le passage au monde anglophone n'est pas une traduction, c'est un changement de modèle
d'évaluation ; un `if pays == "CI"` écrit pour dépanner ne se retire pas, il se multiplie, et la
discipline seule ne tient pas trois ans. Le changement de segment du MVP, du secondaire au primaire,
n'a touché ni le modèle ni le contrat : c'est la première preuve que la provision tient, et si une
entité doit s'ajouter pour accueillir un segment, la provision était fausse
([ADR 014](../../docs/adr/014-la-localisation-passe-par-le-country-pack.md),
[ADR 018](../../docs/adr/018-le-mvp-commence-par-le-primaire.md)).

**Non conforme.** Un plan qui écrit `CI`, `XOF`, `BEPC`, `trimestre`, `20` ou `CM2` dans
`domaine/`, `socle/` ou `metier/` ; un plan qui crée une colonne conditionnelle pour une entité
propre à un pack ; un plan qui fait importer `modules/segments/` par le socle ou par `metier/` — la
hiérarchie de [docs/01-stack.md § 2.4](../../docs/01-stack.md) ne va que dans un sens ; un plan qui
ne fait pas passer le test d'agnosticité.

### VI. Le référentiel d'évaluation est une donnée versionnée, pas du code

**Règle.** Échelle, table de conversion, formule de composition en arbre déclaratif, règles
d'arrondi, règles de rang, gabarit de bulletin sont des données versionnées par pays et par année ;
le moteur est un interpréteur qui vit dans `domaine/` sans E/S, pas une fonction par pays ; toute
moyenne porte la version du référentiel qui l'a produite et est recalculable à l'identique ; un
référentiel publié est figé — on en crée une version, on ne le modifie pas.

**Motif.** Un bulletin réédité trois ans plus tard doit refléter le barème de l'époque, pas le
barème courant ; les règles d'arrondi sont la première source de contestation, et une convention
implicite du langage n'est pas défendable devant un parent. Coder la moyenne sur 20 en dur
condamnerait l'extension anglophone à une réécriture du module, du bulletin et de tous les bulletins
archivés : l'interpréteur est cher, et payé une seule fois
([ADR 010](../../docs/adr/010-le-referentiel-d-evaluation-est-une-donnee-versionnee.md)).

**Non conforme.** Un plan qui écrit une formule de moyenne en Python plutôt qu'en arbre
déclaratif ; un plan dont le moteur porte une branche par pays ou par échelle ; un plan qui stocke
une moyenne sans la version du référentiel ; un plan qui modifie un référentiel publié au lieu d'en
créer une version ; un plan qui donne des E/S à `domaine/`.

### VII. Toute entité pédagogique porte son année

**Règle.** Rien n'est global — ni une classe, ni un coefficient, ni un tarif, ni une affectation de
rôle ; deux années coexistent, une active et une en préparation ; une affectation expire avec son
année et se reconduit explicitement, jamais par défaut.

**Motif.** On réinscrit pour septembre pendant que le troisième trimestre tourne : une classe sans
année écrase celle de l'an passé, et un bulletin archivé devient faux. Une affectation reconduite
par défaut garde son accès à l'enseignant parti ; à la bascule, la personne non reconduite doit voir
un message clair, pas une interface vide
([ADR 015](../../docs/adr/015-l-interface-se-compose-a-partir-des-capacites.md),
[docs/01-stack.md § 7.1](../../docs/01-stack.md)).

**Non conforme.** Un plan dont une table pédagogique n'a pas `annee_id NOT NULL` ; un plan qui
suppose qu'une seule année existe à la fois ; un plan qui reconduit les affectations à la bascule
sans acte explicite ; un plan qui replie silencieusement une route pédagogique sur l'année active
quand l'en-tête d'année manque.

### VIII. Montants entiers, notes NUMERIC, absences en intervalle

**Règle.** Tout montant est un entier d'unité mineure, avec l'exposant porté par la devise du pack ;
toute note et tout coefficient sont `NUMERIC` ; toute occupation et toute absence sont un intervalle
`[début, fin)` — jamais de flottant sur un montant, jamais un entier sur une note, jamais une paire
de dates sur une absence.

**Motif.** Une note de 14,25 stockée en entier devient 14 et rend la moyenne indéfendable ; un
flottant sur une somme d'argent produit des arrondis qu'un économe retrouve à l'arrêté de caisse ;
un appel par demi-journée et un appel par cours exigent deux modèles si l'absence n'est pas un
intervalle — et c'est précisément la provision qui a absorbé le passage au primaire sans changement.
On dégrade ces provisions sans le vouloir, jamais volontairement, et une migration de toutes les
notes du produit se découvre trois ans après ([docs/01-stack.md § 7.1](../../docs/01-stack.md),
[ADR 018](../../docs/adr/018-le-mvp-commence-par-le-primaire.md)).

**Non conforme.** Un plan qui déclare une colonne de montant en `FLOAT` ou `NUMERIC`, une note ou
un coefficient en `INTEGER`, une absence par deux colonnes de dates ; un plan qui porte un exposant
de devise ailleurs que dans le pack ; un plan qui ne fait pas passer la porte P-08.

### IX. Aucune saisie ne se perd

**Règle.** Toute écriture porte une clé d'idempotence générée par le client, et sa réponse est
mémorisée ; les saisies longues — appel, notes — s'enregistrent par petits lots au fil de l'eau,
jamais en un envoi unique ; l'utilisateur voit en permanence si sa saisie est sur le serveur ou en
attente.

**Motif.** La saisie perdue est le seul indicateur du brief dont le rouge est fatal : un enseignant
qui perd quarante notes à la dernière ligne ne rouvre pas l'application, et il le raconte en salle
des professeurs. Le hors-connexion est différé, pas exclu, et l'idempotence avec mémorisation de la
réponse est l'une des quatre fondations qui ne se rattrapent pas après coup — c'est là que se perd
la confiance ([ADR 001](../../docs/adr/001-hors-connexion-differe.md),
[docs/00-brief.md § 3](../../docs/00-brief.md)).

**Non conforme.** Un plan qui expose une écriture sans clé d'idempotence ou sans test de rejeu ; un
plan qui envoie un appel ou une grille de notes en un seul corps de fin de séance ; un plan dont
l'écran ne distingue pas « enregistré » de « en attente » ; un plan qui laisse le serveur attribuer
l'identifiant d'une création.

### X. Tout changement d'état métier écrit un événement outbox dans la même transaction

**Règle.** Une transaction qui échoue n'envoie rien ; une transaction qui réussit envoie toujours ;
l'outbox est consommé par un worker en processus, sans file de messages.

**Motif.** Un SMS d'absence parti sans que l'absence soit enregistrée, ou une absence enregistrée
sans SMS, sont les deux faces d'une même perte de confiance. Le journal d'événements immuable est
aussi la fondation qui permettra un jour de rejouer un historique — une file purgée ne le permet
pas, un grand livre si ([ADR 001](../../docs/adr/001-hors-connexion-differe.md),
[ADR 003](../../docs/adr/003-monolithe-modulaire-microservices-plus-tard.md)).

**Non conforme.** Un plan qui notifie, envoie ou publie hors de la transaction qui change l'état ;
un plan qui écrit l'événement après le `COMMIT` ; un plan qui introduit un bus ou une file de
messages ; un plan dont une transition de machine à états n'émet aucun événement.

### XI. Les modules ne partagent jamais de transaction de base de données

**Règle.** Un schéma Postgres par module, aucune jointure inter-modules, aucune clé étrangère
traversante, aucune transaction SQL couvrant deux modules ; les lectures passent par l'interface
publique du module propriétaire, exposée dans son `__init__.py` ; les migrations Alembic vivent dans
le dossier du module et ne touchent jamais le schéma d'un autre.

**Motif.** C'est la seule condition qui rende l'extraction future d'un service indolore : un module
qui écrit dans le schéma d'un autre la rend impossible, quelle que soit la propreté des interfaces.
Le prix se paie tous les jours — facturer une fratrie exige d'interroger `scolarite` par son
interface avant d'écrire dans `finance`, deux allers-retours là où une jointure suffirait — et il est
payé sciemment ([ADR 003](../../docs/adr/003-monolithe-modulaire-microservices-plus-tard.md)).

**Non conforme.** Un plan qui joint deux schémas de modules, pose une clé étrangère entre eux, ou
ouvre une transaction qui traverse une frontière de module ; un plan qui fait lire une table d'un
autre module par `SELECT` plutôt que par son interface ; un plan dont une migration touche un
schéma étranger ; un plan qui fait importer `metier/` par `socle/`.

### XII. L'isolation des tenants est une double barrière

**Règle.** Row Level Security `ENABLE` **et** `FORCE` sur chaque table, avec un rôle applicatif
distinct du propriétaire ; `SET LOCAL app.current_tenant` dans chaque transaction, jamais à
l'ouverture de connexion ; **et** vérification applicative de la capacité et du périmètre — aucune
des deux barrières n'est jamais la seule ; une ressource hors du périmètre du tenant répond `404`,
jamais `403`.

**Motif.** Une fuite entre deux établissements est l'incident qui termine le produit, et il ne
s'agit pas de données commerciales : ce sont des dossiers de mineurs et des signalements. `ENABLE`
seul ne s'applique pas au propriétaire des tables, un `SET` à l'ouverture de connexion fuit avec le
pool, et le filtrage applicatif seul cède au premier oubli ; la RLS ne couvre pas le périmètre, un
enseignant du bon tenant verrait les notes d'une autre classe. Publier l'existence d'un
établissement tiers est déjà une fuite
([ADR 005](../../docs/adr/005-isolation-des-tenants-par-rls-et-double-barriere.md)).

**Non conforme.** Un plan dont une table neuve n'a pas `ENABLE` + `FORCE` avec sa politique ; un
plan qui pose le tenant sur la connexion ; un plan sans test d'isolation entre deux tenants ; un
plan qui répond `403` à une ressource d'un autre tenant. Le refus d'un en-tête d'établissement non
affilié est un autre cas, défini dans [docs/03-api.md](../../docs/03-api.md) : le principe vise la
ressource, pas l'en-tête.

### XIII. Le SMS est un canal de premier rang, pas un repli

**Règle.** Chaque type de message porte une variante par canal, **rédigée** pour ce canal, sous
160 caractères pour le SMS, vérifiée à l'enregistrement du modèle et non à l'envoi ; le budget est
contrôlé avant l'envoi, les fenêtres horaires sont respectées, et les notifications non urgentes se
regroupent en récapitulatif.

**Motif.** Une part significative des responsables légaux n'a ni smartphone ni forfait data : un
push n'atteint pas les familles qu'il faut atteindre, et il n'y a pas de notification native avant
Capacitor. Le SMS est aussi le poste de coût majeur du modèle économique — les deux faits sont vrais
en même temps. Découvrir à 7 h du matin qu'un modèle dépasse coûte deux SMS par famille, et sans
regroupement le modèle économique ne tient pas
([ADR 013](../../docs/adr/013-le-sms-est-un-canal-de-premier-rang.md),
[ADR 002](../../docs/adr/002-web-d-abord-capacitor-plus-tard.md)).

**Non conforme.** Un plan qui dérive la variante SMS par troncature d'un autre canal ; un plan qui
vérifie la longueur à l'envoi ; un plan qui envoie sans consulter le budget ou hors fenêtre ; un
plan qui émet un SMS unitaire pour un événement non critique ; un plan qui fait dépendre une
notification métier d'une notification push.

### XIV. L'IA propose, un humain nommé décide

**Règle.** Six capacités, trois niveaux d'autonomie, dont le troisième est un interdit absolu :
note finale et décision de passage, sanction disciplinaire, qualification d'une situation de
protection de l'enfance, diagnostic médical, décision RH individuelle, attribution ou retrait d'une
bourse, exclusion d'un élève ; aucun score de risque individuel d'élève n'est affiché — une alerte
est formulée en faits observables, jamais en jugement ; la plateforme reste pleinement
opérationnelle avec l'assistance désactivée par son réglage serveur, l'affordance disparaît de
l'écran au lieu d'être grisée, **et c'est un test**.

**Motif.** Trente-quatre agents autonomes sont cinq ou six capacités déclinées par domaine ;
l'autonomie sur la notation, la discipline, la santé et la paie expose l'établissement et l'éditeur ;
« prédire les risques d'échec » est du profilage de mineurs, et mal fait, il produit un effet
d'étiquetage durable sur des enfants. L'IA n'est pas ce qui fait acheter la première année, la
fiabilité oui — et ce qui est déterministe ne passe jamais par un modèle
([ADR 011](../../docs/adr/011-six-capacites-ia-pas-trente-quatre-agents.md),
[ADR 017](../../docs/adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md)).

**Non conforme.** Un plan qui donne un effet à une sortie d'IA sans validateur humain nommé et
journalisé ; un plan qui touche un interdit de niveau C ; un plan qui affiche un score, une
probabilité ou une étiquette sur un élève ; un plan dont un parcours cesse de fonctionner assistance
suspendue ; un plan qui implémente une capacité hors C1 et C5 au MVP, ou qui retire le test de
refus explicite d'une capacité non implémentée ; un plan qui fait calculer une moyenne, un barème ou
une relance par un modèle de langage.

### XV. Le poids d'un écran est une contrainte, pas un objectif

**Règle.** L'écran d'appel tient sous 120 Ko transférés, avec un premier affichage utile sous deux
secondes sur 3G lente ; un budget dépassé est un refus de fusion, pas une dette ; aucune chaîne
d'interface en dur — les clés `fr` et `en` naissent ensemble ; un refus s'annonce **avant** la
saisie et dit son versant positif, ce qu'on peut faire à la place.

**Motif.** Le poids est l'indicateur d'adoption : un parent qui consomme 5 Mo pour un bulletin n'y
revient pas, un enseignant dont l'écran d'appel met vingt secondes retourne à sa feuille, et sur le
web chaque octet se télécharge à chaque visite. Dans une base unique, rien n'empêche mécaniquement
une dépendance du back-office d'atterrir dans l'écran d'appel — c'est ce que P-10 mesure. Le
bilinguisme est dans le socle parce qu'il ne se rattrape pas après, et un refus découvert après la
saisie est une saisie perdue ([ADR 000](../../docs/adr/000-nuxt-et-rust-une-seule-application.md),
[ADR 002](../../docs/adr/002-web-d-abord-capacitor-plus-tard.md),
[docs/01-stack.md § 7.3](../../docs/01-stack.md)).

**Non conforme.** Un plan qui ajoute une dépendance, une police ou une image à un écran budgété
sans mesurer le poids ; un plan qui propose de « réduire plus tard » ; un plan qui écrit un libellé
en dur ou ne livre qu'une des deux langues ; un plan dont un refus n'apparaît qu'à la soumission ou
sans alternative ; un plan qui charge une ressource depuis un service distant sur le chemin du
premier affichage.

## Périmètre et portes de vérification

**Le périmètre du MVP est fermé.** Le segment est le primaire, et lui seul
([ADR 018](../../docs/adr/018-le-mvp-commence-par-le-primaire.md)) ; le hors-connexion est différé
([ADR 001](../../docs/adr/001-hors-connexion-differe.md)) ; l'application est web et installable,
sans Capacitor ([ADR 002](../../docs/adr/002-web-d-abord-capacitor-plus-tard.md)) ; il n'y a ni
microservices, ni file de messages, ni Kubernetes, ni ORM
([ADR 003](../../docs/adr/003-monolithe-modulaire-microservices-plus-tard.md),
[ADR 017](../../docs/adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md)) ; il n'y a ni
contenu pédagogique, ni LMS, ni comptabilité certifiée, ni paie déclarative, ni concours nationaux,
ni reconnaissance faciale. **`docs/06-apres-mvp.md` ne s'ouvre pas pour coder** : un plan qui s'y
réfère pour justifier une généralisation est non conforme, et la seule chose qu'une tranche doit
aux extensions futures tient dans la porte P-08.

**Chaque principe a sa porte mécanique** dans `scripts/verifier.sh`, et chaque porte a son test
négatif — une porte qui ne trouve jamais rien est indistinguable d'une porte qui n'a rien à
trouver. La correspondance qu'un plan doit citer :

| Principe | Porte | Ce qu'elle casse volontairement pour se prouver |
|---|---|---|
| I, II, XII | P-01, P-05 | Retirer une politique RLS ; rendre un écran inatteignable |
| III | P-11 | Un `import` vers `protection`, même au fond d'une fonction |
| V | P-09 | Un `if pack.pays == "CI"` dans le socle |
| VI, VII, VIII | P-08, P-12 | Une note en entier ; une colonne renommée sans sa requête |
| XI | P-01, P-04 | Une clé étrangère traversante ; un import de `metier/` par `socle/` |
| XV | P-06, P-10 | Une chaîne en dur ; 300 Ko d'image sur l'écran d'appel |
| Tous | P-02, P-03, P-07 | Une dépendance en intervalle ; un client généré avec diff ; une licence copyleft |

Une porte s'ajoute quand une erreur réelle s'est produite, ou quand son absence coûterait une fuite
entre clients — jamais parce qu'elle figurerait bien dans une liste. Le détail des douze portes est
dans [docs/01-stack.md § 7](../../docs/01-stack.md), et il fait foi.

## Méthode et définition de terminé

**Une tranche de la roadmap est un cycle Spec Kit** : `specify` → `plan` → `tasks` → `implement`,
avec le prompt déjà rédigé dans [docs/04-roadmap.md](../../docs/04-roadmap.md). La numérotation
suit l'epic, pas l'ordre d'exécution.

**Toute phase de planification lit d'abord** [docs/02-domaine.md](../../docs/02-domaine.md) et
[docs/03-api.md](../../docs/03-api.md), et **en dérive** — elle n'invente ni entité ni endpoint. Un
changement nécessaire se propose comme diff explicite sur le fichier projet **avant** de continuer,
jamais comme divergence locale. Une route neuve entre dans `03-api.md` dans le même changement que
son handler.

**Toute production visuelle lit d'abord le système de design.** `docs/design/theme.css` est la
seule source des valeurs visuelles, et le vocabulaire visible vient du country pack. Une revue
visuelle par tranche se tient en session dédiée, après `specify` et avant `plan`, un artboard par
user story ; une maquette validée se range selon la procédure de
[docs/05-design.md](../../docs/05-design.md).

**Rien n'est terminé tant que `scripts/verifier.sh` ne passe pas en une commande.** La définition
de terminé complète est en [docs/01-stack.md § 8.3](../../docs/01-stack.md) ; un plan la reprend, il
ne la réduit pas. Chaque `plan` porte un contrôle de constitution qui cite, pour chacun des quinze
principes, comment la tranche le respecte ou pourquoi elle s'en écarte — et un écart tacite est un
refus.

**Le journal se met à jour en fin de session** dans [docs/progress.md](../../docs/progress.md).
Une décision qui survit à la session part dans un ADR ; le journal n'en garde que le renvoi.

## Gouvernance

**Cette constitution fixe ce qui ne se négocie pas ; elle ne remplace aucune source de vérité.**

- [docs/02-domaine.md](../../docs/02-domaine.md) et [docs/03-api.md](../../docs/03-api.md) font
  foi sur le modèle et sur le contrat ;
- [docs/progress.md](../../docs/progress.md) dit où en est le produit et ce qui attend une réponse ;
- [docs/adr/](../../docs/adr/) porte les motifs — un principe d'ici est un condensé, l'ADR est
  l'original ;
- [docs/01-stack.md](../../docs/01-stack.md) porte les portes,
  [docs/05-design.md](../../docs/05-design.md) le système de design, et `docs/design/theme.css`
  les valeurs visuelles.

**Un principe se modifie par un ADR, pas par un commit.** Ajouter, retirer ou redéfinir un principe
exige un ADR accepté dans `docs/adr/`, qui expose le contexte, la décision, le prix accepté et les
alternatives écartées ; la constitution est ensuite amendée en citant cet ADR, et sa version
incrémentée. Un ADR renversé ou amendé n'est jamais réécrit : il porte sa note en tête, comme
l'ADR 017 l'a fait pour six de ses prédécesseurs.

**Les questions ouvertes ne sont pas des principes.** Ce qui attend une réponse dans
`docs/progress.md` — la granularité des capacités, le nombre d'agrégateurs, la stratégie de rendu,
le contenu du pack primaire — reste une question jusqu'à son ADR. Une décision non prise ne se
durcit pas par accident, et un plan qui tranche une question ouverte doit le dire.

**Versionnement.** `MAJEURE` quand un principe est retiré ou redéfini de façon incompatible ;
`MINEURE` quand un principe ou une section est ajouté ou matériellement étendu ; `CORRECTIF` pour
une clarification sans changement de sens. Chaque amendement met à jour le rapport de
synchronisation en tête de fichier et la ligne de version ci-dessous.

**Contrôle de conformité.** Chaque `plan` vérifie la tranche contre les quinze principes avant de
produire un modèle ou un contrat ; chaque revue vérifie qu'aucun écart n'est tacite ; chaque
`implement` se termine par `scripts/verifier.sh`. La constitution prime sur toute autre pratique en
cas de conflit, et la complexité ajoutée par une tranche se justifie par écrit contre le principe
qu'elle sert.

**Version** : 1.0.0 | **Ratifiée** : 2026-09-03 | **Dernier amendement** : 2026-09-03
