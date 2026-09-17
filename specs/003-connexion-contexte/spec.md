# Feature Specification: Se connecter et savoir où l'on est (T1a)

**Feature Branch**: `003-connexion-contexte`

**Created**: 2026-09-17

**Status**: Draft

**Input**: User description: le prompt **T1a, Se connecter et savoir où l'on est** de
[docs/04-roadmap.md](../../docs/04-roadmap.md#t1a--se-connecter-et-savoir-où-lon-est), collé tel
quel. Il tient en une phrase : permettre à une personne de s'identifier **par son numéro de
téléphone** et d'arriver là où elle travaille, sur un poste probablement partagé, sans qu'aucun
compte d'un établissement ne voie jamais une donnée d'un autre. C'est **la première frontière de
sécurité du produit** ; ici, un compte authentifié n'a encore le droit de rien.

**Sources qui font foi** : [docs/02-domaine.md](../../docs/02-domaine.md) § 0 (R6, R9, R11, R12,
R13), § 3.1 et § 3.2 (les quatre couches, le compte), § 3.6 (invariants : suspension immédiate,
compte individuel côté personnel), § 16 et § 17 ; [docs/03-api.md](../../docs/03-api.md) § 1.2
(en-têtes et leur table de refus), § 1.3 (idempotence), § 1.6 à § 1.8 (enveloppe, préfixes, codes
HTTP), **§ 1.9** (le contexte), § 2.1 (authentification), § 2.2 (moi), § 2.5 (la suspension) et
§ 3 (règles opposables) ; [docs/01-stack.md](../../docs/01-stack.md) § 5 et **§ 5.1** (session sur
poste partagé), § 7 et § 8.3 ; [ADR 005](../../docs/adr/005-isolation-des-tenants-par-rls-et-double-barriere.md)
(double barrière), [ADR 007](../../docs/adr/007-valkey-pour-l-ephemere.md) (sessions et liste de
révocation sont éphémères), [ADR 013](../../docs/adr/013-le-sms-est-un-canal-de-premier-rang.md)
(le message court est rédigé pour le message court) ; la maquette **A1**
`docs/design/ecrans/01_connexion-mobile.html` ; et la
[constitution](../../.specify/memory/constitution.md) v1.0.0, principes I, II, IV, VII, IX, X,
XII, XIII et XV.

## User Scenarios & Testing *(mandatory)*

**Acteurs.**

- **Mme Traoré, maîtresse titulaire d'un CM1 et mère de trois élèves.** Un seul téléphone d'entrée
  de gamme, réseau 2G en classe, l'appel plusieurs fois par jour. Elle ne doit **pas** recevoir un
  message court à chaque ouverture, et elle n'a qu'un seul espace, jamais deux.
- **Le responsable légal sans adresse électronique**, au forfait compté, qui reçoit un lien
  d'activation par message court et n'a jamais vu l'application.
- **Deux parents qui partagent un téléphone.** C'est le cas normal, pas un cas limite.
- **La secrétaire sur le poste partagé du secrétariat**, qui crée les comptes, renvoie un lien,
  change un numéro quand une carte SIM est perdue, et quitte le poste sans toujours fermer sa
  session.
- **La personne qui administre l'établissement**, celle que l'écran « aucun domaine » nomme, et
  qui suspend un compte le jour d'un départ.
- **La commande de vérification**, qui doit prouver qu'un compte d'un établissement ne voit rien
  d'un autre, qu'une révocation coupe à la requête suivante, et qu'aucun jeton ne vit dans le
  stockage du navigateur.

Les user stories sont ordonnées par ce qu'elles débloquent : les trois premières sont les deux
critères de fin de la roadmap (ouvrir par code à usage unique, puis par code personnel ; aucune
fuite entre tenants) ; les trois suivantes rendent la session utile et sûre (le contexte, la
révocation, l'activation) ; les deux dernières traitent ce que la réalité du terrain impose (le
numéro change, le numéro se partage).

---

### User Story 1 - Ouvrir sa session par un code reçu par message court (Priority: P1)

Mme Traoré ouvre l'application sur son téléphone. L'écran lui demande **son numéro de téléphone**,
rien d'autre : ni adresse électronique, ni mot de passe. Elle reçoit un code à six chiffres par
message court, le saisit, et arrive dans son espace. Si le message tarde, l'écran l'a prévenue avant
qu'elle s'inquiète : le code reste valable dix minutes, elle peut fermer l'application. **Que son
numéro soit connu ou non, la demande de code répond exactement de la même façon** ; le code ne
part que si un compte porte ce numéro.

**Why this priority**: c'est la porte d'entrée de tout le produit et le premier critère de fin de
la roadmap. Sans elle, aucune autre tranche n'a de personne connectée.

**Independent Test**: sur un tenant de test portant un compte actif, demander un code pour ce
numéro et pour un numéro que personne ne porte, comparer les deux réponses ; lire le code sur la
passerelle simulée, le saisir, constater la session ; rejouer avec un code faux cinq fois, puis
avec un code expiré. Aucune autre story n'est nécessaire.

**Acceptance Scenarios**:

1. **Given** un compte actif dont l'identifiant est un numéro donné, **When** la personne demande
   un code pour ce numéro, **Then** la réponse est un accusé sans contenu, **et** un message court
   portant un code à six chiffres part vers ce numéro **hors du chemin de la réponse**, par
   l'événement outbox écrit dans la même transaction.
2. **Given** un numéro bien formé qu'aucun compte ne porte, ou qu'un compte suspendu porte,
   **When** on demande un code, **Then** la réponse est **identique** en statut, en corps et en
   en-têtes à celle du scénario 1, aucun message ne part, et le code d'erreur
   `AUT_NUMERO_INCONNU` n'est **jamais** renvoyé sur cette route.
3. **Given** un code envoyé il y a moins de dix minutes, **When** la personne le saisit, **Then**
   une session s'ouvre : un jeton d'accès court dans la réponse, un jeton de rafraîchissement dans
   un cookie non lisible par script, et le code est détruit.
4. **Given** un code envoyé il y a plus de dix minutes, **When** la personne le saisit, **Then**
   le refus est `AUT_OTP_EXPIRE` et l'écran propose son versant positif : recevoir un nouveau
   code.
5. **Given** un code valide, **When** cinq saisies fausses se succèdent, **Then** le refus est
   `AUT_OTP_TENTATIVES_EPUISEES`, le code est détruit, et seule une nouvelle demande permet de
   continuer.
6. **Given** une demande de code faite il y a moins de soixante secondes pour le même numéro,
   **When** une seconde demande arrive, **Then** elle est refusée par une limitation de débit avec
   son délai de reprise, aucun second message ne part ; **et** l'écran affichait déjà le compte à
   rebours avant que la personne n'appuie.
7. **Given** cinq demandes en une heure pour le même numéro, **When** une sixième arrive,
   **Then** elle est refusée par la même limitation ; le compte n'est **pas** suspendu, et une
   personne qui n'a pas reçu ses messages n'est pas punie pour cela.
8. **Given** une demande pour un même numéro rejouée avec la même clé de requête, **When** elle
   arrive, **Then** la réponse mémorisée est renvoyée et **aucun second message** ne part.
9. **Given** un numéro qui n'a pas la forme d'un numéro international, **When** on demande un
   code, **Then** le refus est `422 AUT_NUMERO_INVALIDE`, qui ne dit rien de l'existence d'un
   compte ; l'écran l'avait annoncé pendant la saisie.
10. **Given** l'écran d'erreur « numéro inconnu du système » de la maquette A1, **When** on le
    confronte au contrat, **Then** **le contrat gagne** : aucun écran ne dit qu'un numéro est
    inconnu. L'écran de saisie du code porte à la place, sous « Le SMS n'est pas encore arrivé ? »,
    l'orientation vers le secrétariat de l'établissement, **sans numéro** : avant la session le
    tenant n'est pas connu (E-01) : *le numéro que votre établissement a enregistré pour vous est
    peut-être un autre ; demandez au secrétariat de le vérifier*. L'écart est documenté.

---

### User Story 2 - Aucun compte d'un établissement ne voit une donnée d'un autre, et l'établissement comme l'année sont choisis, jamais devinés (Priority: P1)

La session remplace la résolution provisoire du tenant que le socle T0a avait posée. Chaque requête
porte l'établissement actif et, sur une route pédagogique, l'année de travail, dans deux en-têtes
que le serveur vérifie **contre les rattachements du compte**. Un établissement auquel le compte
n'est pas rattaché répond « interdit », qu'il appartienne au même tenant ou à un autre : la
réponse ne permet pas de savoir s'il existe. Une année manquante sur une route pédagogique est une
erreur, **jamais** un repli sur l'année active.

**Why this priority**: c'est le second critère de fin de la roadmap et la raison d'être de la
double barrière. Un repli implicite sur l'année active écrit une note dans la mauvaise année ; une
réponse « introuvable » sur un établissement tiers publie son existence.

**Independent Test**: deux tenants, deux comptes, un établissement chacun, plus un second
établissement dans le premier tenant auquel le compte n'est pas rattaché. Depuis chaque session,
appeler la seule lecture de données du socle (les paramètres) avec les quatre en-têtes dans tous
leurs états. Dépend de la seule story 1 pour obtenir une session.

**Acceptance Scenarios**:

1. **Given** n'importe quelle route hors la sonde et l'authentification, **When** l'en-tête
   d'autorisation manque, est illisible, expiré ou révoqué, **Then** la réponse est `401` avec
   `AUT_JETON_MANQUANT`, `AUT_JETON_INVALIDE` ou `AUT_SESSION_REVOQUEE`, avant toute validation de
   schéma, sur **toute** route protégée.
2. **Given** une session du compte d'un tenant A, **When** l'en-tête d'établissement désigne un
   établissement d'un tenant B, **Then** la réponse est `403 TEN_ETABLISSEMENT_NON_AUTORISE`,
   jamais `404`.
3. **Given** un tenant A portant deux établissements A1 et A2 et un compte rattaché à A1 seul,
   **When** l'en-tête désigne A2, **Then** la réponse est `403 TEN_ETABLISSEMENT_NON_AUTORISE`,
   **indistinguable** de celle du scénario 2.
4. **Given** une route portant des données d'établissement, **When** l'en-tête d'établissement
   manque ou n'est pas un identifiant, **Then** la réponse est `400 TEN_ETABLISSEMENT_REQUIS`.
5. **Given** une route déclarée pédagogique, **When** l'en-tête d'année manque, **Then** la
   réponse est `400 ANN_ANNEE_REQUISE`, **y compris** quand le compte n'a qu'une seule année
   possible : aucun repli, même évident.
6. **Given** l'en-tête d'année présent, **When** il désigne une année d'un autre établissement ou
   d'un autre tenant, ou une année inexistante, **Then** la réponse est
   `404 TEN_RESSOURCE_INTROUVABLE` ; quand il n'est pas un identifiant, `400 ANN_ANNEE_REQUISE`.
7. **Given** une session et des en-têtes valides, **When** une transaction s'ouvre, **Then** la
   variable de tenant est posée **depuis le compte de la session**, dans la transaction, et le
   mécanisme provisoire de T0a n'existe plus dans le code ; le test qui le prouvait est remplacé
   par celui-ci.
8. **Given** deux tenants portant chacun un compte, des rattachements et des sessions, **When**
   chacun lit ses paramètres et son contexte, **Then** aucun ne voit une ligne de l'autre, et le
   test d'isolation entre deux tenants couvre chaque table neuve de cette tranche.
9. **Given** une route pédagogique avec en-tête d'année valide mais en-tête d'établissement
   désignant un autre établissement que celui de l'année, **When** elle est appelée, **Then** la
   réponse est `404 TEN_RESSOURCE_INTROUVABLE` : l'année n'est pas dans le périmètre désigné.

---

### User Story 3 - Le code personnel remplace le message court sur un appareil connu (Priority: P1)

Après sa première ouverture par code reçu, l'écran propose à Mme Traoré de choisir **un code
personnel à quatre chiffres**, en disant pourquoi avant de le demander : il remplacera le message
court à chaque ouverture sur cet appareil. Elle peut remettre ce choix à plus tard. Dès lors, sur
ce téléphone, elle ouvre son espace en tapant quatre chiffres, sans attendre aucun message. Sur un
appareil que son compte ne connaît pas, le code personnel n'est pas proposé.

**Why this priority**: « une enseignante qui fait l'appel six fois par jour ne reçoit pas six
messages » est un critère de fin de la roadmap et un poste de coût du modèle économique.

**Independent Test**: ouvrir par code reçu sur un navigateur, définir un code personnel, fermer la
session, rouvrir par code personnel et constater qu'aucun message n'est parti ; recommencer sur un
second navigateur et constater que le code personnel n'y est pas proposé. Dépend de la story 1.

**Acceptance Scenarios**:

1. **Given** une session qui vient de s'ouvrir par code reçu sur un appareil, **When** l'étape
   du code personnel s'affiche, **Then** elle dit à quoi il sert **avant** de le demander, le
   demande deux fois, et propose « Plus tard : me connecter par message court » ; un refus de
   format (autre chose que quatre chiffres) est annoncé pendant la saisie.
2. **Given** un code personnel défini et un appareil connu du compte, **When** la personne ouvre
   l'application, **Then** l'écran propose **son nom** et la saisie de quatre chiffres, sans jamais
   afficher son numéro ; la session s'ouvre et **aucun message ne part**.
3. **Given** un appareil que le compte ne connaît pas, ou dont la connaissance a expiré, **When**
   la personne ouvre l'application, **Then** le code personnel n'est pas proposé ; le parcours par
   message court l'est.
4. **Given** un appareil connu, **When** cinq codes personnels faux se succèdent, **Then** le
   refus est `AUT_PIN_TENTATIVES_EPUISEES`, le code personnel est verrouillé sur ce compte jusqu'à
   une ouverture par message court, et l'écran le dit avec son versant positif : recevoir un code.
5. **Given** un code personnel oublié, **When** la personne ouvre par message court, **Then** elle
   peut en définir un nouveau, qui remplace l'ancien.
6. **Given** un code personnel déjà défini, **When** la personne veut le changer depuis une
   session, **Then** le code courant est exigé ; une session ouverte par message court dans les
   dix dernières minutes en dispense, et c'est le seul cas.
7. **Given** un poste partagé sur lequel trois comptes sont connus, **When** quelqu'un ouvre
   l'application, **Then** les trois noms sont proposés, aucun numéro n'est visible, et chacun
   n'ouvre qu'avec son propre code personnel.
8. **Given** un compte suspendu, connu d'un appareil, **When** un code personnel est saisi,
   **Then** le refus est `AUT_COMPTE_SUSPENDU` et l'appareil oublie ce compte.
9. **Given** un code personnel, **When** une route quelconque répond, **Then** le code personnel
   n'apparaît **jamais** dans une réponse : on répond « défini » ou « absent », conformément à la
   règle 4 de [03-api.md § 3](../../docs/03-api.md).
10. **Given** la maquette A1 qui propose « Ouvrir avec l'empreinte digitale », **When** on la
    confronte au domaine, **Then** **le domaine gagne** : l'authentification est « téléphone et
    code reçu, code personnel pour les usages fréquents » ; aucune biométrie n'est livrée ni
    proposée, l'écart est documenté.

---

### User Story 4 - Le contexte compose l'interface, et la personne choisit où elle travaille (Priority: P2)

La coquille du socle T0b lit désormais **le contexte réel** au lieu d'un contexte de
démonstration, sans qu'aucun écran change. Il porte le compte, les établissements où la personne
est rattachée avec chacun son administrateur, les années de travail possibles, le pack de pays, les
paramètres effectifs. Une personne rattachée à deux établissements choisit le sien ; une personne
qui a deux années possibles choisit la sienne ; **une personne sans aucune capacité voit un message
qui nomme qui peut lui ouvrir ses domaines**, jamais une page vide.

**Why this priority**: c'est ce qui fait qu'une action non autorisée est absente et non grisée, et
le point de branchement que T0b a laissé. Sans lui, la session ouvre sur rien.

**Independent Test**: depuis une session, lire le contexte avec l'en-tête d'établissement et
comparer sa forme au contrat ; lancer la coquille sur cette source et constater l'écran « aucun
domaine » nommant l'administrateur ; rattacher le compte à un second établissement et constater le
choix. Dépend des stories 1 et 2.

**Acceptance Scenarios**:

1. **Given** une session et un en-tête d'établissement valide, **When** la personne demande son
   contexte, **Then** il porte exactement la forme de [03-api.md § 1.9](../../docs/03-api.md) :
   `compte` (identifiant, nom, prénoms, langue), `etablissements` (ceux où le compte est rattaché,
   chacun avec ses sites, ses cycles actifs, ses modules actifs et son `administrateur`),
   `etablissement_actif` égal à l'en-tête, `annees` (celles de l'établissement actif auxquelles le
   compte est rattaché, chacune avec libellé et état), `annee_active` (celle en état actif, ou
   absente s'il n'y en a pas), `capacites` et `acces_nominatifs` **vides** jusqu'à T1b,
   `country_pack`, `parametres_effectifs` et `alertes`.
2. **Given** la coquille de T0b, **When** sa source de contexte devient la requête réelle,
   **Then** aucun composant ni aucune page de la coquille ne change ; un compte sans capacité
   voit l'écran « aucun domaine » avec le nom, les prénoms et le téléphone de l'administrateur.
3. **Given** un compte rattaché à un seul établissement, **When** la session s'ouvre, **Then** la
   personne arrive directement dans son espace ; **Given** un compte rattaché à deux
   établissements, **Then** l'application lui demande lequel, ou reprend celui choisi la dernière
   fois **sur cet appareil**, et changer d'établissement relit le contexte.
4. **Given** un établissement portant une année active et une année en préparation auxquelles le
   compte est rattaché, **When** la personne change d'année depuis la coquille, **Then**
   l'en-tête d'année change pour toutes les requêtes suivantes et le contexte est relu ; le choix
   vit sur l'appareil, **jamais** comme un défaut côté serveur sur lequel une route pourrait se
   replier.
5. **Given** un établissement qui a désigné son administrateur, **When** le contexte est composé,
   **Then** `administrateur` porte le nom, les prénoms et le téléphone de cette personne ;
   **Given** aucune désignation, ou un administrateur désigné dont le compte est suspendu,
   **Then** `administrateur` porte le nom de l'établissement et son téléphone, avec des prénoms
   vides, et **jamais** un champ absent.
6. **Given** un tenant qui n'a jamais eu de session, **When** le contexte est demandé, **Then**
   le pack de pays y figure avec ses langues, sa devise et son vocabulaire, lus depuis les
   données du tenant et non depuis une constante.
7. **Given** l'écran de connexion, avant toute session, **When** il s'affiche, **Then** sa langue
   est celle choisie sur l'appareil (`fr` ou `en`, comme la maquette A1) ; après ouverture, la
   langue de l'interface est celle du compte.

---

### User Story 5 - La révocation est immédiate, la session se ferme, et le jeton tourne (Priority: P2)

Un membre du personnel quitte l'établissement ; son compte est suspendu le jour même, et **sa
requête suivante est refusée**, même si son jeton d'accès n'a pas expiré. Sur un poste partagé, la
secrétaire ferme sa session d'un geste visible dans l'en-tête ; si elle oublie, la session s'éteint
d'elle-même au bout de la durée que le tenant a fixée. Le jeton de rafraîchissement tourne à chaque
usage, et un jeton déjà tourné qu'on représente signale un vol : toute la session tombe.

**Why this priority**: « le départ d'un membre du personnel coupe l'accès le jour même » est un
invariant du domaine, et les postes partagés sont la règle dans les établissements.

**Independent Test**: ouvrir une session, suspendre le compte par la route de suspension, rejouer
la requête précédente avec le même jeton ; ouvrir une session, rafraîchir, représenter l'ancien
jeton de rafraîchissement ; inspecter le stockage du navigateur après connexion. Dépend de la
story 1.

**Acceptance Scenarios**:

1. **Given** une session ouverte avec un jeton d'accès valable encore cinquante minutes, **When**
   le compte est suspendu, **Then** la requête suivante portant ce jeton répond
   `401 AUT_SESSION_REVOQUEE`, le rafraîchissement est refusé, et le code personnel répond
   `AUT_COMPTE_SUSPENDU` ; **aucune** requête n'est servie entre la suspension et le refus.
2. **Given** la route de suspension de [03-api.md § 2.5](../../docs/03-api.md), **When** elle
   est appelée, **Then** elle exige la capacité `habilitations.compte.suspendre` par le point
   d'insertion que T0a a laissé et que T1b remplit, écrit un événement outbox, révoque toutes les
   sessions du compte et fait oublier le compte à tous ses appareils connus.
3. **Given** une session, **When** la personne la ferme, **Then** le jeton d'accès et le jeton de
   rafraîchissement sont révoqués sur-le-champ, le cookie est effacé, et l'appareil **reste
   connu** : la prochaine ouverture se fait par code personnel.
4. **Given** un jeton de rafraîchissement, **When** il est utilisé, **Then** un nouveau jeton le
   remplace dans le cookie et l'ancien devient invalide ; **When** l'ancien est représenté,
   **Then** toute la session est révoquée, y compris le jeton neuf, et un événement le dit.
5. **Given** un jeton d'accès de soixante minutes, **When** il expire pendant l'usage, **Then**
   l'application le renouvelle sans que la personne le voie ; **When** la session dépasse
   `securite.duree_session_minutes`, **Then** le renouvellement est refusé et la personne rouvre
   par code personnel ou par message court.
6. **Given** une session ouverte dans un navigateur, **When** on inspecte le stockage local, le
   stockage de session et les cookies lisibles par script, **Then** aucun jeton n'y figure ; le
   cookie de rafraîchissement est non lisible par script, réservé au transport sécurisé, borné à
   l'origine et au chemin de rafraîchissement.
7. **Given** le magasin éphémère remis à zéro, **When** les personnes reviennent, **Then** toutes
   doivent rouvrir une session, aucune n'en garde une, et un compte suspendu **reste** suspendu :
   la suspension est une donnée durable, la liste de révocation ne l'est pas.

---

### User Story 6 - Activer son compte depuis un lien à usage unique (Priority: P2)

Le secrétariat crée le compte d'un responsable légal à partir de son numéro. Celui-ci reçoit un
message court, rédigé pour le message court, avec un lien. Il l'ouvre : son compte s'active, sa
session s'ouvre, et l'application lui propose un code personnel. Le lien ne sert qu'une fois et
expire ; s'il l'a perdu, il peut aussi entrer son numéro et recevoir un code, ce qui active le
compte tout autant.

**Why this priority**: c'est ainsi que les familles entrent dans le produit, et ce qui rend la
story 1 utilisable par quelqu'un qui n'a jamais vu l'application.

**Independent Test**: créer un compte par la route de création, lire le lien sur la passerelle
simulée, l'ouvrir, constater l'activation et la session ; le rouvrir ; renvoyer un lien ; ouvrir
par code reçu un compte encore invité. Dépend de la story 1.

**Acceptance Scenarios**:

1. **Given** une personne connue du tenant et un numéro, **When** la secrétaire crée son compte,
   **Then** le compte naît en état `invite`, un message court portant un lien à usage unique part
   par l'outbox, sous 160 caractères, avec le nom de l'établissement, sans abréviation ; et la
   réponse dit « invitation envoyée le … », **jamais** le lien.
2. **Given** le lien reçu, **When** la personne l'ouvre dans les `securite.invitation_validite_jours`,
   **Then** le compte passe en état `actif`, une session s'ouvre, l'appareil devient connu et
   l'étape du code personnel s'affiche.
3. **Given** un lien déjà consommé, ou expiré, ou remplacé, **When** on l'ouvre, **Then** le refus
   est `AUT_INVITATION_INVALIDE` et l'écran dit le versant positif : entrer son numéro pour
   recevoir un code, ou demander un nouveau lien au secrétariat.
4. **Given** un compte en état `invite`, **When** la secrétaire renvoie une invitation, **Then**
   un lien neuf part et le précédent est invalidé ; **Given** un compte déjà `actif`, **Then** le
   renvoi est refusé, `AUT_COMPTE_DEJA_ACTIF`, et le versant positif est le parcours par code reçu.
5. **Given** un compte en état `invite` dont la personne a perdu le message, **When** elle ouvre
   par code reçu sur son numéro, **Then** la vérification du code active le compte : posséder le
   numéro est la preuve, quel que soit le canal.
6. **Given** un compte suspendu, **When** on tente de l'inviter ou d'ouvrir son lien, **Then** le
   refus est `AUT_COMPTE_SUSPENDU`.
7. **Given** la route de création, **When** elle est appelée, **Then** elle exige la capacité
   `habilitations.compte.gerer` par le point d'insertion, porte sa clé de requête, et son rejeu ne
   crée ni second compte ni second message.

---

### User Story 7 - Changer de numéro de téléphone (Priority: P3)

Le numéro change souvent. Mme Traoré, qui a encore son ancien téléphone, demande le changement
depuis son espace : un code part vers le **nouveau** numéro, et l'identifiant ne change qu'une fois
ce code vérifié ; l'ancien numéro est informé. Quand la carte SIM est perdue, c'est le secrétariat
qui change le numéro ; toutes ses sessions tombent, ses appareils sont oubliés, et la première
ouverture sur le nouveau numéro, par code reçu, tient lieu de vérification.

**Why this priority**: la roadmap l'impose dans la tranche, pas dans une reprise. Sans procédure, un
numéro perdu est un compte perdu.

**Independent Test**: depuis une session, demander un changement vers un numéro libre, lire le
code sur la passerelle, le vérifier, constater le nouvel identifiant et le message d'information ;
par la route administrative, changer le numéro d'un compte ayant une session ouverte et constater
la révocation. Dépend des stories 1 et 5.

**Acceptance Scenarios**:

1. **Given** une session, **When** la personne demande un changement vers un nouveau numéro,
   **Then** un code à usage unique part vers ce **nouveau** numéro, avec les mêmes règles
   d'expiration, de tentatives et de débit que la story 1, et l'identifiant n'a pas changé.
2. **Given** le code reçu sur le nouveau numéro, **When** il est vérifié, **Then** l'identifiant
   du compte devient le nouveau numéro, l'ancien numéro reçoit un message d'information rédigé pour
   le message court, la session courante survit, et un événement porte l'ancien et le nouveau
   numéro.
3. **Given** un nouveau numéro qui est déjà l'identifiant d'un autre compte du tenant, **When**
   la personne demande le changement, **Then** un code part vers ce numéro comme pour tout autre ;
   **When** elle le vérifie, **Then** le refus est `AUT_IDENTIFIANT_DEJA_UTILISE`, avec son versant
   positif : le partage d'un numéro se déclare au secrétariat (story 8), jamais depuis son propre
   espace. Rien, avant la vérification, ne dit qu'un numéro est pris (E-04).
4. **Given** une personne qui n'a plus accès à son ancien numéro, **When** la secrétaire change son
   numéro par la route administrative, **Then** l'identifiant change, toutes les sessions du compte
   sont révoquées, tous ses appareils connus sont oubliés, l'ancien numéro reçoit un message
   d'information, et la personne ouvre par code reçu sur le nouveau numéro.
5. **Given** la route administrative, **When** elle est appelée, **Then** elle exige la capacité
   `habilitations.compte.gerer` par le point d'insertion et écrit un événement.

---

### User Story 8 - Deux parents, un téléphone (Priority: P3)

Le père et la mère d'Awa n'ont qu'un téléphone. Chacun a **son** compte, parce que chacun a son
lien avec l'élève et ses rubriques de communication ; les deux comptes portent le même numéro. Le
secrétariat l'a déclaré comme un partage familial en créant le second, et la déclaration est
tracée. Quand le code arrive sur le téléphone, l'écran demande **qui** ouvre la session, et le choix
est tracé avec elle. Côté personnel, un compte est individuel : aucun rattachement de personnel ne
peut se poser sur un compte dont le numéro est partagé, et c'est T1b qui porte ce refus.

**Why this priority**: c'est le cas normal des familles, et la traçabilité est ce qui rend le
partage tolérable ; sans elle, le journal d'accès ne veut rien dire.

**Independent Test**: créer deux comptes sur un même numéro, sans puis avec la déclaration ;
demander un code, constater qu'un seul message part, vérifier le code, constater le choix de la
personne et sa trace. Dépend des stories 1 et 6.

**Acceptance Scenarios**:

1. **Given** un compte portant un numéro, **When** la secrétaire crée un second compte sur ce
   numéro pour une autre personne **sans** déclarer un partage familial, **Then** le refus est
   `AUT_IDENTIFIANT_DEJA_UTILISE`, avec son versant positif : déclarer le partage.
2. **Given** la même création **avec** la déclaration de partage familial, **When** elle est
   acceptée, **Then** le second compte existe, et un événement porte qui l'a déclaré et quand.
3. **Given** deux comptes actifs sur un numéro, **When** un code est demandé, **Then** **un seul**
   message part ; **When** le code est vérifié, **Then** l'écran propose les deux noms, la session
   s'ouvre pour le compte choisi, et l'événement d'ouverture porte ce choix.
4. **Given** deux comptes connus d'un même appareil, **When** l'application s'ouvre, **Then**
   chacun a son code personnel et son nom ; le code de l'un n'ouvre pas l'autre.
5. **Given** un compte dont le numéro est partagé, **When** T1b tente d'y poser un rattachement de
   personnel, **Then** le refus est celui de T1b ; cette tranche garantit seulement que le fait
   « ce numéro est partagé » est **lisible** par T1b, et le dit dans ses hypothèses.

---

### Edge Cases

- **La passerelle de messages courts est indisponible.** La demande de code répond toujours de la
  même façon : l'envoi est un événement outbox, et son échec ne remonte jamais dans la réponse,
  sinon l'indisponibilité publierait l'existence des comptes. Le travailleur réessaie ; l'écran
  avait annoncé que le message pouvait tarder.
- **Deux codes demandés à la suite.** Le second remplace le premier ; un seul code est valide à la
  fois pour un numéro.
- **Le même numéro dans deux tenants.** Une enseignante vacataire dans deux groupes scolaires a un
  compte dans chacun. Un seul message part ; après vérification, l'écran demande où elle travaille,
  comme pour le partage familial ; **une session appartient à un seul compte d'un seul tenant**.
- **Le poste partagé sans fermeture de session.** La session s'éteint d'elle-même à
  `securite.duree_session_minutes` ; le geste de fermeture est toujours visible dans l'en-tête ;
  aucun verrouillage par inactivité n'est livré, parce que le corpus ne le demande pas, et c'est
  dit dans les hypothèses.
- **Un appareil connu prêté.** L'appareil reste connu jusqu'à la fin de sa validité ; seul le code
  personnel ouvre. Aucune gestion de la liste de ses appareils n'est livrée ici.
- **L'horloge.** Expiration des codes, des liens et des sessions en temps universel ; l'écran
  affiche les délais en durées (« dans 47 s »), jamais en heures locales.
- **Un jeton d'accès valide dont le compte a été supprimé.** Un compte ne se supprime pas ; il se
  suspend. Aucune route de suppression n'existe.
- **L'établissement actif n'a aucune année.** Le contexte porte `annees` vide et `annee_active`
  absente ; les routes pédagogiques répondent `400 ANN_ANNEE_REQUISE` comme toujours ; aucune
  route de cette tranche n'est pédagogique, la déclaration existe pour les suivantes.
- **Le lien d'invitation ouvert sur un autre appareil que le téléphone.** Il fonctionne : c'est
  l'appareil qui l'ouvre qui devient connu, pas le téléphone qui l'a reçu.
- **Le renouvellement du jeton depuis deux onglets.** Deux renouvellements concurrents avec le même
  jeton ne sont pas un vol si le second arrive dans une fenêtre courte après le premier ; au-delà,
  c'est une réutilisation et la session tombe. La fenêtre est une constante de sécurité du produit.
- **La suspension de l'administrateur désigné.** Le contexte retombe sur le téléphone de
  l'établissement ; l'écran « aucun domaine » ne nomme jamais une personne suspendue.
- **Un numéro saisi avec des espaces, un zéro initial, un indicatif absent.** La saisie est
  normalisée au format international avant toute comparaison ; l'indicatif proposé par défaut
  vient de la configuration du déploiement, jamais du code.
- **Un très grand nombre de demandes de code depuis un même client.** Une seconde limitation, par
  client et non par numéro, répond par la même limitation de débit, avant toute lecture en base.

## Requirements *(mandatory)*

### Functional Requirements

**L'identifiant**

- **FR-001** : L'identifiant d'un compte est **un numéro de téléphone**, stocké normalisé au
  format international ; aucun parcours de cette tranche ne demande, ne propose ni n'accepte une
  adresse électronique.
- **FR-002** : La forme d'affichage d'un numéro vient du country pack ; l'indicatif proposé par
  défaut sur l'écran de connexion, avant toute session, vient de la configuration du déploiement.
  Aucun indicatif ni format n'est écrit dans le code.
- **FR-003** : Un numéro mal formé est refusé `422 AUT_NUMERO_INVALIDE`, annoncé pendant la saisie,
  et ce refus ne dit rien de l'existence d'un compte.

**Le code à usage unique reçu par message court**

- **FR-004** : La demande de code répond par un accusé sans contenu, **identique** en statut, corps
  et en-têtes quel que soit le numéro bien formé ; `AUT_NUMERO_INCONNU` n'est jamais renvoyé sur
  cette route.
- **FR-005** : Le code ne part que si un compte **actif ou invité** porte ce numéro ; un compte
  suspendu ne reçoit rien. L'envoi est un événement outbox écrit dans la transaction de la
  demande, consommé par le travailleur, jamais sur le chemin de la réponse.
- **FR-006** : Le code a six chiffres, vaut dix minutes, tolère cinq saisies fausses puis est
  détruit (`AUT_OTP_TENTATIVES_EPUISEES`), expire avec `AUT_OTP_EXPIRE`, et un nouveau code
  remplace le précédent. Le code n'est jamais stocké en clair.
- **FR-007** : Une seconde demande pour le même numéro dans les soixante secondes, ou au-delà de
  cinq par heure, est refusée `429 API_LIMITE_DEBIT` avec son délai de reprise ; une limitation par
  client s'applique en plus, avant toute lecture. Aucune limitation ne suspend un compte.
- **FR-008** : La demande de code porte sa clé de requête comme toute écriture ; un rejeu renvoie
  la réponse mémorisée et **n'envoie pas un second message**.
- **FR-009** : Le message court du code est rédigé pour le message court : sous 160 caractères,
  nom de l'établissement ou du produit, durée de validité, sans abréviation ; ses variantes `fr`
  et `en` naissent ensemble.
- **FR-010** : Une saisie de code fausse est refusée `AUT_OTP_INVALIDE` en disant le nombre de
  tentatives restantes.

**La session et ses jetons**

- **FR-011** : La vérification d'un code ouvre une session : un jeton d'accès de soixante minutes
  dans la réponse, un jeton de rafraîchissement dans un cookie **non lisible par script, réservé au
  transport sécurisé, `SameSite=Strict`**, borné au chemin de rafraîchissement.
- **FR-012** : Aucun jeton n'est jamais écrit dans le stockage local, le stockage de session ni un
  cookie lisible par script ; un test le prouve après une ouverture réelle dans un navigateur.
- **FR-013** : Le jeton de rafraîchissement **tourne à chaque usage** ; l'ancien devient invalide ;
  sa réutilisation hors d'une courte fenêtre de concurrence révoque toute la session et écrit un
  événement.
- **FR-014** : Une session appartient à **un seul compte d'un seul tenant** et dure au plus
  `securite.duree_session_minutes` ; au-delà, le renouvellement est refusé.
- **FR-015** : La fermeture de session révoque sur-le-champ le jeton d'accès et le jeton de
  rafraîchissement, efface le cookie, et laisse l'appareil connu ; le geste est accessible depuis
  l'en-tête de la coquille en un geste : le **menu de compte** porté par l'avatar (nom, établissement
  et année avec leur changement, mon numéro, fermer la session), et directement dans l'en-tête dès
  la largeur `md` (E-05).
- **FR-016** : Sessions, liste de révocation, codes à usage unique et appareils connus vivent dans
  le magasin éphémère ; sa perte ne coûte que des reconnexions. Compte, identifiant, état, code
  personnel, désignation d'administrateur et événements sont durables.
- **FR-017** : Les routes d'authentification et la sonde sont les seules à répondre sans jeton ;
  toute autre route répond `401` (`AUT_JETON_MANQUANT`, `AUT_JETON_INVALIDE`,
  `AUT_SESSION_REVOQUEE`) par le middleware de session, avant toute validation de schéma.

**Le code personnel et l'appareil connu**

- **FR-018** : Après une ouverture par code reçu ou par lien, l'application propose de définir un
  code personnel à quatre chiffres, en disant son usage avant de le demander, avec « Plus tard » ;
  le code est saisi deux fois et n'est jamais stocké en clair.
- **FR-019** : Un appareil devient **connu** d'un compte à chaque ouverture par code reçu ou par
  lien sur cet appareil, et le reste `securite.appareil_connu_jours` ; plusieurs comptes peuvent
  être connus d'un même appareil, chacun avec sa propre validité.
- **FR-020** : Le code personnel n'ouvre une session que sur un appareil connu du compte ; sur un
  appareil inconnu, il n'est pas proposé, et une tentative répond `AUT_APPAREIL_INCONNU`.
- **FR-021** : L'écran d'ouverture par code personnel propose le **nom** des comptes connus de
  l'appareil et n'affiche jamais un numéro.
- **FR-022** : Cinq codes personnels faux verrouillent le code personnel du compte
  (`AUT_PIN_TENTATIVES_EPUISEES`) jusqu'à une ouverture par code reçu ; un code faux répond
  `AUT_PIN_INVALIDE` avec les tentatives restantes ; un compte sans code personnel répond
  `AUT_PIN_ABSENT`.
- **FR-023** : Changer son code personnel exige le code courant, sauf dans les dix minutes qui
  suivent une ouverture par code reçu ou par lien ; une ouverture par code reçu permet toujours de
  redéfinir un code oublié.
- **FR-024** : Un code personnel n'apparaît dans aucune réponse ; les routes disent « défini » ou
  « absent ».
- **FR-025** : Aucune biométrie n'est livrée ni proposée ; l'écart avec la maquette A1 est
  documenté.

**La révocation et la suspension**

- **FR-026** : Chaque requête protégée consulte la liste de révocation **avant** de servir ; un
  compte suspendu ne se voit servir **aucune** requête après sa suspension, quel que soit l'état
  de ses jetons.
- **FR-027** : La route de suspension de [03-api.md § 2.5](../../docs/03-api.md) est livrée : elle
  passe le compte en état `suspendu`, révoque toutes ses sessions, fait oublier le compte à tous
  ses appareils, écrit un événement, et exige `habilitations.compte.suspendre` par le point
  d'insertion de capacité.
- **FR-028** : Un compte suspendu ne reçoit aucun code, ne peut ouvrir ni par code personnel
  (`AUT_COMPTE_SUSPENDU`, et l'appareil l'oublie), ni par lien, ni par renouvellement
  (`AUT_SESSION_REVOQUEE`). La suspension est durable et survit à la perte du magasin éphémère.
- **FR-029** : La levée d'une suspension n'est pas livrée : aucune route du contrat ne la porte,
  et c'est dit dans les hypothèses.

**L'activation et la création de compte**

- **FR-030** : Un compte se crée pour une personne du tenant, avec un numéro, en état `invite` ;
  un message court portant un lien à usage unique part par l'outbox, rédigé pour le message court,
  en `fr` et en `en`. La création exige `habilitations.compte.gerer` par le point d'insertion,
  porte sa clé de requête, et son rejeu ne crée rien.
- **FR-031** : Le lien vaut `securite.invitation_validite_jours`, ne sert qu'une fois, et un
  renvoi invalide le précédent ; ouvert, il active le compte, ouvre une session, rend l'appareil
  connu et propose le code personnel.
- **FR-032** : Un lien consommé, expiré ou remplacé répond `AUT_INVITATION_INVALIDE` avec le
  versant positif ; un renvoi sur un compte `actif` répond `AUT_COMPTE_DEJA_ACTIF` ; une invitation
  sur un compte suspendu répond `AUT_COMPTE_SUSPENDU`.
- **FR-033** : La vérification d'un code reçu sur un compte `invite` l'active : la possession du
  numéro est la preuve, quel que soit le canal.
- **FR-034** : Aucune route ne renvoie un lien ni un jeton d'invitation écrit ; la réponse dit la
  date d'envoi.

**Le changement de numéro**

- **FR-035** : Depuis sa session, une personne demande un changement vers un nouveau numéro : un
  code part vers ce numéro, avec les règles de FR-006 et FR-007 ; l'identifiant ne change qu'à la
  vérification ; l'ancien numéro reçoit un message d'information ; la session courante survit ;
  un événement porte l'ancien et le nouveau numéro.
- **FR-036** : Un nouveau numéro déjà identifiant d'un autre compte du tenant est refusé
  `AUT_IDENTIFIANT_DEJA_UTILISE` en libre-service, **à la vérification du code, jamais à la
  demande** : le code part vers le nouveau numéro quoi qu'il en soit, et seule la personne qui
  possède ce numéro apprend qu'il est déjà pris (E-04). Une demande n'est donc jamais un oracle sur
  les numéros.
- **FR-037** : Une route administrative change le numéro d'un compte sans vérification préalable
  du nouveau numéro, révoque toutes les sessions du compte, oublie tous ses appareils, informe
  l'ancien numéro, écrit un événement, et exige `habilitations.compte.gerer` par le point
  d'insertion ; la première ouverture par code reçu sur le nouveau numéro tient lieu de
  vérification.

**Le numéro partagé**

- **FR-038** : Plusieurs comptes peuvent porter le même identifiant, **uniquement** si la création
  du second a déclaré explicitement un partage familial ; sans déclaration, la création répond
  `AUT_IDENTIFIANT_DEJA_UTILISE` avec le versant positif. La déclaration est un événement qui porte
  son auteur et sa date.
- **FR-039** : Quand un numéro porte plusieurs comptes, un seul code part ; après vérification, la
  personne choisit son compte parmi les noms proposés, et l'événement d'ouverture porte le choix.
  Il en va de même quand le numéro porte des comptes dans plusieurs tenants.
- **FR-040** : Le fait qu'un identifiant est partagé est lisible par l'interface de service du
  module, pour que T1b refuse d'y poser un rattachement de personnel.

**Les en-têtes et l'isolation**

- **FR-041** : La résolution provisoire du tenant depuis l'en-tête d'établissement, posée par T0a,
  est **retirée** ; le tenant d'une transaction vient du compte de la session, posé dans la
  transaction et jamais sur la connexion.
- **FR-042** : `X-Nelo-Etablissement` est vérifié contre les rattachements du compte : absent ou
  malformé, `400 TEN_ETABLISSEMENT_REQUIS` ; présent mais non rattaché, `403
  TEN_ETABLISSEMENT_NON_AUTORISE`, que l'établissement soit du même tenant, d'un autre, ou
  inexistant, sans qu'aucune différence de réponse ne les distingue.
- **FR-043** : `X-Nelo-Annee` est exigé sur toute route **déclarée pédagogique** : absent,
  `400 ANN_ANNEE_REQUISE` sans aucun repli sur l'année active, même unique ; malformé,
  `400 ANN_ANNEE_REQUISE` ; présent mais hors de l'établissement actif ou hors du tenant,
  `404 TEN_RESSOURCE_INTROUVABLE`. Chaque route déclare si elle est pédagogique ; aucune route de
  cette tranche ne l'est, et un test exerce la déclaration sur une route de test.
- **FR-044** : Les quatre en-têtes sont lus par des middlewares, avant toute validation de schéma,
  pour que la table de refus de [03-api.md § 1.2](../../docs/03-api.md) soit vraie.
- **FR-045** : Chaque table neuve porte la politique de sécurité au niveau ligne activée et forcée,
  et le test d'isolation entre deux tenants couvre chacune ; le compte, ses rattachements et ses
  événements ne traversent aucune frontière de module par une clé étrangère.
- **FR-046** : Les routes du socle T0a (les paramètres) exigent désormais une session ; leurs tests
  sont adaptés, leur contrat ne change pas.

**Le contexte**

- **FR-047** : `GET /moi/capacites` est livrée et renvoie la forme de [03-api.md § 1.9](../../docs/03-api.md)
  telle que T0b l'a enregistrée dans le contrat, sans ajout ni retrait de champ, avec `capacites`
  et `acces_nominatifs` vides jusqu'à T1b.
- **FR-048** : `etablissements` porte les établissements auxquels le compte est rattaché, jamais
  les autres du tenant ; `etablissement_actif` est celui de l'en-tête ; `annees` porte les années
  de l'établissement actif auxquelles le compte est rattaché, avec libellé et état ;
  `annee_active` est celle en état actif ou est absente.
- **FR-049** : Chaque établissement du contexte porte son `administrateur` : la personne que
  l'établissement a désignée, ou, à défaut ou si son compte est suspendu, le nom et le téléphone
  de l'établissement avec des prénoms vides ; jamais un champ absent.
- **FR-050** : `country_pack`, `parametres_effectifs` et `alertes` sont lus depuis les données du
  tenant ; aucune valeur de pays, de devise ou de vocabulaire n'est écrite dans le code.
- **FR-051** : La coquille de T0b lit le contexte réel par sa source de contexte, sans qu'un
  composant ni une page change ; le choix de l'établissement et de l'année se fait dans la
  coquille, se mémorise sur l'appareil, et **jamais** côté serveur comme un défaut.
- **FR-052** : Un compte rattaché à un seul établissement arrive directement dans son espace ; à
  plusieurs, il choisit ; changer d'établissement ou d'année relit le contexte.

**Les écrans**

- **FR-053** : Les écrans de cette tranche suivent la maquette A1 et s'assemblent à partir des
  quatorze composants de T0b, sans composant neuf : numéro, code reçu, choix de la personne (quand
  le numéro est partagé), définition du code personnel, ouverture par code personnel, choix de
  l'établissement, activation par lien, changement de numéro ; chacun en clair et en sombre, à
  390 px et élargi, atteignable dans les deux moteurs de rendu (P-05).
- **FR-054** : Chaque refus est annoncé avant la saisie quand il est prévisible (format du numéro,
  compte à rebours du renvoi, tentatives restantes) et dit son versant positif.
- **FR-055** : Aucune chaîne d'interface en dur ; les clés `fr` et `en` naissent ensemble, y
  compris les messages courts ; le lexique s'étend du vocabulaire de la tranche.
- **FR-056** : L'écran de connexion est budgété au même plafond que l'accueil dans le registre des
  écrans ; son poids est mesuré (P-10).
- **FR-057** : L'écran « numéro inconnu » de la maquette A1 n'est pas livré ; l'orientation vers
  le secrétariat, sans numéro, est portée par l'écran du code reçu, et l'écart est documenté.
  L'écran du numéro porte le nom du produit, jamais celui d'un établissement (E-01).
- **FR-063** : La création d'un compte expose son pendant de vérification, `POST /comptes/verification`,
  qui dit ce qui bloquerait (personne déjà titulaire d'un compte, numéro déjà porté et partage
  familial à déclarer) sans rien écrire ni envoyer ; il exige la même capacité (E-04).
- **FR-064** : Les mots d'écran d'un compte suspendu et d'une session révoquée existent en `fr` et
  `en`, disent un fait et leur versant positif : « Votre accès est fermé » avec le nom et le
  téléphone de l'administrateur de l'établissement quand le compte est connu (code personnel,
  lien) ; « Votre session est terminée » avec « Ouvrir une nouvelle session » (E-07). Une demande de
  code sur un compte suspendu n'affiche rien : la réponse est la même que pour tout numéro.
- **FR-065** : Les deux états de l'année que la coquille affiche portent un code de pastille et un
  mot du lexique (`ANNEE_ACTIVE`, voix neutre ; `ANNEE_PREPARATION`, voix ocre) ; les états du
  compte et le partage familial n'ont aucun écran dans cette tranche et entrent au lexique « à
  venir » pour T1b (E-03). Le mot visible du canal est **SMS**, jamais « message court » ni
  « texto » (E-06).

**La traçabilité, les paramètres et la vérification**

- **FR-058** : Chaque changement d'état d'un compte et chaque événement de session significatif
  (ouverture par code reçu, par code personnel, par lien, choix d'un compte sur un numéro partagé,
  fermeture, révocation par réutilisation, suspension, changement de numéro, déclaration de
  partage) écrit un événement outbox dans la même transaction ; le journal des événements est en
  insertion seule.
- **FR-059** : La dernière connexion du compte est mise à jour à chaque ouverture.
- **FR-060** : Les durées et seuils qui dépendent du tenant sont des clés du catalogue de
  [02-domaine.md § 17](../../docs/02-domaine.md) : `securite.duree_session_minutes` (existante),
  `securite.pin_tentatives_max`, `securite.appareil_connu_jours`, `securite.invitation_validite_jours`.
  Les seuils évalués **avant** qu'un compte soit connu (longueur et validité du code, tentatives,
  délais de renvoi, limitations de débit, fenêtre de concurrence du rafraîchissement) sont des
  constantes de sécurité du produit, portées en un seul endroit, nommées, jamais dispersées.
- **FR-061** : Toute règle nouvelle a son test négatif : retirer la consultation de la liste de
  révocation, rendre la réponse de demande de code différente selon l'existence du compte, replier
  une route pédagogique sur l'année active, ou écrire un jeton dans le stockage du navigateur fait
  échouer la vérification.
- **FR-062** : `scripts/verifier.sh` passe en une commande, et le contrat régénéré ne produit aucun
  diff (P-03).

### Key Entities *(include if data involved)*

- **Compte** : ce par quoi une personne s'identifie. Porte le rattachement à sa personne (par
  identifiant, R13), l'identifiant (numéro normalisé), le code personnel (empreinte, jamais en
  clair), l'état (`invite`, `actif`, `suspendu`), la dernière connexion, la date d'invitation.
  Appartient à un tenant ; plusieurs comptes peuvent porter le même identifiant sous déclaration de
  partage familial.
- **Rattachement du compte à un établissement et à une année** : ce contre quoi les en-têtes sont
  vérifiés. C'est l'**affectation** de [02-domaine.md § 3.2](../../docs/02-domaine.md), dont cette
  tranche ne pose que ce dont elle a besoin (compte, année, établissement, début, fin) ; T1b y
  ajoute le rôle et le périmètre sans renommer ni retirer.
- **Session** : éphémère. Un jeton d'accès court, une famille de jetons de rafraîchissement en
  rotation, le compte et le tenant, l'instant d'ouverture, la borne de durée ; la liste de
  révocation la coupe.
- **Appareil connu** : éphémère, borné dans le temps. Le lien entre un appareil et un compte, né
  d'une ouverture par code reçu ou par lien, qui autorise le code personnel.
- **Code à usage unique** : éphémère. Six chiffres, un numéro, une expiration, un compteur de
  tentatives ; sert à ouvrir, à activer, à vérifier un nouveau numéro.
- **Invitation** : un jeton à usage unique, sa date d'envoi, son expiration, son état ; ne sort
  jamais d'une réponse.
- **Administrateur désigné de l'établissement** : le compte que l'établissement désigne comme
  celui qui attribue les domaines ; nourrit `administrateur` du contexte.
- **Événement de compte** : l'événement outbox de chaque changement d'état et de chaque ouverture ;
  c'est la traçabilité du partage familial et du départ d'un membre du personnel.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** : Une personne qui a reçu son code arrive dans son espace en **trois écrans** (numéro,
  code, code personnel ou « plus tard ») et en moins de **90 secondes** après la réception, sur un
  téléphone à 390 px en réseau 2G.
- **SC-002** : Sur un appareil connu, la réouverture par code personnel prend moins de
  **10 secondes** et produit **zéro** message court ; une journée de six ouvertures produit zéro
  message.
- **SC-003** : Sur cent demandes de code alternant numéro connu et numéro inconnu, les réponses
  sont identiques en statut, corps et en-têtes dans **100 %** des cas, et la différence des temps
  de réponse médians est inférieure à **50 ms**.
- **SC-004** : Après une suspension, **zéro** requête du compte est servie ; le premier refus
  survient à la requête immédiatement suivante, sans attendre l'expiration d'aucun jeton.
- **SC-005** : Sur deux tenants, **100 %** des tentatives de lecture croisée (en-tête
  d'établissement, en-tête d'année, ligne de table) sont refusées, et aucune réponse ne diffère
  selon que la ressource tierce existe ou non.
- **SC-006** : **100 %** des routes hors la sonde et l'authentification refusent une requête sans
  jeton, et **0** jeton est trouvé dans le stockage du navigateur après une ouverture réelle.
- **SC-007** : **100 %** des réutilisations d'un jeton de rafraîchissement tourné hors fenêtre sont
  détectées et révoquent la session entière.
- **SC-008** : L'événement d'envoi du code est remis à la passerelle simulée moins de **5 secondes**
  après la demande, par le travailleur, dans **100 %** des cas où un compte existe, et dans **0 %**
  des cas où il n'existe pas.
- **SC-009** : L'écran de connexion tient sous son plafond de poids, mesuré par P-10, en clair et
  en sombre, sur les deux moteurs de rendu.
- **SC-010** : **100 %** des chaînes visibles de la tranche, messages courts compris, existent en
  `fr` et en `en` (P-06).
- **SC-011** : Chaque règle nouvelle casse volontairement une fois dans `scripts/tests-negatifs.sh`
  et fait échouer la vérification ; le dépôt reste intact.
- **SC-012** : `scripts/verifier.sh` passe en une commande, en moins de **5 minutes** sur un poste
  de développement.

## Assumptions

- **La tranche précède T1b, T2a et T3a, dont elle doit lire les entités.** Vérifier un en-tête
  « contre les affectations du compte » suppose l'affectation (T1b) et l'année (T2a) ; composer le
  contexte suppose le nom et la langue de la personne (T3a). T1b dit déjà qu'elle « autorise
  l'accès à des ressources qui n'existent pas encore », et T2a laisse à T1b l'affectation à une
  année : la roadmap accepte cet ordre. Cette spécification exige le **comportement** et laisse au
  plan le **socle minimal** à poser, sous trois contraintes : chaque colonne posée est une colonne
  du domaine, avec son nom ; la tranche propriétaire complète sans renommer ni retirer ; aucune
  règle de ces tranches (transition d'année, calcul des capacités, lien de responsabilité) n'est
  implémentée ici. C'est le mécanisme du point d'insertion que T0a a laissé pour la capacité.
- **Diffs appliqués sur le corpus, dérivés et tracés**, selon l'arbitrage délégué du journal :
  - [02-domaine.md § 1.2](../../docs/02-domaine.md) : `etablissement` porte
    `administrateur_compte_id?`. Le contexte de § 1.9 exige un administrateur nommé par
    établissement « que T1a sert » ; sans désignation, le modèle ne pouvait pas le nommer.
  - [02-domaine.md § 16](../../docs/02-domaine.md) : `compte` : `invite` → `actif` → `suspendu`.
    Le champ `statut` existait sans ses valeurs.
  - [02-domaine.md § 17](../../docs/02-domaine.md) : trois clés `securite.*` (tentatives du code
    personnel, validité de l'appareil connu, validité de l'invitation), à côté de la durée de
    session qui existait.
  - [03-api.md § 1.8](../../docs/03-api.md) : le `429` porte le code `API_LIMITE_DEBIT`, qui
    n'était pas nommé.
  - [03-api.md § 2.1](../../docs/03-api.md) : les codes `AUT_OTP_INVALIDE`, `AUT_NUMERO_INVALIDE`,
    `AUT_PIN_INVALIDE`, `AUT_PIN_ABSENT`, `AUT_PIN_TENTATIVES_EPUISEES`, `AUT_APPAREIL_INCONNU`,
    `AUT_INVITATION_INVALIDE`, `AUT_COMPTE_DEJA_ACTIF`, `AUT_IDENTIFIANT_DEJA_UTILISE`.
  - [03-api.md § 2.2](../../docs/03-api.md) : `POST /moi/telephone` et
    `POST /moi/telephone/verification`, la procédure de changement en libre-service que le prompt
    impose et que le contrat ne portait pas.
  - [03-api.md § 2.5](../../docs/03-api.md) : `POST /comptes` (créer et inviter),
    `POST /comptes/{id}/invitation` (renvoyer), `POST /comptes/{id}/telephone` (changement
    administratif), sous une capacité `habilitations.compte.gerer`, à côté de la suspension.
- **Les valeurs par défaut sont provisoires et ouvertes en Q30 du journal** : code à six chiffres
  valable dix minutes, cinq tentatives, renvoi après soixante secondes, cinq demandes par heure et
  par numéro ; code personnel à quatre chiffres, cinq tentatives ; appareil connu 90 jours ;
  invitation 7 jours. Les valeurs de la maquette A1 sont reprises quand elle en donne ; les autres
  sont des pratiques courantes. Changer l'une d'elles touche une constante nommée ou une clé du
  catalogue, jamais un écran.
- **Une session est pour un seul compte d'un seul tenant.** Un numéro qui porte des comptes dans
  plusieurs tenants, ou plusieurs comptes d'une famille, conduit à un choix après vérification du
  code ; changer de compte est une nouvelle session.
- **Les seuils évalués avant qu'un compte soit connu ne peuvent pas être des clés de tenant** : la
  demande de code précède la connaissance du tenant. Ils sont des constantes de sécurité du
  produit, en un seul endroit.
- **Le pack de pays du contexte** : T0a n'a pas posé la table `country_pack` de
  [02-domaine.md § 1.2](../../docs/02-domaine.md) ; le plan la pose ou lit le pack d'une autre
  manière, mais le contexte ne porte jamais une valeur de pays venue du code.
- **La cohérence entre l'identifiant du compte et le téléphone principal de la personne** est une
  règle de T3a ; ici, l'identifiant du compte est la seule source pour l'ouverture de session.
- **Aucun verrouillage par inactivité, aucune liste de ses appareils, aucune levée de suspension**
  ne sont livrés : le corpus ne les demande pas. La levée de suspension attend une route et une
  capacité que T1b arbitrera.
- **Le lien d'invitation active sans étape de confirmation** : ouvrir le lien reçu sur le numéro
  est la preuve, au même titre que le code. Un lien perdu se remplace par le code reçu.
- **Le profil (`/moi/profil`) n'est pas livré** : la langue affichée vient du compte après
  ouverture, de l'appareil avant ; sa modification arrive avec la personne (T3a).
- **La revue visuelle prend la forme A** : cette tranche produit des écrans qu'une personne
  regarde. Les données de démonstration sont celles du primaire.

## Hors périmètre

- Les capacités, les rôles, les périmètres, le calcul des capacités effectives, le refus d'un
  rattachement de personnel sur un numéro partagé, la levée de suspension, la revue des accès :
  T1b. Ici, `capacites` est vide et chaque route qui exige une capacité passe par le point
  d'insertion.
- Les transitions de l'année scolaire, sa bascule, ses périodes : T2a. La personne, ses liens, ses
  rubriques, le profil : T3a.
- Le moteur de messages, le routage, le budget, les fenêtres d'envoi : T4a. Les messages de cette
  tranche passent par la passerelle simulée de T0a et par l'outbox, avec leurs variantes rédigées.
- La biométrie, les clés d'accès, tout second facteur au-delà de la possession du numéro.
- Le verrouillage par inactivité, la gestion de ses appareils, la fermeture de toutes ses sessions
  depuis son espace.
- L'appel vocal de secours que la maquette A1 évoque (« Recevoir le code par appel vocal ») : la
  hiérarchie des canaux de [02-domaine.md § 11.1](../../docs/02-domaine.md) le place en V3.
- Le hors-connexion, tout cache de données, Capacitor, Tauri, le serveur d'intégration continue,
  tout déploiement.
- Tout ce que [docs/06-apres-mvp.md](../../docs/06-apres-mvp.md) décrit ; ce document ne s'ouvre
  pas pour cette tranche.

## Revue visuelle

Cette tranche produit des écrans qu'une personne regarde : la revue prend la **forme A** de
[docs/05-design.md](../../docs/05-design.md#forme-a--la-tranche-a-des-écrans), un canvas `/design`,
**un artboard par user story**, en session dédiée après cette spécification et avant le plan. Le
prompt prêt à coller est dans [design/prompt-design.md](design/prompt-design.md). Les sources vont
dans `specs/003-connexion-contexte/design/`. Trois écarts avec la maquette A1 y sont à encadrer :
l'écran « numéro inconnu » (le contrat gagne), l'empreinte digitale (le domaine gagne), l'appel
vocal (V3).

**Canvas publié** le 2026-09-17, **validé** le 2026-09-17 :
<https://claude.ai/artifact/2jb9b3vRrhWTMmyKBSNRdW>. Huit artboards `US1` à `US8`, sources
`specs/003-connexion-contexte/design/US1..US8.dc.html` + `canvas.json` ; le fichier assemblé
`canvas.html` n'est pas versionné. Les trois écarts annoncés avec A1 y sont barrés (numéro inconnu,
empreinte digitale, appel vocal). La planche en relève sept autres, encadrés en pointillé ocre,
**tranchés le 2026-09-17** (E-01 à E-07, détail dans [research.md](research.md#après-la-revue-visuelle--sept-écarts-tranchés)) :

- **Avant la session, le tenant n'est pas connu** : l'écran du numéro ne peut pas nommer
  l'établissement, et la carte « Le SMS n'est pas encore arrivé ? » ne peut pas tenir le numéro du
  secrétariat depuis le contexte (§ 1.9 ne sert qu'après). Configuration du déploiement, comme
  l'indicatif (FR-002), ou la carte sans numéro : le scénario 10 de US1 et FR-057 en dépendent.
  **E-01 : la carte sans numéro, l'écran du numéro au nom du produit.** Un numéro de déploiement
  serait celui de l'éditeur, pas du secrétariat.
- **Les six cases du code et le pavé numérique d'A1 sont des composants neufs** que le plan refuse
  (R-21) : champ nombre du canon. Si les cases sont voulues, c'est un arrêt de cycle.
  **E-02 : refusés.** Le champ nombre du canon, avec `inputmode="numeric"` et `autocomplete="one-time-code"`,
  fait la même chose ; un composant neuf pour un gain visuel ne vaut pas un arrêt de cycle.
- **Trois états sans code de pastille ni mot du lexique** : l'année (`ACTIVE`, `PREPARATION`),
  le compte (`invite`, `actif`, `suspendu`), le partage familial d'un numéro.
  **E-03 : `ANNEE_ACTIVE` et `ANNEE_PREPARATION` entrent dans les codes de pastille et au lexique** ;
  les états du compte et le partage n'ont aucun écran ici et entrent au lexique « à venir » (T1b).
- **Le refus « identifiant déjà utilisé » n'est pas prévisible avant l'envoi** : ni `POST /comptes`
  ni `POST /moi/telephone` n'ont de pendant `/verification` (03-api § 3, règle 3). La planche
  annonce au retour du premier envoi ; sinon le contrat gagne une route.
  **E-04 : deux réponses.** En libre-service, le refus est **différé à la vérification du code** :
  un pendant qui dirait « ce numéro est pris » serait un oracle sur les numéros, l'inverse de la
  contrainte non négociable. Pour le secrétariat, le contrat gagne `POST /comptes/verification`
  (règle 3 de § 3), sous la même capacité.
- **L'en-tête à 390 px n'a pas la place du geste « Fermer la session »** sans rogner le nom de
  l'établissement ; FR-015 exclut de le cacher dans le menu de l'avatar.
  **E-05 : l'avatar ouvre le menu de compte** (nom, établissement et année, mon numéro, fermer la
  session), un geste depuis l'en-tête à toute largeur ; dès `md`, « Fermer la session » est aussi
  directement dans l'en-tête. FR-015 est reformulée.
- **« SMS » ou « message court »** : la spec cite l'un, A1 et la pastille de canal disent l'autre ;
  le lexique doit fixer le mot visible.
  **E-06 : SMS.** C'est le mot d'A1, de la pastille de canal et du terrain ; « message court » reste
  un mot de documentation.
- **Ce que lit un compte suspendu** (`AUT_COMPTE_SUSPENDU`, `AUT_SESSION_REVOQUEE`) : la spec donne
  les codes, pas le mot d'écran ni son versant positif.
  **E-07 : « Votre accès est fermé », avec l'administrateur nommé** quand le compte est connu ;
  « Votre session est terminée », « Ouvrir une nouvelle session » ; rien à la demande de code
  (FR-064).
