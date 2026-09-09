# 04 — Roadmap

*Onze epics, vingt-et-une tranches livrables. Chaque tranche est un prompt `/speckit-specify` prêt à
coller.*

---

## Le segment couvert

**Les vingt-et-une tranches servent un seul segment : le primaire.** Six niveaux du CP1 au CM2, un
maître polyvalent par classe, un appel par demi-journée, aucune série. Le préscolaire, le secondaire
général, le technique et le supérieur arrivent après le MVP, **dans cet ordre**
([ADR 018](adr/018-le-mvp-commence-par-le-primaire.md)).

Ce choix ne change **aucune** tranche de place et n'en ajoute aucune : il change les **hypothèses de
travail** de six d'entre elles — T2b, T5, T6a, T6b, T6c et T7 — et le cas nominal d'une septième, T8c.
Le tableau des conséquences est dans l'ADR ; ce qu'une tranche doit en retenir est écrit dans son
propre bloc.

---

## Comment cette liste est ordonnée

Quatre règles ont produit cet ordre, et elles priment sur l'envie de commencer par ce qui est
agréable.

1. **Ce qui est irréversible passe tôt.** Les capacités et le cloisonnement viennent avant tout écran
   métier : un système de rôles fixes ne se transforme pas en autorisation contextuelle par ajout, il
   se remplace — et avec lui toutes les vérifications d'accès du produit.
2. **Ce qui décide de l'adoption se teste tôt, en conditions réelles.** L'appel de séance et la saisie
   de notes sont les deux écrans qui décident si le produit est adopté ou reposé. Ils passent avant
   le confort, et ils s'éprouvent sur un vrai réseau, dans une vraie salle de classe.
3. **La frontière d'une dépendance externe se pose dès le début, l'implémentation vient plus tard.**
   Passerelle SMS, agrégateur de paiement, service d'inférence : les abstractions et leurs
   implémentations simulées existent dès T0a. Quand leur tranche arrive, c'est un **remplacement**,
   pas une découverte.
4. **Le moteur de messages précède l'appel.** Ce n'est pas intuitif, et c'est expliqué juste en
   dessous.

### Pourquoi le moteur de messages passe avant l'appel

C'est la seule décision d'ordre qui ne va pas de soi, et elle est documentée dans
[ADR 016](adr/016-le-moteur-de-messages-precede-l-appel.md).

**Un appel sans SMS n'est pas un demi-produit : c'est un autre produit.** Une feuille de présence
numérique remplace une feuille de papier — sans plus. Ce qui fait acheter, c'est que la famille sache
que l'enfant est absent **avant midi**, et le délai entre l'absence et le SMS est l'un des sept
indicateurs du brief.

Livrer l'appel d'abord et brancher le SMS ensuite coûte deux fois : on écrit un chemin de
notification provisoire, puis on le remplace, et **on démontre entretemps un produit qui n'a pas
l'argument qui le vend.**

> **Conséquence assumée** : le produit ne montre aucun écran de classe avant sa dixième tranche. C'est
> voulu. Les neuf premières posent ce sans quoi l'écran de classe serait à refaire.

### Pourquoi vingt-et-une tranches

Une tranche est un **point de validation**. Elle se découpe quand elle empaquette des sous-systèmes
qui ne partagent ni code, ni mode de défaillance, ni méthode de test — parce qu'un seul point de
validation pour deux natures de risque dilue l'attention là où elle vaut le plus cher.

Trois découpages possibles ont été **écartés** pour ne pas multiplier les cérémonies sans gain :
l'appel et l'absence restent ensemble (même écran, même mode de défaillance), le pilotage et l'export
restent ensemble (même lecture, aucun état), et le conseil de classe garde sa décision de passage
(l'un ne se teste pas sans l'autre). Le coût de ce resserrement est nommé à chaque fois qu'il se paie.

**La numérotation suit l'epic, pas l'ordre d'exécution.** `T4a` est la neuvième tranche à construire
mais appartient à l'epic communication. La colonne **rang** donne l'ordre réel.

### Vue d'ensemble

| Rang | Tranche | Poids | Risque | Ce qu'on sait faire à la fin |
|---|---|---|---|---|
| 1 | **T0a** Le socle serveur | ▪▪ | Faible | Un endpoint répond avec un client typé régénéré sans retouche |
| 2 | **T0b** Le socle d'interface | ▪▪▪ | Faible | Les quatorze composants s'affichent en clair et en sombre |
| 3 | **T1a** Se connecter et savoir où l'on est | ▪▪▪ | **Élevé** | Une enseignante ouvre son espace par OTP, et aucun tenant n'en voit un autre |
| 4 | **T1b** Les capacités, les rôles et les périmètres | ▪▪▪ | **Élevé, irréversible** | Un censeur qui tient aussi la pédagogie voit **une** interface, et le dossier psychosocial reste fermé |
| 5 | **T2a** L'année scolaire et sa bascule | ▪▪▪ | **Élevé, irréversible** | Deux années coexistent : on réinscrit pour septembre pendant que le 3ᵉ trimestre tourne |
| 6 | **T2b** La structure pédagogique | ▪▪ | Moyen | Une classe de CM2 dédoublée en deux groupes de soutien a un appel juste |
| 7 | **T3a** Les personnes, les foyers et les liens | ▪▪▪ | **Élevé** | Un enfant confié à sa tante en ville a un tuteur de fait, et la facture s'éclate 60/40 |
| 8 | **T3b** L'élève et son inscription | ▪▪▪ | Moyen | Un dossier incomplet dit ce qui manque **avant** qu'on tente de valider |
| 9 | **T4a** Le moteur de messages, le routage et le budget | ▪▪▪ | **Élevé** | Un événement produit un SMS de moins de 160 caractères, dans la fenêtre horaire, sous budget |
| 10 | **T5** L'appel, l'absence et sa justification | ▪▪▪ | **Élevé, ergonomique** | Une classe de 40 est appelée **en moins de 45 s**, et la famille reçoit le SMS en moins de 10 min |
| 11 | **T6a** Le référentiel d'évaluation et son moteur | ▪▪▪ | **Très élevé, irréversible** | Un pack fictif sur 10 avec deux périodes produit des moyennes justes, et une échelle non numérique ne coûte aucune ligne de moteur |
| 12 | **T6b** La saisie de notes | ▪▪ | **Élevé, ergonomique** | Le réseau tombe à la 38ᵉ note sur 40 : **rien n'est perdu** |
| 13 | **T6c** Le bulletin | ▪▪▪ | Élevé | Un bulletin réédité trois ans plus tard est identique à l'original |
| 14 | **T7** Le conseil de classe et la décision de passage | ▪▪▪ | Élevé | Le conseil des maîtres a son dossier prêt sans qu'on l'ait compilé ; la décision se verrouille à la notification |
| 15 | **T8a** La grille tarifaire et la facturation par foyer | ▪▪▪ | Élevé | Une fratrie de trois sur deux cycles produit **une** facture, remise fratrie comprise |
| 16 | **T8b** L'encaissement, la caisse et le reçu | ▪▪▪ | **Très élevé** | Un webhook qui arrive deux fois n'encaisse qu'une fois ; la caisse tombe juste |
| 17 | **T8c** Le financement public et la créance sur l'État | ▪▪ | Élevé | L'état des arriérés par année sort en un clic |
| 18 | **T4b** Les circulaires et la messagerie journalisée | ▪▪ | Moyen | Aucun message adulte-mineur n'est supprimable, et un tiers peut le lire |
| 19 | **T9** Le registre de protection de l'enfance | ▪▪ | **Très élevé** | Un signalement confidentiel part sans auteur, et le chef d'établissement concerné ne le lit pas |
| 20 | **T10a** L'import et la reprise | ▪▪▪ | Élevé | Un établissement de 800 élèves est opérationnel en moins de deux semaines |
| 21 | **T10b** Le pilotage et l'export | ▪▪ | Moyen | Le tableau de bord distingue facturé, encaissé et encaissable |

### Comment utiliser une tranche

Chaque tranche porte un bloc à copier tel quel. Le cycle est `specify` → `plan` → `tasks` →
`implement`. La **description d'epic** qui précède les blocs porte le pourquoi commun ; elle ne se
colle pas, elle se lit.

> **Toute phase de planification lit [02-domaine.md](02-domaine.md) et [03-api.md](03-api.md), et en
> dérive.** Si une entité ou un endpoint manque, on **propose un diff sur le fichier projet et on
> attend l'arbitrage** — on ne diverge jamais localement.

**Après chaque `specify` conclu, on produit le prompt de revue visuelle** et on le lance en session
dédiée, avant `plan`. Le gabarit est en fin de [05-design.md](05-design.md).

---

## Ce qu'une tranche ne doit pas fermer

Le produit d'aujourd'hui sert l'école primaire d'un groupe scolaire privé d'Abidjan ;
[06-apres-mvp.md](06-apres-mvp.md) décrit ce qui pourrait venir ensuite — quatre segments, trois
vagues de pays, quarante-trois modules.
**Neuf tranches sur vingt-et-une peuvent, sans le vouloir, rendre cette suite impossible.** Les douze
autres n'ont rien à surveiller, et le savoir est aussi utile.

> ⚠️ **La référence opérationnelle est la porte P-08, pas ce document-ci ni le 06.**
> Une tranche a besoin de **huit contrôles mécaniques** ([01-stack.md § 7.1](01-stack.md)), pas de
> quatre cents lignes de stratégie multi-segments. Lire l'après-MVP au moment de coder une tranche,
> c'est s'exposer au premier risque que ce document identifie lui-même : **la vision plateforme qui
> contamine le MVP.** Le tableau ci-dessous est une carte pour l'humain qui arbitre ; P-08 est ce qui
> garde.

Le risque n'est jamais un choix délibéré. Il ressemble à ceci : on écrit une note en nombre entier
parce qu'un devoir se note sur 20 en points ronds, et trois ans plus tard il faut migrer toutes les
notes du produit pour qu'un pack ghanéen puisse noter sur 100 avec décimales.

| Tranche | Ce qu'elle pourrait fermer | Ce qui la garde |
|---|---|---|
| **T0a** | La hiérarchie de paquets — le socle contaminé par un module, `protection` importé | Portes **P-04** et **P-11**, mécaniques — **des tests, là où un compilateur suffisait** |
| **T1b** | Rôles fixes au lieu de capacités + périmètre ; une capacité cloisonnée ajoutable à un rôle | Porte **P-11** + le refus explicite `HAB_CAPACITE_CLOISONNEE_NON_ROLABLE` |
| **T2a** | Une entité pédagogique sans `annee_id` — et les bulletins archivés deviennent faux | Porte **P-08** |
| **T2b** | Le coefficient posé sur la matière au lieu de l'enseignement ; le dédoublement au niveau de la classe | Porte **P-08** |
| **T3a** | Le lien de responsabilité réduit à « père / mère » — et le tuteur de fait devient inexprimable | Revue + le jeu de cas |
| **T5** | L'absence en paire de dates au lieu d'un intervalle — l'appel par UE du supérieur devient un second modèle | Porte **P-08** |
| **T6a** | **La tranche la plus exposée du corpus.** Une échelle sur 20 en dur, un `match pays`, une règle d'arrondi implicite : chacune condamne l'extension anglophone | Porte **P-09** + le **test d'agnosticité**, permanent |
| **T8a** | Un montant en virgule flottante ; une devise sans exposant | Porte **P-08** |
| **T10b** | Des indicateurs taillés pour une école primaire seule, alors que le consolidé devra comparer une maternelle et un lycée | Revue |

**Ce qui n'est pas demandé** : construire quoi que ce soit pour ces extensions. Une provision est une
colonne ou un référentiel, jamais une fonctionnalité. Ce qui est demandé est plus modeste et plus
efficace — **ne pas la retirer**.

> **La règle en une phrase** : une tranche du MVP peut tout ignorer de l'après-MVP, sauf les colonnes
> qu'elle n'a pas le droit de dégrader. P-08 les garde ; ce tableau dit lesquelles.

---

# Étape 0 — La constitution

**Avant T0a, et avant toute autre chose.** Spec Kit installe une constitution vide ; c'est le fichier
que **chaque `plan` vérifie**. Tant qu'il porte les jetons du gabarit, une tranche peut être planifiée
sans être contrôlée contre quoi que ce soit — et c'est exactement ce qu'on cherche à éviter.

Le bloc ci-dessous ne contient aucune décision neuve : il **rassemble ce que le corpus a déjà
tranché** et le rend opposable à chaque plan.

```text
/speckit-constitution Rédige la constitution du projet Nelo à partir des quinze principes ci-dessous.
Ils ne sont pas à inventer : ils condensent des décisions déjà prises et documentées. Lis d'abord
CLAUDE.md, docs/00-brief.md, docs/01-stack.md et les dix-neuf fichiers de docs/adr/ pour en tirer les
motifs — un principe sans son pourquoi ne survit pas à la première contrainte de calendrier.

1. LE SERVEUR EST LA SEULE AUTORITÉ. L'interface masque, l'API refuse. Chaque appel revérifie la
   capacité ET le périmètre. Aucune vérification côté client n'est jamais la seule. Le client
   n'applique aucune formule de composition, ne convertit aucune note en mention, ne calcule aucun
   rang, aucun solde, aucune pénalité : il affiche ce que le serveur a calculé.

2. L'INTERFACE SE COMPOSE À PARTIR DES CAPACITÉS, JAMAIS DES RÔLES. Les capacités effectives d'une
   personne sont l'union de ses affectations, chacune liée à un rôle ET à un périmètre. Aucune liste
   de rôles n'est codée en dur côté client. Une action non autorisée est ABSENTE de l'écran, jamais
   grisée. L'absence de capacité affiche un message qui nomme l'administrateur de l'établissement,
   jamais une page vide ni une erreur technique.

3. LE CLOISONNEMENT PRIME SUR LES HABILITATIONS, ET C'EST UNE FRONTIÈRE D'IMPORT. Dossier médical,
   psychosocial, signalements, disciplinaire en instruction, paie individuelle : ces capacités ne
   sont PAS ajoutables à un modèle de rôle et s'attribuent nominativement, avec motif et date de fin.
   Aucun paquet n'importe le module de protection, et c'est tenu par trois verrous : aucune
   déclaration de dépendance, un test de graphe d'imports, et un module d'interface qui n'expose rien
   hors de son service. Un compilateur refusait, un test signale : c'est plus faible que la garantie
   d'origine, et le plan qui s'en écarte doit le dire. Toute lecture s'écrit dans le journal d'accès,
   y compris en cas de refus. Un chef d'établissement n'a pas accès par défaut au contenu d'un
   signalement qui le concerne.

4. TOUTE DONNÉE D'ÉLÈVE EST UNE DONNÉE DE MINEUR. Base légale, durée de conservation et journal
   d'accès sont définis pour chaque traitement, DANS LE MODÈLE. Aucune donnée d'élève n'existe sans
   qu'on sache qui peut la lire, combien de temps, et à quel titre.

5. LE PAYS NE VIT QUE DANS LE COUNTRY PACK, ET LE SEGMENT NON PLUS. Aucune littérale de pays, de
   devise, d'examen, de découpage d'année ou d'échelle de notation hors du pack. Aucun cycle, aucun
   niveau, aucune série, aucune composition d'instance écrits dans le code. Aucune branche
   conditionnée par le pays ni par le segment : le MVP sert le primaire, et aucune ligne ne le sait.
   Le test d'agnosticité — un pack fictif à échelle sur 10 et deux périodes fonctionnant de bout en
   bout — est permanent.

6. LE RÉFÉRENTIEL D'ÉVALUATION EST UNE DONNÉE VERSIONNÉE, PAS DU CODE. Échelle, table de conversion,
   formule de composition en arbre déclaratif, règles d'arrondi, règles de rang, gabarit de bulletin.
   Le moteur est un interpréteur, pas une fonction par pays. Toute moyenne porte la version qui l'a
   produite et est recalculable à l'identique. Un référentiel publié est figé : on en crée une
   version, on ne le modifie pas.

7. TOUTE ENTITÉ PÉDAGOGIQUE PORTE SON ANNÉE. Rien n'est global : ni une classe, ni un coefficient, ni
   un tarif, ni une affectation de rôle. Deux années coexistent — une active, une en préparation. Une
   affectation expire avec son année et se reconduit explicitement, jamais par défaut.

8. TOUT MONTANT EST UN ENTIER D'UNITÉ MINEURE, avec l'exposant porté par la devise du pack. TOUTE
   NOTE ET TOUT COEFFICIENT SONT NUMERIC. TOUTE OCCUPATION ET TOUTE ABSENCE SONT UN INTERVALLE
   [début, fin). Jamais de flottant sur un montant, jamais un entier sur une note, jamais une paire
   de dates sur une absence.

9. AUCUNE SAISIE NE SE PERD. Toute écriture porte une clé d'idempotence générée par le client, et sa
   réponse est mémorisée. Les saisies longues — appel, notes — s'enregistrent par petits lots au fil
   de l'eau, jamais en un envoi unique. L'utilisateur voit en permanence si sa saisie est sur le
   serveur ou en attente. C'est là que se perd la confiance.

10. TOUT CHANGEMENT D'ÉTAT MÉTIER ÉCRIT UN ÉVÉNEMENT OUTBOX DANS LA MÊME TRANSACTION. Une
    transaction qui échoue n'envoie rien ; une transaction qui réussit envoie toujours.

11. LES MODULES NE PARTAGENT JAMAIS DE TRANSACTION DE BASE DE DONNÉES. Un schéma par module, aucune
    jointure inter-modules, aucune clé étrangère traversante, et les lectures passent par
    l'interface publique du module propriétaire. C'est la seule condition qui rende l'extraction
    future d'un service indolore.

12. L'ISOLATION DES TENANTS EST UNE DOUBLE BARRIÈRE. Row Level Security ENABLE ET FORCE sur chaque
    table, SET LOCAL du tenant dans chaque transaction, ET vérification applicative de la capacité et
    du périmètre. Une ressource hors du périmètre du tenant répond 404, jamais 403.

13. LE SMS EST UN CANAL DE PREMIER RANG, PAS UN REPLI. Chaque type de message porte une variante par
    canal, RÉDIGÉE pour ce canal, sous 160 caractères pour le SMS, vérifiée à l'enregistrement du
    modèle et non à l'envoi. Le budget est contrôlé avant l'envoi, les fenêtres horaires sont
    respectées, et les notifications non urgentes se regroupent en récapitulatif.

14. L'IA PROPOSE, UN HUMAIN NOMMÉ DÉCIDE. Six capacités, trois niveaux d'autonomie. Interdits
    absolus : note finale et décision de passage, sanction disciplinaire, qualification d'une
    situation de protection de l'enfance, diagnostic médical, décision RH individuelle, attribution
    ou retrait d'une bourse, exclusion d'un élève. Aucun score de risque individuel d'élève n'est
    affiché : une alerte est formulée en faits observables, jamais en jugement. La plateforme reste
    pleinement opérationnelle avec l'assistance désactivée par son réglage serveur, et c'est un
    test.

15. LE POIDS D'UN ÉCRAN EST UNE CONTRAINTE, PAS UN OBJECTIF. L'écran d'appel tient sous 120 Ko. Un
    budget dépassé est un refus de fusion, pas une dette. Aucune chaîne d'interface en dur : les
    clés fr et en naissent ensemble. Un refus s'annonce AVANT la saisie et dit son versant positif —
    ce qu'on peut faire à la place.

Pour chaque principe : un intitulé court, la règle en une phrase opposable, le motif en une ou deux
phrases, et la manière dont un plan peut être jugé non conforme. Ajoute une section de gouvernance
qui dit qu'un principe se modifie par un ADR, pas par un commit, et qui renvoie vers
docs/02-domaine.md et docs/03-api.md comme sources de vérité projet, docs/progress.md pour l'état
courant, docs/adr/ pour les motifs. La constitution ne les remplace pas : elle fixe ce qui ne se
négocie pas.
```

**Après ratification**, deux vérifications valent la peine : que la constitution ne contredit aucun
ADR, et que les questions encore ouvertes de [progress.md](progress.md) n'y sont pas transformées en
principes — une décision non prise ne se durcit pas par accident.

---

# T0 — Fondations

Avant d'écrire une ligne de métier, on doit pouvoir lancer le produit d'une commande, le voir à
l'écran, et savoir qu'il est juste sans relire des fichiers. L'environnement tourne entièrement sur
le poste : aucun service distant, aucune clé d'API, parce qu'une démonstration dans un établissement
d'Abidjan ne peut dépendre ni du réseau ni d'un compte cloud.

**Cet epic se découpe par pile, pas par fonction** — ses éléments sont mutuellement bloquants et un
découpage fonctionnel n'aurait aucun sens. Le point de jonction entre les deux tranches est le
contrat d'API et la génération du client qui en découle.

**Contraintes communes** : aucun service tiers distant requis pour développer ; toute intégration
externe vit derrière une abstraction avec une implémentation simulée qui **sait échouer autant que
réussir** ; chaque porte de vérification a son test négatif.

**Hors périmètre de l'epic** : toute logique métier, tout écran de travail, toute intégration réelle,
tout déploiement.

> ⚠️ **Exception de rédaction assumée** : ces deux tranches nomment la pile technique, parce qu'ici
> la pile *est* le sujet. Toutes les tranches suivantes s'en abstiennent.

## T0a — Le socle serveur

**Risque** : faible, bloquant. **Poids** : 45 % de l'epic.

```text
/speckit-specify Besoin : poser le socle serveur et prouver qu'il tient, avant qu'aucune règle métier
n'existe. Un développeur seul n'a pas le temps de relire des spécifications pour vérifier qu'un
changement est juste : les contrôles doivent être mécaniques et tenir dans une seule commande.

La pile est nommée ici parce qu'elle EST le sujet de la tranche : FastAPI et Pydantic pour l'API,
SQLAlchemy Core et asyncpg pour l'accès aux données — jamais l'ORM —, Alembic pour les migrations avec
un dossier par module, uv pour l'environnement et le verrouillage des dépendances, ruff pour le style
et l'analyse, pytest pour les tests.

Livrer :
- un environnement décrit par un fichier de composition unique, démarré par une seule commande, qui
  fournit la base de données, le magasin éphémère et le stockage d'objets — TROIS SERVICES, pas un de
  plus. Le service d'inférence n'en est pas un : c'est une dépendance externe derrière son interface ;
- l'espace de travail découpé en paquets selon la hiérarchie domaine, socle, metier, segments, avec
  les tests de GRAPHE D'IMPORTS qui échouent si un paquet du socle importe un paquet metier, ET si un
  paquet quelconque importe le module de protection — y compris par un import différé au fond d'une
  fonction. Ce que le compilateur donnait gratuitement est ici un test à écrire et à maintenir ;
- le cloisonnement du module de protection tenu par TROIS VERROUS : aucune déclaration de dépendance,
  le test de graphe d'imports, et un module d'interface qui n'expose rien hors de son service ;
- un module doré écrit à la main de bout en bout — entité, accès aux données, service, gestionnaire
  de requête, tests — qui servira de patron à tous les suivants. Pas de généricité prématurée : du
  code concret se refactore, une abstraction prématurée se subit ;
- l'isolation par tenant : politique de sécurité au niveau ligne activée ET forcée sur chaque table,
  variable de tenant posée dans chaque transaction et jamais à l'ouverture de connexion, avec le test
  d'isolation entre deux tenants ;
- l'idempotence : tout appel d'écriture porte un identifiant de requête généré par le client, la
  réponse est mémorisée, un rejeu identique renvoie la même réponse sans réexécuter l'effet, un rejeu
  divergent est refusé ;
- la table d'événements et le travailleur qui la consomme, dans le même processus ;
- la génération de la spécification d'API depuis les schémas de validation et les routes annotées, et
  la génération du client typé depuis cette spécification. Le refus de validation est un CITOYEN DE
  PREMIER RANG du contrat : il porte son propre code d'erreur et le chemin de chaque champ fautif ;
- l'emplacement de l'assistance : un paquet du socle, jamais un service à déployer. Cette tranche pose
  le paquet, son interface et le RÉGLAGE SERVEUR du catalogue de paramètres qui la suspend à sa
  portée ; les deux capacités elles-mêmes arrivent avec leurs tranches ;
- les abstractions des dépendances externes avec leur implémentation SIMULÉE : passerelle de messages
  courts, agrégateur de paiement, service d'inférence. Chaque simulation sait échouer aussi bien que
  réussir — accusé en retard, accusé en double, accusé jamais reçu — et son mode d'échec est
  déclenchable depuis la configuration ;
- une commande de vérification unique qui enchaîne tout ce qui doit passer et sort en échec au
  premier contrôle rouge, avec les portes qui concernent le serveur : le schéma s'applique sur une
  base vierge — un dossier de migration par module — et chaque table porte sa politique d'isolation ;
  aucune clé étrangère ne traverse le schéma d'un module ; aucune dépendance n'est déclarée en
  intervalle et les deux fichiers de verrouillage sont commités ; le client régénéré ne produit aucun
  écart non commité ; aucun paquet du socle n'importe un paquet metier ; aucun paquet n'importe la
  protection ; TOUTE FONCTION D'ACCÈS AUX DONNÉES EST EXERCÉE AU MOINS UNE FOIS CONTRE LA BASE
  FRAÎCHEMENT MIGRÉE, parce qu'aucun compilateur ne vérifie plus les requêtes ; aucune dépendance ne
  porte une licence copyleft fort.

Contraintes non négociables :
- une abstraction dont la signature ne pourrait pas être servie par une vraie implémentation est une
  abstraction mal dessinée — on écrit l'interface en pensant aux deux ;
- chaque porte a SON TEST NÉGATIF : on la casse volontairement une fois pour vérifier qu'elle échoue
  vraiment. Une porte qui ne trouve jamais rien est indistinguable d'une porte qui n'a rien à
  trouver ;
- l'assistance désactivée est un TEST, pas une hypothèse : la vérification pose le réglage de
  suspension et reparcourt le module doré. L'affordance disparaît de l'écran, elle n'est pas grisée ;
- une requête SQL n'est plus vérifiée par la compilation : toute fonction d'accès aux données non
  exercée par un test FAIT ÉCHOUER la vérification, elle ne baisse pas une couverture ;
- aucun serveur d'intégration continue à ce stade. Ce qui a de la valeur est que le contrôle soit
  mécanique, pas qu'une machine le lance.

Hors périmètre : toute logique métier, tout écran, toute intégration réelle, tout déploiement, et les
portes qui concernent l'interface — elles sont livrées par T0b.

Risque : faible, mais bloquant pour tout le reste.
Critère de fin : le module doré répond sur son endpoint avec un client typé régénéré sans écart, et
la vérification échoue quand on casse volontairement chacune des sept portes.

Contexte projet : lire docs/01-stack.md (structure du dépôt, hiérarchie des paquets, environnement
local, portes de vérification) et docs/03-api.md sections 1 et 3 (conventions, enveloppe d'erreur,
règles de conception opposables). Ne rien inventer hors de ces fichiers.
```

## T0b — Le socle d'interface

**Risque** : faible, bloquant. **Poids** : 55 % de l'epic.

**Reste volontairement la plus grosse tranche du corpus.** La découper serait pire : la règle du
design system veut qu'un composant manquant **arrête** un cycle, donc livrer six composants sur
quatorze garantit un arrêt à la deuxième tranche métier.

```text
/speckit-specify Besoin : poser la coquille de l'application et sa bibliothèque de composants, pour
que toutes les tranches suivantes assemblent au lieu de dessiner. Le produit tourne sur le téléphone
d'entrée de gamme d'une enseignante en salle de classe, sur une tablette de saisie, sur un poste
partagé de secrétariat et sur le téléphone d'un parent avec un forfait data compté : il se construit
du plus petit gabarit vers le plus grand.

Livrer :
- l'application mobile-first et responsive, avec le fichier de thème copié TEL QUEL depuis les actifs
  de design — il est autosuffisant et ne se réécrit pas ;
- la coquille INSTALLABLE — la PWA est la cible, pas un confort : manifeste, icônes, affichage
  autonome, installation vérifiée sur Chromium et WebKit, aucune dépendance à la barre d'adresse ni à
  un rechargement manuel ; les capacités de plateforme (état du réseau, stockage, caméra,
  notifications) derrière UNE interface unique côté client à une seule implémentation web, pour que
  Capacitor et Tauri l'empaquettent plus tard sans réécriture ; un service worker mince, sans logique
  métier ni cache d'écriture ;
- les quatorze composants canoniques dans TOUS leurs états, en clair et en sombre : bouton, champ,
  interrupteur, pastille d'état, pastille de canal, recherche, avatar, fil d'Ariane, onglets, carte
  d'indicateur, alerte, ligne de tableau, ruban d'état de saisie, coquille d'application ;
- LE RUBAN D'ÉTAT DE SAISIE, qui est le composant le plus important de la tranche : il dit l'heure du
  dernier enregistrement, le nombre de saisies en attente et la qualité du lien, en trois formes et
  trois mots. IL NE BLOQUE JAMAIS LA SAISIE ;
- la coquille qui SE COMPOSE à partir d'un point d'entrée de contexte : un utilisateur mono-domaine
  atterrit dans son domaine, un multi-domaines reçoit un tableau composé, un utilisateur sans
  capacité voit un message qui nomme l'administrateur de son établissement. AUCUNE LISTE DE RÔLES
  N'EST CODÉE EN DUR ;
- l'externalisation des chaînes avec les clés fr et en créées ENSEMBLE, et la résolution des libellés
  métier depuis le pack de pays plutôt que depuis le code ;
- une page de style qui affiche tous les composants dans tous leurs états, côte à côte en clair et en
  sombre, servie en développement ;
- la mesure du poids par écran, avec le budget déclaré par écran et l'échec au dépassement ;
- les portes qui concernent l'interface : chaque écran s'atteint dans un navigateur réel, en clair et
  en sombre, sur deux moteurs de rendu ; aucune chaîne d'interface en dur ; aucun écran budgété ne
  dépasse son plafond.

Contraintes non négociables :
- mobile-first : 390 px de large est la cible de conception, pas un cas dégradé. Une colonne sur
  mobile, deux à partir de 768 px, trois à partir de 1200 px ;
- un tableau ne se réduit pas, il se transforme : sur mobile, une ligne devient une carte avec le
  libellé au-dessus de la valeur ;
- cible tactile de 52 px en classe, 48 ailleurs, 44 en plancher absolu — jamais moins, nulle part ;
- un état n'est jamais porté par la couleur seule : il porte aussi une forme et un mot ;
- l'ocre porte l'attente et l'échéance, jamais l'erreur. Le rouge est réservé à l'impayé et à
  l'absence non justifiée ;
- rien n'est masqué derrière un survol : il n'y a pas de survol au doigt ;
- les valeurs de couleur ne sont JAMAIS écrites ailleurs que dans le fichier de thème ;
- monter un composant dans un test ne prouve pas qu'une page s'atteint : la porte ouvre un vrai
  navigateur.

Hors périmètre : toute donnée réelle, toute règle métier, toute persistance. Les composants
s'affichent sur des données de démonstration.

Risque : faible, mais bloquant. C'est la tranche dont dépend la vitesse de toutes les suivantes.
Critère de fin : la page de style montre les quatorze composants dans tous leurs états, en clair et
en sombre, la porte de poids échoue quand on ajoute une image de 300 Ko à l'écran budgété le plus
serré, et l'application s'installe sur l'écran d'accueil depuis Chromium et WebKit.

Contexte projet : lire docs/05-design.md en entier, docs/design/theme.css (la seule source des
valeurs), docs/design/ecrans/13_systeme-de-design.html (les composants et leurs états),
docs/03-api.md section 1.9 (le contexte qui compose l'interface) et docs/adr/002 (la PWA est la
cible, et ce que le MVP livre pour l'empaquetage). Ne rien inventer hors de ces fichiers.
```

---

# T1 — Identité et capacités

Qui est la personne, ce qu'elle peut faire, et sur quoi. **Cet epic est le plus irréversible du
corpus** : un système de rôles fixes ne se transforme pas en autorisation contextuelle par ajout, il
se remplace — et avec lui toutes les vérifications d'accès du produit.

Il se découpe en deux parce que l'authentification et l'autorisation n'ont ni le même mode de
défaillance, ni la même méthode de test : la première se teste par un parcours, la seconde par une
matrice de personas.

**Hors périmètre de l'epic** : tout écran métier, toute donnée d'élève.

## T1a — Se connecter et savoir où l'on est

**Risque** : élevé. **Poids** : 40 % de l'epic.

```text
/speckit-specify Besoin : permettre à une personne de s'identifier et d'arriver là où elle travaille,
sur un poste qui est probablement partagé. L'identifiant est le NUMÉRO DE TÉLÉPHONE, pas l'adresse
électronique : beaucoup de responsables légaux n'en ont pas.

Livrer :
- l'ouverture de session par code à usage unique envoyé par message court, avec expiration et
  limitation du nombre de tentatives ;
- le code personnel court pour les usages fréquents, une fois l'appareil connu : une enseignante qui
  fait l'appel six fois par jour ne reçoit pas six messages ;
- le jeton de rafraîchissement en cookie non lisible par script, avec rotation à chaque usage — le
  choix est délibéré parce que les postes sont partagés et qu'un jeton en stockage de navigateur
  survit à la fermeture de session ;
- la révocation IMMÉDIATE par liste consultée à chaque requête, pas par expiration du jeton : le
  départ d'un membre du personnel coupe l'accès le jour même ;
- l'activation d'un compte depuis un lien à usage unique reçu par message court ;
- la sélection de l'établissement actif et de l'année de travail, portées par des en-têtes de requête
  vérifiés contre les affectations du compte ;
- le point d'entrée de contexte qui renvoie tout ce dont l'interface a besoin pour ne rendre que ce
  qui existe.

Contraintes non négociables :
- la demande de code répond de la même façon quel que soit le numéro, et le code ne part que si le
  compte existe : publier l'existence d'un compte à partir d'un numéro est une fuite ;
- un établissement non affecté répond « interdit », jamais « introuvable » : ne pas publier
  l'existence d'un établissement tiers ;
- omettre l'année sur une route pédagogique est une erreur, JAMAIS un repli silencieux sur l'année
  active — un repli implicite écrit une note dans la mauvaise année ;
- les comptes partagés sont interdits explicitement côté personnel et tolérés côté famille avec
  traçabilité : deux parents partageant un téléphone est le cas normal ;
- le numéro de téléphone change souvent : la procédure de changement fait partie de la tranche, pas
  d'une reprise ultérieure.

Hors périmètre : les capacités et les périmètres, livrés par T1b. Ici, un compte authentifié n'a
encore le droit de rien.

Risque : élevé — c'est la première frontière de sécurité du produit.
Critère de fin : une personne ouvre son espace par code à usage unique puis par code personnel, et
aucun compte d'un tenant ne voit une donnée d'un autre.

Contexte projet : lire docs/02-domaine.md sections 3.1 et 3.2 (les quatre couches, le compte),
docs/03-api.md sections 1.2, 1.9, 2.1 et 2.2 (authentification, contexte, routes), et
docs/01-stack.md section 5.1 (session sur poste partagé). Ne rien inventer hors de ces fichiers.
```

## T1b — Les capacités, les rôles et les périmètres

**Risque** : élevé, **irréversible**. **Poids** : 60 % de l'epic.

```text
/speckit-specify Besoin : décider ce qu'une personne peut faire et sur quoi, sachant que la
répartition des fonctions varie énormément d'un établissement à l'autre À TAILLE ÉGALE. Dans une
école de 400 élèves, une seule personne tient la scolarité, la pédagogie et l'emploi du temps ;
dans un groupe de 3000, ce sont trois services. Un produit qui impose un découpage fixe force le
petit établissement à partager des mots de passe et le grand à accorder des droits trop larges.

Livrer :
- le référentiel de capacités, nommées PAR VERBE MÉTIER et non par opération technique, de l'ordre de
  cinq à douze par service, chacune portant son domaine et un indicateur de cloisonnement ;
- les modèles de rôle livrés par segment, que l'établissement CLONE ET AJUSTE LUI-MÊME, sans
  intervention de l'éditeur ;
- l'affectation, qui lie une personne à un rôle ET à un périmètre — sites, cycles, classes, matières —
  ET à une année. Un rôle sans périmètre ne veut rien dire ;
- le calcul des capacités effectives comme UNION des affectations, et le point d'entrée qui les
  renvoie avec leurs périmètres ;
- la délégation temporaire, avec DATE DE FIN OBLIGATOIRE et expiration automatique : le censeur qui
  remplace le proviseur absent ne garde pas ses droits en septembre ;
- l'accès nominatif aux capacités cloisonnées : une personne à la fois, avec motif, date de fin et
  traçabilité — et le REFUS EXPLICITE si l'on tente d'ajouter une capacité cloisonnée à un modèle de
  rôle ;
- le journal d'accès en insertion seule, écrit à chaque lecture de donnée cloisonnée, Y COMPRIS quand
  elle est refusée ;
- la suspension immédiate d'un compte, avec révocation des sessions en cours ;
- la revue des accès : liste des comptes actifs et de leurs périmètres, exportable, à passer en revue
  à chaque rentrée ;
- la composition de l'interface à partir des capacités : navigation, densité, écran d'accueil, écrans
  partagés, recherche, exports, notifications, absence de capacité.

Contraintes non négociables :
- le refus d'ajouter une capacité cloisonnée à un rôle est un REFUS DE CONCEPTION, pas de
  configuration : il ne se contourne par aucun réglage ;
- une affectation expire avec son année et se reconduit EXPLICITEMENT, jamais par défaut. À la
  bascule, une personne non reconduite voit un message clair, pas une interface vide ;
- une capacité introduite par une mise à jour n'est JAMAIS accordée automatiquement aux rôles
  existants : elle est proposée à l'administrateur de l'établissement, qui décide ;
- un export ne doit jamais être une porte dérobée vers des données que l'écran refuse d'afficher ;
- pas de menu grisé : un domaine n'apparaît que si la personne y détient au moins une capacité ;
- le serveur refuse quand même : chaque appel revérifie la capacité ET le périmètre. Le masquage
  côté interface n'est jamais une protection ;
- le cumul rend les tests combinatoires : on ne teste pas toutes les combinaisons, on teste un jeu de
  PERSONAS correspondant aux cumuls réellement observés — au minimum le censeur qui tient scolarité
  et pédagogie, l'enseignante professeure principale, la secrétaire-économe, et l'enseignant qui est
  aussi parent d'un élève de l'établissement.

Hors périmètre : les données sur lesquelles ces capacités portent. Ici, on autorise l'accès à des
ressources qui n'existent pas encore.

Risque : élevé et IRRÉVERSIBLE. C'est la tranche qu'on ne rattrape pas.
Critère de fin : les quatre personas voient chacun une interface différente et cohérente, aucun ne
peut lire un dossier psychosocial sans accès nominatif, et une tentative d'ajout de capacité
cloisonnée à un modèle de rôle échoue.

Contexte projet : lire docs/02-domaine.md section 3 en entier (les quatre couches, les capacités, la
composition, le cloisonnement, les invariants), docs/03-api.md sections 1.9 et 2.5, et
docs/adr/015-l-interface-se-compose-a-partir-des-capacites.md et
docs/adr/012-le-cloisonnement-est-une-frontiere-de-compilation.md. Ne rien inventer hors de ces
fichiers.
```

---

# T2 — Le temps et la structure

L'année scolaire est techniquement le morceau le plus difficile d'un système d'information scolaire,
et celui qui est le plus souvent traité trop tard. La structure pédagogique s'y accroche.

**Cet epic pose une règle qui traverse tout le reste** : rien n'est global. Ni une classe, ni un
coefficient, ni un tarif, ni une affectation.

**Hors périmètre de l'epic** : les élèves, les notes, l'argent.

## T2a — L'année scolaire et sa bascule

**Risque** : élevé, **irréversible**. **Poids** : 55 % de l'epic.

```text
/speckit-specify Besoin : faire coexister deux années scolaires, parce que c'est le fonctionnement
normal et non un cas limite : on réinscrit pour septembre alors que le troisième trimestre n'est pas
terminé.

Livrer :
- l'année scolaire avec son état — préparation, active, clôturée, archivée — et ses transitions ;
- les périodes de l'année, dont le nombre et la nature viennent du pack de pays et non du code, avec
  leur propre clôture qui gèle les notes ;
- le calendrier : vacances, jours fériés, périodes d'examen, dates de conseil ;
- l'ouverture de l'année suivante en préparation PENDANT que la courante est active ;
- la duplication paramétrable de la structure — niveaux, matières, coefficients, tarifs — modifiable
  après duplication ;
- la clôture d'année, REFUSABLE, qui renvoie la liste précise de ce qui bloque : notes non saisies,
  bulletins non publiés, échéances ouvertes ;
- le pendant de vérification de la clôture : ce qui bloquerait, consultable AVANT de tenter la
  clôture ;
- l'archivage, en lecture seule intégrale, pour la durée légale de conservation — y compris après le
  départ de l'élève.

Contraintes non négociables :
- une seule année est active par établissement à un instant donné, et une seule peut être en
  préparation en même temps ;
- aucune période ne chevauche une autre dans la même année ;
- aucune écriture n'est acceptée sur une année clôturée ou archivée : la correction passe par une
  procédure explicite, tracée, produisant un document rectificatif — jamais par une écriture
  silencieuse ;
- TOUTE table pédagogique porte son identifiant d'année, non nul. C'est la provision la plus
  coûteuse à rattraper du modèle entier ;
- la clôture est atomique : elle passe entièrement ou pas du tout ;
- le refus de clôture dit ce qui manque et ce qu'on peut faire, jamais seulement qu'elle a échoué.

Hors périmètre : la constitution des classes de l'année suivante à partir des décisions de passage,
qui appartient à T7 ; l'affectation des rôles à une année, livrée par T1b.

Risque : élevé et IRRÉVERSIBLE. Une entité pédagogique sans année rend faux tout bulletin archivé.
Critère de fin : deux années coexistent, la duplication produit une structure modifiable, et une
tentative de clôture avec des notes manquantes échoue en les nommant.

Contexte projet : lire docs/02-domaine.md sections 0 (règle R4) et 4 en entier, et docs/03-api.md
section 2.6. Ne rien inventer hors de ces fichiers.
```

## T2b — La structure pédagogique

**Risque** : moyen. **Poids** : 45 % de l'epic.

```text
/speckit-specify Besoin : décrire l'organisation pédagogique d'une année sans confondre trois notions
qui se ressemblent et qui n'ont rien à voir : le niveau, la classe et le groupe.

Livrer :
- la hiérarchie cycle, niveau, série, classe, groupe, dont les trois premiers niveaux viennent du
  pack de pays. LE SEGMENT DU MVP EST LE PRIMAIRE : six niveaux du CP1 au CM2, ET AUCUNE SÉRIE. La
  série reste dans le modèle, nullable, parce que le secondaire la remplira ; le pack primaire ne la
  déclare pas ;
- la classe, rattachée à une salle, à un site et à un professeur principal — ce dernier étant un rôle
  attaché au COUPLE classe-année, pas à une personne globalement ;
- le groupe, qui porte les options, les langues vivantes, les travaux pratiques, le soutien et
  l'éducation physique. UN ÉLÈVE APPARTIENT À UNE CLASSE ET À N GROUPES ;
- les matières et les enseignements, un enseignement étant le croisement d'une matière, d'un niveau et
  éventuellement d'une série, PORTANT LE COEFFICIENT, le volume horaire, le statut obligatoire ou
  optionnel et le mode d'évaluation ;
- l'affectation des enseignants aux enseignements et aux classes ou groupes. AU PRIMAIRE, LE MAÎTRE
  EST POLYVALENT : la même personne porte autant d'affectations qu'elle enseigne de matières sur sa
  classe, et elle en est le professeur principal. La polyvalence est un CUMUL D'AFFECTATIONS, jamais
  un cas particulier du modèle ;
- les salles et leur capacité ;
- l'emploi du temps EN SAISIE MANUELLE : les séances, leurs créneaux, leurs salles.

Contraintes non négociables :
- LE COEFFICIENT EST PORTÉ PAR L'ENSEIGNEMENT, PAS PAR LA MATIÈRE. Le même français n'a pas le même
  coefficient au CP1 et au CM2, ni — quand le secondaire arrivera — en série A et en série C. Une
  matière qui porte un coefficient est une erreur de modèle, pas un raccourci ;
- LE DÉDOUBLEMENT SE MODÉLISE AU NIVEAU DU GROUPE, jamais de la classe. Une classe scindée en deux
  groupes pour les travaux pratiques a un emploi du temps et un appel corrects seulement à cette
  condition ; sinon les deux sont faux ;
- l'effectif maximal est un AVERTISSEMENT VISIBLE, pas un refus : une classe surchargée existe dans
  la réalité et doit pouvoir exister dans le système ;
- la structure d'une année ne se modifie plus après la première note saisie sur un enseignement, sauf
  procédure explicite ;
- aucun libellé de niveau, de série ou de cycle n'est écrit dans le code : ils viennent du pack.

Hors périmètre : la génération automatique d'emploi du temps, qui est un solveur et appartient à
l'après-MVP ; la constitution automatique des classes, idem.

Risque : moyen. Le coefficient mal placé se paie au premier bulletin.
Critère de fin : une classe de CM2 dédoublée en deux groupes de soutien a un appel juste sur chacun ;
le même enseignement porte deux coefficients sur deux niveaux ; et un maître titulaire porte huit
affectations sur sa classe sans qu'aucune ligne de code ne connaisse le mot « polyvalent ».

Contexte projet : lire docs/02-domaine.md section 5 en entier, et docs/03-api.md section 2.7. Ne rien
inventer hors de ces fichiers.
```

---

# T3 — Les personnes

Raisonner en « parents » ne suffit pas, et la réalité n'est pas modélisable a posteriori. C'est
l'epic où une simplification apparemment innocente — « un élève a un père et une mère » — rend
inexprimable le cas le plus fréquent d'Afrique de l'Ouest.

**Hors périmètre de l'epic** : l'argent, qui arrive en T8 ; les notes et les absences.

## T3a — Les personnes, les foyers et les liens de responsabilité

**Risque** : élevé. **Poids** : 50 % de l'epic.

```text
/speckit-specify Besoin : représenter qui est responsable d'un élève, sachant que la typologie réelle
est bien plus large que « père et mère », et qu'elle décide de qui reçoit quoi, de qui paie quoi et de
qui a le droit de venir chercher l'enfant.

Livrer :
- la personne, entité unique et source de vérité : une même personne peut être simultanément parente
  d'un élève, enseignante vacataire et membre du bureau de l'association de parents. UN SEUL
  ENREGISTREMENT, TROIS RATTACHEMENTS ;
- le foyer, regroupement d'adressage et de facturation, un élève pouvant relever de deux foyers en
  garde alternée ;
- le lien de responsabilité, qualifié par sa nature — dont LE TUTEUR DE FAIT, l'enfant confié à un
  parent en ville pour la scolarité, qui est extrêmement fréquent et n'est pas un cas limite —, par
  l'autorité parentale, par le rang de contact, par la quote-part financière et par le droit de
  récupérer l'enfant ;
- le destinataire de communication PAR RUBRIQUE : le père peut recevoir la facture et la mère les
  absences. Ce n'est pas une préférence, c'est le modèle ;
- le registre des personnes autorisées à récupérer un élève, avec photo et pièce d'identité,
  consultable par le personnel de sortie et IMPRIMABLE PAR CLASSE ;
- la détection automatique de la fratrie — deux élèves partageant un foyer ou un lien parental —, qui
  ne se déclare pas ;
- l'historique complet et NON MODIFIABLE des changements de responsabilité, horodaté avec son auteur.

Contraintes non négociables :
- un élève relève de un ou deux foyers ; au-delà, c'est une erreur de saisie et le modèle la refuse ;
- la somme des quotes-parts actives d'un élève vaut cent pour cent, ou la facturation sera refusée
  avec un message explicite. JAMAIS un arrondi silencieux ;
- au moins un lien actif porte le rang de contact numéro un : un élève sans contact d'urgence ne
  s'inscrit pas ;
- UN LIEN NE SE SUPPRIME JAMAIS : il se clôt avec sa date de fin, et le changement s'écrit dans
  l'historique. Décès, déchéance, changement de tuteur : ce sont des faits, pas des corrections ;
- le numéro de pièce d'identité n'apparaît JAMAIS dans une liste, seulement dans un détail, et sous
  capacité explicite.

Hors périmètre : l'élève lui-même et son inscription, livrés par T3b ; la facturation éclatée, livrée
par T8a — ici on porte la quote-part, on ne l'applique pas.

Risque : élevé. Le lien de responsabilité mal modélisé est une reprise de données, pas une migration.
Critère de fin : un enfant confié à sa tante a un tuteur de fait avec autorité parentale partagée ;
la mère reçoit les absences et le père la facture ; la liste imprimée des personnes autorisées sort
par classe avec les photos.

Contexte projet : lire docs/02-domaine.md section 2 en entier, et docs/03-api.md section 2.4. Ne rien
inventer hors de ces fichiers.
```

## T3b — L'élève et son inscription

**Risque** : moyen. **Poids** : 50 % de l'epic.

```text
/speckit-specify Besoin : suivre le cycle de vie administratif d'un élève, de la candidature au
départ, en disant TOUJOURS ce qui manque avant qu'on tente de valider.

Livrer :
- l'élève, avec son matricule unique par établissement et IMMUABLE, qui le suit sur toute sa scolarité
  y compris en changeant de cycle au sein du groupe ;
- l'inscription rattachée à une année et à une classe, avec son régime — externe, demi-pension,
  interne — et sa machine à états : candidature, dossier incomplet, dossier complet, validée, active,
  puis transférée, radiée ou terminée ; refusée ;
- le dossier de pièces avec contrôle de complétude, la liste des types de pièces venant du pack de
  pays ;
- le pendant de vérification de la validation : ce qui manque, consultable AVANT de tenter ;
- la dérogation permettant de valider malgré un dossier incomplet, avec MOTIF OBLIGATOIRE et auteur
  tracé ;
- la fiche élève UNIQUE, dont les blocs et les actions varient selon les capacités de la personne qui
  la consulte : l'éducateur y voit la discipline, l'économe le solde, l'enseignant les notes de ses
  seules matières, l'infirmier rien sauf accès nominatif. UNE FICHE, PLUSIEURS VUES ;
- les transferts — arrivée, départ, radiation — avec leur motif et leur certificat ;
- la carte scolaire imprimable avec code à barres bidimensionnel ;
- la réinscription dans l'année en préparation pendant que l'année courante est active.

Contraintes non négociables :
- l'inscription en année suivante pendant que la courante est active est le FONCTIONNEMENT NORMAL,
  pas un cas limite ;
- un élève ne peut pas être inscrit dans deux années actives ;
- une radiation ne supprime rien : le dossier reste consultable pour la durée légale de conservation ;
- le refus de validation nomme les pièces manquantes ET dit ce qu'on peut faire — déposer, ou
  demander une dérogation ;
- la fiche élève est UN écran, jamais quatre écrans concurrents par rôle. C'est la règle qui rend le
  produit tenable à mesure que les rôles se multiplient ;
- aucune donnée personnelle ne figure dans une liste sans capacité explicite : ni la date de naissance
  complète, ni le téléphone, ni la pièce d'identité.

Hors périmètre : le rattachement au circuit d'affectation de l'État, livré par T8c ; les frais
d'inscription, livrés par T8a.

Risque : moyen.
Critère de fin : une candidature incomplète dit exactement ce qui manque avant qu'on tente de la
valider, et la même fiche élève montre trois contenus différents à trois personas.

Contexte projet : lire docs/02-domaine.md section 6 en entier, docs/03-api.md sections 2.8 et 3
(règle 3, le pendant de vérification), et docs/design/ecrans/05_fiche-eleve-trois-vues.html. Ne rien
inventer hors de ces fichiers.
```

---

# T4 — La communication

Le point de départ n'est pas la notification : c'est qu'une part importante des responsables légaux
n'a **ni smartphone ni forfait data actif**. Et que le message court est simultanément le canal le
plus fiable et **le poste de coût majeur** du modèle économique.

Les deux faits sont vrais en même temps, et c'est ce qui rend la conception difficile.

**T4a est la neuvième tranche à construire, T4b la dix-huitième.** Le moteur précède l'appel ; les
circulaires attendent que l'argent tourne.

**Hors périmètre de l'epic** : le message court entrant par mot-clé, reporté après le MVP mais conçu
dès maintenant.

## T4a — Le moteur de messages, le routage et le budget

**Risque** : élevé. **Poids** : 65 % de l'epic.

```text
/speckit-specify Besoin : transformer un événement métier en un message qui atteint la bonne personne,
sur le bon canal, dans la bonne langue, sous budget et dans la fenêtre horaire — sachant que le
message court n'est pas un repli mais le canal de premier rang, et qu'il coûte de l'argent à chaque
envoi.

Livrer :
- le référentiel des types de message, chacun portant son domaine et sa criticité ;
- les modèles de message PAR CANAL ET PAR LANGUE, chacun RÉDIGÉ pour son canal — un message court
  n'est pas une notification tronquée ;
- la politique de routage par établissement : quel événement part sur quel canal, pour quel profil de
  destinataire, avec quelle fenêtre d'envoi ;
- le repli en cascade entre canaux, ordonné par la politique ;
- le budget de messages courts par établissement, avec plafond, consommation, seuil d'alerte, et
  VÉRIFICATION AVANT L'ENVOI ;
- le regroupement des notifications non urgentes en un récapitulatif périodique — un seul message
  hebdomadaire au lieu d'un message par événement ;
- la file d'envoi alimentée par les événements du journal, avec accusés de réception, gestion des
  numéros invalides et reprise ;
- le respect du destinataire déclaré par rubrique : une personne ne reçoit que ce dont elle est
  destinataire ;
- la mesure du coût unitaire par établissement et par période.

Contraintes non négociables :
- la longueur du modèle de message court est vérifiée À L'ENREGISTREMENT DU MODÈLE, pas à l'envoi.
  Découvrir à sept heures du matin qu'un modèle dépasse cent soixante caractères coûte deux messages
  par famille ;
- le message court UNITAIRE est réservé aux événements réellement critiques : absence non justifiée,
  convocation, échéance dépassée. Le reste passe par l'espace en ligne, la messagerie riche ou le
  papier ;
- les fenêtres d'envoi respectent les heures ouvrables et les jours de repos ;
- un envoi part du journal d'événements, jamais directement d'un gestionnaire de requête : une
  transaction qui échoue n'envoie rien, une transaction qui réussit envoie toujours ;
- le fournisseur reste derrière l'abstraction posée en T0a : cette tranche remplace la simulation, elle
  ne la contourne pas ;
- les clés fr et en de chaque modèle naissent ensemble ;
- l'avis de situation IMPRIMÉ existe dès cette tranche : il remplace un message court pour le besoin
  de situation complète, et il ne coûte rien.

Hors périmètre : le message court entrant par mot-clé, reporté après le MVP — mais le contrôle d'accès
par le numéro appelant et la réponse générique à un numéro inconnu sont décrits dans la spécification
pour que le report reste additif. Les circulaires et la messagerie, livrées par T4b.

Risque : élevé — c'est le poste de coût qui décide de la marge, et le canal qui décide de l'adoption.
Critère de fin : un événement d'absence produit un message court de moins de cent soixante caractères,
dans la fenêtre horaire, au destinataire déclaré de la rubrique, et l'envoi est refusé quand le budget
est épuisé.

Contexte projet : lire docs/02-domaine.md section 11 en entier, docs/03-api.md section 2.13,
docs/adr/013-le-sms-est-un-canal-de-premier-rang.md, et
docs/design/ecrans/09_console-de-communication-poste.html. Ne rien inventer hors de ces fichiers.
```

## T4b — Les circulaires et la messagerie journalisée

**Risque** : moyen. **Poids** : 35 % de l'epic.

```text
/speckit-specify Besoin : permettre à l'établissement de s'adresser à ses familles et à ses personnels,
et de tenir une conversation — sachant qu'une conversation entre un adulte et un mineur dans une
plateforme scolaire crée un risque que l'éditeur sera tenu de justifier.

Livrer :
- la circulaire avec son périmètre — établissement, site, cycle, niveau, classe — son auteur et sa
  date de publication ;
- l'estimation AVANT ENVOI : combien de destinataires, sur quels canaux, pour quel coût ;
- la messagerie, avec ses conversations rattachées éventuellement à un élève ;
- les rendez-vous entre responsable légal et enseignant, avec créneaux et confirmation ;
- l'agenda de l'établissement, alimenté par le calendrier de l'année.

Contraintes non négociables :
- TOUTE CONVERSATION EST JOURNALISÉE, NON SUPPRIMABLE, ET VISIBLE D'UN TIERS. Sans exception, sans
  réglage, sans mode privé. Il n'existe aucune route de suppression sur un message, et le refus est
  explicite et testé ;
- l'estimation avant envoi n'est pas un confort : une circulaire mal ciblée peut épuiser le budget
  mensuel de messages courts d'un établissement en une opération ;
- une circulaire respecte les mêmes fenêtres d'envoi et le même budget que tout autre message ;
- les capacités bornent le périmètre : un professeur principal ne diffuse pas à l'établissement.

Hors périmètre : la messagerie de groupe entre élèves, hors du produit.

Risque : moyen, mais le volet journalisation est à risque très élevé en réputation.
Critère de fin : une circulaire estime son coût avant d'être envoyée, et une tentative de suppression
d'un message est refusée explicitement.

Contexte projet : lire docs/02-domaine.md section 11, docs/03-api.md section 2.13, et
docs/02-domaine.md section 12 pour ce qui touche à la protection. Ne rien inventer hors de ces
fichiers.
```

---

# T5 — La classe au quotidien

**L'écran qui décide de l'adoption.** Il se conçoit pour un appareil d'entrée de gamme et une
connexion lente, et rien d'autre ne compte devant cette contrainte.

L'appel et l'absence restent **une seule tranche** : c'est le même écran, le même mode de
défaillance, et la même méthode de test. Les découper produirait deux points de validation pour un
seul risque.

## T5 — L'appel, l'absence et sa justification

**Risque** : élevé, ergonomique.

```text
/speckit-specify Besoin : permettre à une enseignante d'appeler une classe de quarante élèves en moins
de quarante-cinq secondes, debout, sur un téléphone d'entrée de gamme, avec un réseau qui peut tomber
à tout moment — et faire que la famille sache l'absence avant midi.

Livrer :
- la liste des appels du jour de la personne connectée, allégée au maximum : c'est sa route d'entrée
  dans le produit. AU PRIMAIRE, SEGMENT DU MVP, CE SONT DEUX DEMI-JOURNÉES ; au secondaire ce sera une
  séance par cours. La même route, la même page, la même grille ;
- la grille d'appel, un geste par élève, une page par appel : pas de navigation, pas de modale
  intermédiaire ;
- L'ENREGISTREMENT PAR PETITS LOTS AU FIL DE L'EAU, chaque lot portant sa clé d'idempotence et
  renvoyant l'état de chaque ligne ;
- l'état par ligne visible en permanence — enregistré, ou en attente — et le ruban d'état de saisie
  qui dit l'heure du dernier enregistrement, le nombre de saisies en attente et la qualité du lien ;
- la présence avec ses états : présent, absent, retard avec ses minutes, excusé ;
- l'absence comme INTERVALLE, agrégée à partir des appels, avec son état justifiée ou non justifiée ;
- l'événement d'absence non justifiée écrit DANS LA MÊME TRANSACTION que l'appel, qui déclenche le
  message court par la politique de routage ;
- le dépôt de justificatif par le responsable légal ou par la vie scolaire, et son traitement ;
- les incidents et les sanctions, DEUX ENTITÉS DISTINCTES : un incident peut n'entraîner aucune
  sanction, une sanction cite son incident quand il existe ;
- les autorisations de sortie et le contrôle de sortie avec vérification de la personne autorisée ;
- les statistiques d'assiduité par classe, niveau et période ;
- LA LISTE D'APPEL IMPRIMABLE À L'AVANCE, une classe par page, avec ses cases à cocher.

Contraintes non négociables :
- LE POIDS DE L'ÉCRAN D'APPEL EST DE CENT VINGT KILO-OCTETS TRANSFÉRÉS, premier affichage utile sous
  deux secondes en réseau lent. C'est un plafond, pas un objectif : le dépassement est un refus ;
- cible tactile de cinquante-deux pixels. Un appel raté parce que la case voisine a été cochée coûte
  un message envoyé à tort à une famille, et une confiance qui ne revient pas ;
- perdre le réseau à la dernière ligne ne coûte JAMAIS les précédentes ;
- le ruban informe, IL NE BLOQUE JAMAIS LA SAISIE ;
- un retard n'est pas une absence : il porte ses minutes et alimente ses propres statistiques ;
- l'absence est un intervalle, jamais une paire de dates ni un booléen par demi-journée — Y COMPRIS
  QUAND LE CAS NOMINAL EST LA DEMI-JOURNÉE. C'est exactement là que la provision se dégrade : le
  primaire appelle par demi-journée, le secondaire par cours, le supérieur par unité d'enseignement,
  et l'intervalle absorbe les trois. Un booléen matin/après-midi coûterait les deux autres ;
- la sortie d'un élève exige la vérification de la personne autorisée, et elle s'écrit. C'est un
  contrôle de sécurité physique ;
- le dossier disciplinaire en cours d'instruction est cloisonné.

Hors périmètre : le conseil de discipline, reporté après le MVP ; le contrôle d'assiduité pour les
boursiers, idem.

Risque : élevé et ERGONOMIQUE. C'est la tranche où le produit se gagne ou se perd.
Critère de fin : une classe de quarante est appelée en moins de quarante-cinq secondes ; on coupe le
réseau à la trente-huitième ligne et rien n'est perdu ; la famille reçoit le message court en moins de
dix minutes.

Contexte projet : lire docs/02-domaine.md section 8 en entier, docs/03-api.md section 2.10,
docs/05-design.md sections 4, 5.1 et 9.3, et
docs/design/ecrans/02_appel-de-seance-mobile.html. Ne rien inventer hors de ces fichiers.
```

---

# T6 — L'évaluation

**C'est la fonctionnalité qui fait acheter**, et l'epic le plus exposé du corpus. Une échelle sur
vingt écrite en dur, une règle d'arrondi implicite, un `match` sur le pays : chacune de ces trois
erreurs condamne l'extension anglophone à une réécriture du module d'évaluation, du bulletin, et de
tous les bulletins archivés.

Il se découpe en trois parce que le moteur, la saisie et le document ont trois natures de risque
distinctes : la justesse du calcul, l'ergonomie sous réseau instable, et la conformité du document.

## T6a — Le référentiel d'évaluation et son moteur

**Risque** : très élevé, **irréversible**. **Poids** : 40 % de l'epic.

```text
/speckit-specify Besoin : calculer des moyennes, des mentions et des rangs SANS QUE LA RÈGLE SOIT
ÉCRITE DANS LE CODE, parce que le modèle francophone sur vingt et le modèle anglophone en pourcentage
avec codes de mention sont irréconciliables si le calcul est codé en dur — et parce qu'un bulletin
réédité trois ans plus tard doit refléter le barème de l'époque.

Livrer :
- le référentiel d'évaluation, VERSIONNÉ par pays et par année, portant l'échelle et ses bornes ;
- la table de conversion d'une valeur vers une mention, avec ses bornes et son indicateur de crédit ;
- la formule de composition de la note périodique et de la note annuelle, sous forme d'ARBRE DE CALCUL
  DÉCLARATIF — jamais du code ;
- les règles d'arrondi, par objet, avec leur nombre de décimales et leur mode ;
- les règles de rang, d'ex æquo et de mention ;
- L'INTERPRÉTEUR qui évalue ces formules, sans entrée-sortie, testable sur un jeu de formules et de
  notes en mémoire ;
- la route de simulation qui rejoue une formule sur un jeu d'essai AVANT publication ;
- le gel d'un référentiel publié : on en crée une version, on ne le modifie pas ;
- le pack de pays ivoirien dans sa partie évaluation DU PRIMAIRE — l'échelle, la conversion en
  mention, la composition périodique et annuelle, les règles d'arrondi et de rang —, ET un pack
  fictif minimal — un cycle, un niveau, une échelle sur dix, deux périodes — qui sert de test
  permanent ;
- SI LE PACK DÉCLARE UNE ÉCHELLE D'ACQUISITION PAR COMPÉTENCE — quatre niveaux nommés plutôt qu'un
  nombre —, LE MOTEUR LA TRAITE COMME UNE ÉCHELLE DE PLUS. C'est le test que le référentiel est bien
  déclaratif : une échelle non numérique ne doit demander AUCUNE ligne de moteur.

Contraintes non négociables :
- AUCUNE BORNE D'ÉCHELLE EN DUR hors des tests. Ni vingt, ni cent ;
- AUCUN AIGUILLAGE SUR LE PAYS dans le moteur. La porte de vérification l'interdit mécaniquement ;
- toute valeur calculée porte la version du référentiel qui l'a produite, et est recalculable à
  l'identique ;
- les règles d'arrondi sont ÉCRITES ET VERSIONNÉES. Elles sont une source majeure de contestation, et
  une convention implicite du langage n'est pas défendable devant un parent ;
- une absence n'est pas un zéro : elle porte son indicateur avec une valeur nulle, et c'est LA FORMULE
  qui décide de son traitement, jamais le code de saisie ;
- toute note est un nombre décimal exact, jamais un flottant, jamais un entier ;
- LE TEST D'AGNOSTICITÉ EST PERMANENT : le pack fictif produit des moyennes, des mentions et des rangs
  justes, de bout en bout.

Hors périmètre : la saisie, livrée par T6b ; le document, livré par T6c ; LE SUIVI LONGITUDINAL DES
ACQUIS FONDAMENTAUX — l'acquis qui se conserve d'une période à l'autre et se valide une fois — qui
n'est PAS une échelle et n'entre pas au MVP.

Risque : TRÈS ÉLEVÉ ET IRRÉVERSIBLE. C'est la tranche la plus exposée du corpus.
Critère de fin : le pack fictif sur dix avec deux périodes produit des moyennes, des mentions et des
rangs justes ; une modification du référentiel publié est refusée ; un aiguillage sur le pays ajouté
volontairement dans le moteur fait échouer la vérification.

Contexte projet : lire docs/02-domaine.md sections 7.1 et 7.2, docs/03-api.md section 2.9,
docs/adr/010-le-referentiel-d-evaluation-est-une-donnee-versionnee.md,
docs/adr/014-la-localisation-passe-par-le-country-pack.md, et docs/01-stack.md section 7.2. Ne rien
inventer hors de ces fichiers.
```

## T6b — La saisie de notes

**Risque** : élevé, ergonomique. **Poids** : 25 % de l'epic.

```text
/speckit-specify Besoin : permettre à un enseignant de saisir quarante notes sur une tablette, avec un
réseau instable, sans jamais rien perdre — et sans que la validation du barème l'arrête au milieu.

Livrer :
- l'évaluation : devoir, composition, contrôle continu, avec son barème, son poids, sa date et son
  état ;
- la grille de saisie par classe ou par groupe, colonne d'élèves, clavier numérique ouvert seul,
  tabulation qui descend la colonne ;
- LE CHANGEMENT DE MATIÈRE SANS QUITTER L'ÉCRAN : au primaire, le même maître saisit les huit matières
  de sa classe. Le faire ressortir vers un menu à chaque matière coûte huit navigations par période ;
- L'ENREGISTREMENT PAR PETITS LOTS AU FIL DE L'EAU, même contrat que l'appel : une clé d'idempotence
  par lot, l'état de chaque ligne en retour, le ruban d'état de saisie ancré ;
- la saisie de l'absence à une évaluation, distincte d'une note nulle ;
- la dispense, distincte de l'absence ;
- le verrouillage des notes à la clôture de la période ;
- la procédure de correction d'une note verrouillée, tracée, avec son auteur et son motif ;
- les moyennes par élève et par période, calculées par le moteur de T6a, portant leur version de
  référentiel.

Contraintes non négociables :
- une valeur hors des bornes du référentiel est REFUSÉE, jamais écrêtée, et le refus dit les bornes ;
- envoyer à la fois un indicateur d'absence et une valeur est une erreur de conception côté client,
  refusée explicitement ;
- perdre le réseau à la trente-huitième note sur quarante ne coûte AUCUNE des trente-sept
  précédentes ;
- l'état de chaque ligne est visible : enregistré, ou en attente. Aucun état global ambigu ;
- le poids de l'écran de saisie tient sous deux cents kilo-octets ;
- aucune note n'est modifiable après verrouillage sans la procédure explicite.

Hors périmètre : les appréciations, livrées par T6c ; le bulletin, idem.

Risque : élevé et ergonomique.
Critère de fin : on coupe le réseau à la trente-huitième note sur quarante et rien n'est perdu ; une
note hors des bornes de l'échelle est refusée en nommant ces bornes ; et un maître enchaîne deux
matières de sa classe sans quitter la grille.

Contexte projet : lire docs/02-domaine.md sections 7.3, 7.4 et 7.5, docs/03-api.md section 2.9 (la
saisie par lot), et docs/design/ecrans/04_saisie-des-notes-tablette.html. Ne rien inventer hors de ces
fichiers.
```

## T6c — Le bulletin

**Risque** : élevé. **Poids** : 35 % de l'epic.

```text
/speckit-specify Besoin : produire le document qui fait acheter le produit — un bulletin conforme au
gabarit du pays, juste, réémettable à l'identique, et dont l'édition d'un trimestre prend moins d'une
journée au lieu d'une semaine.

Livrer :
- le calcul du bulletin sur une classe et une période, produisant moyennes par matière, moyenne
  générale, rang, mention et assiduité — et, SI LE PACK DÉCLARE UNE ÉCHELLE D'ACQUISITION, le niveau
  atteint par compétence, restitué par le même moteur et par le même gabarit ;
- l'appréciation par matière et l'appréciation générale, portant leur auteur ET LEUR ORIGINE — humaine
  ou proposée par assistance et validée par une personne nommée. AU PRIMAIRE, LE MÊME MAÎTRE LES REDIGE
  TOUTES : la saisie s'enchaîne matière après matière sans changer d'écran ;
- l'assistance à la rédaction des appréciations EN PROPOSITION VALIDÉE : elle propose, un humain nommé
  valide avant effet, la sortie est étiquetée comme telle, et le journal enregistre quelle capacité,
  quel modèle, quelles données, quelle sortie, quel validateur ;
- le rendu du bulletin en document imprimable PAR LE SERVEUR, au gabarit du pack de pays, portant son
  empreinte ;
- l'état du bulletin : en préparation, calculé, arrêté, publié, archivé ;
- la publication multicanale aux destinataires déclarés de la rubrique scolaire ;
- la réédition, qui produit un document IDENTIQUE à l'original.

Contraintes non négociables :
- le document est rendu PAR LE SERVEUR, jamais par le navigateur : la mise en page d'un bulletin ne
  peut pas dépendre du terminal de l'utilisateur ;
- un bulletin publié est immuable et porte son empreinte ;
- une réédition trois ans plus tard reflète le barème de l'époque, pas le barème courant ;
- l'assistance à la rédaction est DÉSACTIVABLE PAR UN RÉGLAGE SERVEUR, et non par l'arrêt d'un
  service : suspendue, le produit reste pleinement opérationnel, les appréciations se saisissent à la
  main, et l'affordance disparaît de l'écran au lieu d'être grisée. C'est un test ;
- l'assistance ne produit JAMAIS une note, ni un rang, ni une mention : ce sont des règles
  déterministes, et les faire passer par un modèle de langage transforme une opération vérifiable en
  une opération à auditer ;
- le contenu généré est évalué sur les stéréotypes de genre, d'origine et de milieu social avant mise
  en production ;
- le document imprimé est lisible en noir et blanc, aucune couleur ne porte d'information.

Hors périmètre : la décision de passage, livrée par T7 ; la publication conditionnée à la tenue du
conseil, qui est un paramètre livré ici mais dont l'effet arrive avec T7 ; le livret d'acquis
fondamentaux suivi d'une année sur l'autre, qui n'est pas un bulletin de période et attend le
segment primaire complet.

Risque : élevé. C'est le livrable qui décide de la vente.
Critère de fin : un bulletin est produit pour une classe entière, réédité trois ans plus tard à
l'identique, et le produit fonctionne avec le service d'inférence arrêté.

Contexte projet : lire docs/02-domaine.md sections 7.3 à 7.5 et 13, docs/03-api.md sections 1.10 et
2.9, docs/adr/011-six-capacites-ia-pas-trente-quatre-agents.md, et docs/05-design.md section 10. Ne
rien inventer hors de ces fichiers.
```

---

# T7 — Le conseil de classe et le passage

Le rituel central de l'année scolaire, et une entité à **valeur juridique** : la décision de passage.
Elle garde sa tranche avec le conseil, parce que l'un ne se teste pas sans l'autre.

## T7 — Le conseil de classe et la décision de passage

**Risque** : élevé.

```text
/speckit-specify Besoin : tenir le conseil sans que personne n'ait compilé le dossier à la main, et
produire une décision de fin d'année qui a une valeur juridique, une voie de recours et un
verrouillage. AU PRIMAIRE — LE SEGMENT DU MVP — L'INSTANCE EST LE CONSEIL DES MAÎTRES : mêmes tables,
même circuit, un libellé qui vient du pack. Le code `CONSEIL_CLASSE` n'est pas un libellé.

Livrer :
- la convocation du conseil : date, ordre du jour, participants, quorum. LA COMPOSITION VIENT DU PACK :
  au primaire, l'équipe des maîtres et la direction, SANS délégué élève ni délégué parent ; au
  secondaire, avec. Une liste de qualités écrite dans le code est une erreur de modèle ;
- LE DOSSIER PRÉPARÉ AUTOMATIQUEMENT : moyennes, rang, assiduité, incidents, appréciations par
  matière. Le conseil délibère, il ne compile pas ;
- la délibération par élève : appréciation générale, mention, sanction positive — tableau d'honneur,
  encouragements, avertissement de travail ou de conduite ;
- la décision de fin d'année, entité en soi : admis, admis sous condition, redoublement, réorientation
  vers une autre série, orientation vers l'enseignement technique, exclusion. LES ISSUES OUVERTES À UN
  NIVEAU VIENNENT DU PACK : au primaire, aucune série n'existe, donc ni réorientation ni orientation
  technique — les valeurs restent au modèle et ne sont pas proposées ;
- la notification aux familles, qui VERROUILLE la décision ;
- la voie de recours avec son délai, qui vient du pack de pays et non d'une constante ;
- le procès-verbal signé, immuable, portant son empreinte ;
- l'export des décisions de passage vers l'année en préparation, pour la constitution des classes.

Contraintes non négociables :
- le conseil de CLASSE ne se confond jamais avec le conseil de DISCIPLINE, qui relève de la vie
  scolaire ;
- une décision se verrouille après notification : avant, elle est modifiable ; après, elle ne l'est
  plus que par la voie de recours ;
- une réorientation exige sa série cible DÈS QUE LE PACK DÉCLARE DES SÉRIES AU NIVEAU VISÉ ; sans
  elle, la décision est refusée. Au primaire, ce refus ne se produit jamais, et le code qui le porte
  ne s'écrit pas différemment pour autant ;
- L'EXAMEN DE FIN DE CYCLE APPARTIENT AU MINISTÈRE. Le passage en sixième en dépend : le produit
  enregistre la décision et le résultat, il n'organise ni l'inscription ni l'épreuve ;
- le délai de recours est une donnée du pack, jamais une constante du code ;
- le procès-verbal est immuable et porte son empreinte ;
- L'ASSISTANCE NE PRONONCE JAMAIS UNE DÉCISION DE PASSAGE. Elle peut au mieux préparer un dossier.
  C'est un interdit absolu, pas un réglage.

Hors périmètre : la constitution automatique des classes de l'année suivante, qui est un problème
d'optimisation sous contraintes et appartient à l'après-MVP. Ici, les décisions sont exportées ; la
constitution reste manuelle.

Risque : élevé — la décision de passage a une valeur juridique et une voie de recours.
Critère de fin : le dossier du conseil est complet sans qu'on l'ait compilé ; une décision notifiée
n'est plus modifiable ; le conseil des maîtres du pack primaire se tient sans délégué et atteint son
quorum ; et le même code, avec un pack qui déclare des séries, refuse une réorientation sans série
cible.

Contexte projet : lire docs/02-domaine.md section 9 en entier, docs/03-api.md section 2.11, et
docs/design/ecrans/08_conseil-de-classe-poste.html. Ne rien inventer hors de ces fichiers.
```

---

# T8 — L'argent

**C'est la fonctionnalité qui fait payer.** Le modèle simple « les parents paient l'école » est faux
pour une part majeure des effectifs du privé ivoirien : l'État est un payeur, par le conventionnement
de l'établissement et — au secondaire — par l'affectation d'élèves, dont plus d'un tiers des effectifs
du premier cycle relèvent dans le privé.

> **Le MVP sert le primaire, où l'affectation d'élèves n'existe pas.** T8c garde donc son modèle
> entier et change de cas nominal : la subvention à l'établissement conventionné remplace l'élève
> affecté. Le motif est dans [ADR 018](adr/018-le-mvp-commence-par-le-primaire.md) — c'est le seul
> endroit du corpus où le changement de segment coûte quelque chose.

L'epic se découpe en trois parce que la facturation, l'encaissement et la créance sur l'État ont trois
natures de risque : la justesse du calcul, l'idempotence face à un tiers, et la conformité d'une pièce
qui déclenche un paiement public.

**Hors périmètre de l'epic** : la comptabilité générale certifiée, hors du métier ; la paie, reportée.

## T8a — La grille tarifaire et la facturation par foyer

**Risque** : élevé. **Poids** : 35 % de l'epic.

```text
/speckit-specify Besoin : facturer une famille, pas un élève — parce qu'une fratrie de trois enfants
répartis sur trois cycles reçoit UNE facture, avec une remise fratrie, et éventuellement deux payeurs
à soixante et quarante pour cent.

Livrer :
- la grille tarifaire VERSIONNÉE par année, par niveau et par régime, avec ses lignes de tarif :
  poste, montant, date d'exigibilité, caractère obligatoire ;
- la facture portée PAR LE FOYER, avec ses lignes par élève et par poste ;
- l'éclatement par quote-part : deux payeurs à soixante et quarante reçoivent chacun leur échéancier
  et leur solde, SUR LA MÊME FACTURE ;
- l'échéancier avec ses états : à venir, exigible, réglée, en retard ;
- les remises — fratrie, personnel, mérite, social — chacune portant SON MOTIF ET SON AUTEUR ;
- la génération de campagne de facturation sur un périmètre ;
- le solde du foyer : facturé, encaissé, restant dû, par payeur ;
- les relances multicanales, soumises au budget de messages et aux fenêtres d'envoi ;
- les bourses et les prises en charge par un employeur, avec leur convention et leur plafond.

Contraintes non négociables :
- TOUT MONTANT EST UN ENTIER D'UNITÉ MINEURE, avec l'exposant porté par la devise du pack. Jamais de
  flottant ;
- la facture est portée par le foyer, jamais par l'élève ;
- la somme des quotes-parts vaut cent pour cent, ou la facturation est refusée avec un message
  explicite ;
- aucune remise n'est anonyme : motif et auteur obligatoires ;
- la grille tarifaire est versionnée et figée après publication ;
- le client n'additionne rien : le serveur renvoie les montants déjà calculés.

Hors périmètre : l'encaissement, livré par T8b ; le financement public, livré par T8c.

Risque : élevé.
Critère de fin : une fratrie de trois élèves sur deux cycles produit une facture unique avec remise
fratrie, éclatée entre deux payeurs à soixante et quarante.

Contexte projet : lire docs/02-domaine.md sections 10.1, 10.2 et 10.5, docs/03-api.md section 2.12, et
docs/design/ecrans/07_fiche-foyer-econome.html. Ne rien inventer hors de ces fichiers.
```

## T8b — L'encaissement, la caisse et le reçu

**Risque** : très élevé. **Poids** : 40 % de l'epic.

```text
/speckit-specify Besoin : encaisser en argent mobile et en espèces sans jamais encaisser deux fois,
sans jamais perdre un paiement, et en produisant un reçu que personne ne peut contester — sachant que
les confirmations du fournisseur arrivent en retard, en double, ou jamais.

Livrer :
- l'encaissement en espèces, avec sa caisse et son reçu numéroté ;
- l'initiation d'un paiement en argent mobile depuis l'espace de la famille ;
- la réception des confirmations du fournisseur, STRICTEMENT IDEMPOTENTE, avec vérification de
  signature ;
- la machine à états explicite du paiement : initié, en attente, confirmé, échoué, expiré, remboursé ;
- le reçu NUMÉROTÉ SÉQUENTIEL PAR CAISSE, imprimable, portant son empreinte ;
- l'arrêté de caisse quotidien, avec théorique, compté, écart et explication de l'écart ;
- le pendant de vérification de l'arrêté : ce qui bloquerait, consultable avant de tenter ;
- LA RÉCONCILIATION QUOTIDIENNE AUTOMATIQUE entre le journal de la plateforme et le relevé du
  fournisseur ;
- le remboursement PAR ÉCRITURE INVERSE, avec sa propre référence.

Contraintes non négociables :
- il n'existe AUCUNE route de suppression sur un paiement. Le refus est explicite et testé ;
- l'idempotence porte sur l'initiation ET sur la confirmation entrante. Une confirmation reçue trois
  fois n'encaisse qu'une fois ;
- une séquence de reçus trouée est une ANOMALIE SIGNALÉE, pas une curiosité ;
- un arrêté avec écart non expliqué est refusé ;
- le fournisseur reste derrière l'abstraction posée en T0a : cette tranche remplace la simulation,
  elle ne la contourne pas. Changer de fournisseur ne doit toucher aucune ligne de logique métier ;
- la simulation doit savoir ne jamais confirmer : le paiement qui reste en attente indéfiniment est
  le cas nominal à concevoir, pas l'exception ;
- une part majoritaire des paiements reste en espèces : l'écran de caisse est aussi soigné que le
  parcours en ligne.

Hors périmètre : le partage de revenu sur l'encaissement, question ouverte de l'après-MVP ; la
comptabilité générale.

Risque : TRÈS ÉLEVÉ. C'est le poste où naissent les litiges.
Critère de fin : une confirmation reçue trois fois n'encaisse qu'une fois ; un paiement qui n'est
jamais confirmé expire proprement ; la caisse du jour tombe juste et l'écart non expliqué bloque
l'arrêté.

Contexte projet : lire docs/02-domaine.md sections 10.3 et 10.4, docs/03-api.md section 2.12, et
docs/adr/009-agregateur-de-paiement-derriere-une-interface.md. Ne rien inventer hors de ces fichiers.
```

## T8c — Le financement public et la créance sur l'État

**Risque** : élevé. **Poids** : 25 % de l'epic.

```text
/speckit-specify Besoin : modéliser le circuit de financement public, parce que pour un établissement
conventionné la trésorerie dépend de subventions versées avec retard, parfois d'une année sur l'autre,
et qu'aucun tableau de bord n'est honnête sans lui. LE CAS NOMINAL DU MVP EST LA SUBVENTION À
L'ÉTABLISSEMENT PRIMAIRE CONVENTIONNÉ ; l'affectation d'un élève par l'État, qui est un dispositif du
secondaire, est le MÊME modèle avec un fait générateur par élève — on le prévoit, on ne le construit
pas.

Livrer :
- le rattachement d'une inscription à une décision d'affectation de l'État et à sa cohorte, avec le
  montant pris en charge — la table existe et reste VIDE au primaire, où l'État finance l'effectif et
  non l'élève. Elle se remplit avec le segment secondaire, sans migration ;
- LA CRÉANCE PORTÉE PAR L'ÉTABLISSEMENT ET L'ANNÉE DE RATTACHEMENT, avec ses trois effectifs : c'est
  le cas nominal du MVP, et le modèle le portait déjà ;
- la SÉPARATION STRICTE entre ce que l'État couvre et ce qui est facturable à la famille — sujet
  sensible et contrôlé ;
- la créance sur l'État par année de rattachement : montant dû, ancienneté, encaissements partiels ;
- LA RÉCONCILIATION ENTRE TROIS NOMBRES DISTINCTS : effectif déclaré, effectif contrôlé, effectif
  payé ;
- l'attestation d'effectif, qui est LA PIÈCE QUI DÉCLENCHE LE PAIEMENT, avec ses échéances
  réglementaires venant du pack de pays ;
- l'état des arriérés par année, sortant en un clic ;
- l'intégration au tableau de bord de trésorerie : facturé, encaissé, ENCAISSABLE À COURT TERME.

Contraintes non négociables :
- le tableau de bord distingue trois montants, faute de quoi il est MENSONGER pour un établissement
  conventionné ;
- les échéances réglementaires viennent du pack, jamais du code ;
- l'effectif déclaré, l'effectif contrôlé et l'effectif payé sont trois nombres distincts, et leur
  réconciliation est une opération du modèle, pas un tableur ;
- la part État et la part famille ne se mélangent jamais sur une même ligne de facture.

Hors périmètre : l'interface avec la plateforme nationale d'affectation, qui appartient au ministère —
on s'y interface au mieux, on ne s'y substitue pas.

Risque : élevé. C'est l'argument de vente auprès des établissements conventionnés.
Critère de fin : l'état des arriérés par année de rattachement sort en un clic, et l'écart entre
effectif déclaré et effectif payé est visible et chiffré.

Contexte projet : lire docs/02-domaine.md sections 10.1, 10.2 et 10.5, docs/00-brief.md section 4
(contrainte 5), et docs/03-api.md section 2.12. Ne rien inventer hors de ces fichiers.
```

---

# T9 — La protection de l'enfance

C'est le domaine où une erreur de conception a les conséquences les plus graves, humaines comme
juridiques. **Module dédié et cloisonné — jamais une fonctionnalité annexe d'un autre service.**

**C'est un plancher, pas une option** : le produit ne se met pas en service sans lui. Il arrive en
dix-neuvième position parce qu'il exige des élèves, des personnels et des capacités — pas parce qu'il
est secondaire.

## T9 — Le registre de protection de l'enfance

**Risque** : très élevé.

```text
/speckit-specify Besoin : permettre à tout membre du personnel de signaler une situation, y compris de
façon confidentielle, et garantir que ce signalement suit un circuit humain nommé sans jamais être
lisible par quelqu'un qui n'y a pas droit — y compris par le chef d'établissement, y compris quand
c'est lui qui est concerné.

Livrer :
- le signalement, dont L'AUTEUR PEUT ÊTRE ABSENT : le signalement confidentiel existe, et c'est la
  raison d'être du registre ;
- le référent de protection de l'enfance désigné dans l'établissement, avec sa période ;
- le circuit de traitement : étapes nommées, acteurs, horodatages, délais réglementaires venant du
  pack de pays ;
- l'escalade vers la direction, puis vers les autorités compétentes, avec sa référence ;
- la traçabilité INTÉGRALE ET NON MODIFIABLE de chaque action ;
- la politique de conservation spécifique, DISTINCTE de celle du dossier scolaire ;
- le suivi psychosocial, cloisonné ;
- le dossier médical et le registre de passage à l'infirmerie, cloisonnés ;
- LA FICHE D'URGENCE ET LES ALLERGIES, NON CLOISONNÉES, accessibles au personnel encadrant et
  IMPRIMABLES PAR CLASSE ;
- le journal d'accès, écrit à chaque lecture Y COMPRIS EN CAS DE REFUS, avec alerte au responsable en
  cas d'accès anormal.

Contraintes non négociables :
- déposer un signalement N'EXIGE AUCUNE CAPACITÉ. Tout membre du personnel peut signaler ;
- aucun autre module du produit ne référence ce module. C'est une frontière de compilation, vérifiée
  mécaniquement — un module qui pourrait lire un signalement finirait par le lire ;
- les capacités de ce domaine ne sont PAS ajoutables à un modèle de rôle : elles s'attribuent
  nominativement, avec motif et date de fin ;
- un chef d'établissement n'a pas accès par défaut au contenu d'un signalement qui le concerne. C'est
  la raison d'être de la couche, et c'est son test ;
- la fiche d'urgence est délibérément hors du cloisonnement : un choc anaphylactique ne se traite pas
  en demandant une habilitation ;
- L'ASSISTANCE PEUT AU MIEUX ALERTER UNE PERSONNE NOMMÉE. Pas de qualification, pas de score de
  risque, pas de décision, pas de notification automatique aux familles. Interdit absolu ;
- le registre change de registre visuel : pas d'emoji, pas d'illustration, pas de couleur d'accent,
  pas de formule encourageante. Le texte est sobre, factuel, et NOMME LE CIRCUIT.

Hors périmètre : la vérification des antécédents du personnel au recrutement, qui appartient au module
de ressources humaines, reporté ; le climat scolaire anonymisé, reporté.

Risque : TRÈS ÉLEVÉ en réputation et en droit.
Critère de fin : un signalement confidentiel part sans auteur ; une tentative d'ajout de la capacité
de consultation à un modèle de rôle échoue ; le chef d'établissement concerné par un signalement ne le
lit pas ; la liste des fiches d'urgence sort par classe.

Contexte projet : lire docs/02-domaine.md section 12 en entier,
docs/adr/012-le-cloisonnement-est-une-frontiere-de-compilation.md, docs/03-api.md section 2.14,
docs/01-stack.md section 7.4, docs/05-design.md section 8.3, et
docs/design/ecrans/10_registre-protection-enfance-poste.html. Ne rien inventer hors de ces fichiers.
```

---

# T10 — La mise en service

**La migration n'est pas une étape du projet : c'est la première fonctionnalité vendue.** Les données
existantes sont dans Excel, sur papier, ou dans un logiciel abandonné. Un établissement de 800 élèves
doit être opérationnel en moins de deux semaines.

**Hors périmètre de l'epic** : le back-office éditeur complet, reporté ; la formation, qui est un
livrable humain.

## T10a — L'import et la reprise

**Risque** : élevé. **Poids** : 65 % de l'epic.

```text
/speckit-specify Besoin : reprendre les données d'un établissement telles qu'elles existent — un
tableur désordonné, des colonnes nommées à la main, des noms écrits de trois façons — et le rendre
opérationnel en moins de deux semaines, sans jamais écrire de données fausses.

Livrer :
- le dépôt d'un fichier tabulaire ;
- LA PROPOSITION AUTOMATIQUE DE CORRESPONDANCE DE COLONNES, tolérante au désordre et aux libellés
  approximatifs, corrigeable à la main ;
- LA SIMULATION OBLIGATOIRE avant exécution : ce qui serait créé, modifié, rejeté — SANS RIEN
  ÉCRIRE ;
- l'exécution, avec son rapport de lignes rejetées et de leurs motifs ;
- l'import de photos d'élèves en masse ;
- LA REPRISE DES SOLDES DE SCOLARITÉ au premier jour, avec contrôle d'équilibre ;
- L'ANNÉE DE TRANSITION : un établissement qui bascule en cours d'année, avec un historique partiel.
  Ce cas est PRÉVU, pas subi ;
- la détection et la fusion des doublons de personnes.

Contraintes non négociables :
- la simulation est obligatoire avant l'exécution. Une reprise de soldes qui se découvre fausse après
  écriture est le pire scénario de mise en service ;
- l'assistance à la correspondance de colonnes est DÉSACTIVABLE PAR RÉGLAGE SERVEUR : suspendue, la
  correspondance se fait à la main et l'import fonctionne ;
- un solde de reprise déséquilibré est refusé, en nommant l'écart ;
- une ligne rejetée dit pourquoi, en termes que le secrétariat comprend — jamais un code technique ;
- l'import respecte toutes les règles du modèle : quotes-parts à cent pour cent, contact de rang un,
  matricule unique. Un import n'est pas une porte dérobée dans les invariants.

Hors périmètre : la migration depuis un logiciel concurrent par connecteur dédié ; l'import des
historiques de notes des années antérieures, qui relève d'une reprise sur devis.

Risque : élevé. C'est ce qui décide si la vente se transforme en usage.
Critère de fin : un fichier de 800 élèves aux colonnes désordonnées est importé après simulation, avec
un rapport de rejets lisible par un secrétariat.

Contexte projet : lire docs/02-domaine.md sections 2, 6 et 13 (capacité C5), docs/03-api.md
section 2.15, et docs/00-brief.md section 4 (contrainte 7). Ne rien inventer hors de ces fichiers.
```

## T10b — Le pilotage et l'export

**Risque** : moyen. **Poids** : 35 % de l'epic.

```text
/speckit-specify Besoin : donner à la direction la vue d'ensemble qu'elle n'a pas aujourd'hui, et
garantir à l'établissement qu'il peut partir avec ses données — parce que c'est l'argument de vente
contre la peur de l'enfermement.

Livrer :
- le tableau de bord : effectifs, assiduité, réussite, trésorerie, créance sur l'État ;
- LA DISTINCTION ENTRE FACTURÉ, ENCAISSÉ ET ENCAISSABLE À COURT TERME ;
- les indicateurs d'alerte : impayés au-delà du seuil, absentéisme, budget de messages bas ;
- le journal d'audit consultable, en lecture seule ;
- le journal des sorties d'assistance : capacité, modèle, données, sortie, validateur ;
- L'EXPORT COMPLET DES DONNÉES DE L'ÉTABLISSEMENT, dans un format ouvert, DISPONIBLE À TOUT MOMENT ;
- le registre des traitements de données personnelles, exportable ;
- les documents administratifs générés au gabarit du pack : certificat de scolarité, attestation,
  convocation.

Contraintes non négociables :
- le tableau de bord se compose lui aussi à partir des capacités : une personne ne voit que les
  indicateurs de ses domaines ;
- aucun indicateur cloisonné n'apparaît sur un tableau de bord général. Le nombre de signalements en
  cours n'est PAS un indicateur de direction ;
- l'export complet n'est pas une fonction de confort : c'est un engagement commercial et une exigence
  de portabilité des données ;
- le journal d'audit est en insertion seule ;
- les indicateurs sont utilisables sur téléphone : la direction valide et consulte depuis son mobile.

Hors périmètre : la console éditeur complète — provisionnement, abonnements, supervision — reportée ;
les remontées statistiques à la tutelle, reportées avec le pack de pays complet.

Risque : moyen.
Critère de fin : le tableau de bord distingue les trois montants ; l'export complet se produit et se
relit ; aucun indicateur cloisonné n'y figure.

Contexte projet : lire docs/02-domaine.md sections 10.5, 12 et 14, docs/03-api.md section 2.16,
docs/01-stack.md sections 4 et 5.2, et
docs/design/ecrans/12_tableau-de-bord-direction-poste.html. Ne rien inventer hors de ces fichiers.
```

---

## Après la vingt-et-unième tranche

Le pilote édite ses bulletins et encaisse sa scolarité dans Nelo. **C'est à ce moment-là, et pas
avant, que [06-apres-mvp.md](06-apres-mvp.md) s'ouvre.**

La première extension à regarder n'est pas un segment ni un pays : c'est le **message court entrant
par mot-clé**. C'est la seule chose reportée du MVP dont le report coûte de l'argent tous les mois.

---

**Suite** → [05-design.md](05-design.md) pour la revue visuelle, [progress.md](progress.md) pour
l'état courant.
