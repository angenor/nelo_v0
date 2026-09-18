# Le lexique

*Les mots visibles du produit. Écrit avec les clés de T0b ; semé de
[05-design.md § 8.1](../05-design.md).*

**Ce document prime sur les clés.** Quand `web/app/core/i18n/fr.json` et ce lexique divergent, c'est
le fichier de clés qui a tort, et un test le dit (`web/tests/unit/lexique.test.ts`). Un mot métier
(« classe », « bulletin », « responsable légal ») ne vit pas dans les clés : il vient du pack de
pays, par son code neutre ([02-domaine.md § 15](../02-domaine.md)).

Comment lire les tableaux :

- **On dit** : le mot, tel qu'il s'affiche en français.
- **On ne dit jamais** : les mots refusés, séparés par des virgules. Une précision en italique
  entre parenthèses borne le refus ; un refus qui porte **sa condition entre parenthèses** (« alerte
  (pour un signalement) ») dépend du contexte et se relit à la main, le test ne le vérifie pas.
- **Où il vit** : `fr.json` (une clé d'interface), `pack` (un code neutre du pack), ou `à venir`
  quand aucun écran de la tranche ne l'affiche encore.

## 1. Le vocabulaire canonique

| On dit | On ne dit jamais | Où il vit |
|---|---|---|
| Élève | Apprenant, étudiant *(sauf dans le supérieur, où le pack le dit)* | `fr.json` |
| Responsable légal | Parent *(sauf quand le lien est effectivement PERE ou MERE)* | pack, code `RESPONSABLE` |
| Appel | Pointage, feuille de présence | `fr.json` |
| Absence non justifiée | Absence illégale, absence sauvage | `fr.json` |
| Bulletin | Relevé de notes | pack, code `BULLETIN` |
| Reste à payer | Impayé, dette, arriéré *(l'arriéré existe, mais c'est la créance sur l'État)* | `fr.json` |
| Échéance | Deadline, date limite | `fr.json` |
| Enregistré | Sauvegardé, synchronisé | `fr.json` |
| Signalement | Dénonciation, alerte (pour un signalement) | à venir, T9 |
| Établissement | École *(le MVP sert des écoles primaires, le produit servira aussi des lycées et des groupes scolaires)* | `fr.json` |

**« Impayé » ne s'affiche pas.** L'état métier garde son code, `IMPAYE`, et sa voix rouge
(FR-005) ; le mot visible de la pastille est **« En retard »**, l'état `en_retard` de l'échéance
([02-domaine.md § 16](../02-domaine.md)). Le montant, lui, se dit « Reste à payer ».

**« Alerte » reste le nom d'un composant** ([composants.md § 11](composants.md)) : le refus porte sur
le signalement, qu'on n'appelle jamais une alerte.

## 2. Les refus propres à la tranche

| On dit | On ne dit jamais | Pourquoi |
|---|---|---|
| En ligne | Web | Le canal se dit comme l'espace en ligne ([ADR 002](../adr/002-web-d-abord-capacitor-plus-tard.md)), écart 2 de la revue visuelle |
| Hors ligne | Déconnecté, erreur réseau | Une coupure n'est pas une faute ; le ruban la dit en ocre |
| Rien ne sera perdu | Rechargez la page, réessayez plus tard | La saisie ne se perd pas et ne demande aucun geste (FR-013, FR-042) |
| Famille | Parents d'élèves | Hors du mot du pack, on parle de la famille |
| SMS | Message court, texto | Le mot du terrain et celui de la pastille de canal (écart E-06 de T1a) ; « message court » reste le mot de la documentation |
| Code reçu | Mot de passe à usage unique, OTP | Ce qui arrive par SMS est un code, et il se dit comme la personne le lit |
| Code personnel | Code secret, PIN | Quatre chiffres sur un appareil connu, ce n'est pas un mot de passe |
| Ouvrir une session | Se connecter, login | Le poste est partagé : une session s'ouvre, puis se ferme |
| Fermer la session | Se déconnecter, logout | Le même mot, dans l'autre sens ; jamais un anglicisme |
| Votre compte n'est pas bloqué | Compte verrouillé, compte banni | Cinq codes faux détruisent le code, jamais le compte : le refus dit ce qui reste ouvert |
| Le secrétariat peut le vérifier avec vous | Numéro inconnu, numéro non enregistré | Aucun écran ne dit qu'un numéro est inconnu (écart E-01) ; le versant positif est le geste qui débloque |
| Reprise possible dans une durée | Trop de tentatives, accès refusé | Une attente se dit par sa durée, et le dernier code reçu reste valable |

## 3. Les mots de la tranche

Chaque mot ci-dessous est la valeur exacte de sa clé en français. L'anglais naît avec lui dans
`en.json`.

### Les états

| Mot | Clé |
|---|---|
| Payé | `etat.paye` |
| Soldé | `etat.solde` |
| Justifié | `etat.justifie` |
| Enregistré | `etat.enregistre` |
| Validé | `etat.valide` |
| Échéance proche | `etat.echeance_proche` |
| En attente | `etat.en_attente` |
| Non fait | `etat.non_fait` |
| En retard | `etat.impaye` |
| Non justifié | `etat.non_justifie` |
| Présent | `etat.present` |
| Brouillon | `etat.brouillon` |
| Proposé, non validé | `etat.propose` |
| Active | `etat.annee_active` |
| En préparation | `etat.annee_preparation` |
| Activé | `interrupteur.active` |
| Désactivé | `interrupteur.desactive` |

### Le ruban

| Mot | Clé |
|---|---|
| Tout est enregistré | `ruban.enregistre` |
| Envoi de {n} saisies | `ruban.envoi_de` |
| Hors ligne | `ruban.hors_ligne` |
| Aucun enregistrement pour l’instant | `ruban.aucun_enregistrement` |
| Aucune saisie en attente | `ruban.aucune_attente` |
| Vous pouvez continuer à saisir | `ruban.continuez` |
| {n} saisies conservées, envoi à la reconnexion | `ruban.conservees` |
| Continuez, rien ne sera perdu | `ruban.rien_perdu` |
| Lien bon | `ruban.lien_bon` |
| Lien faible | `ruban.lien_faible` |
| Pas de lien | `ruban.pas_de_lien` |

### La coquille

| Mot | Clé |
|---|---|
| Accueil | `coquille.accueil` |
| Tableau composé | `coquille.tableau_compose` |
| Votre compte n’a encore aucun domaine | `coquille.aucune_capacite.titre` |
| Demander mes accès | `coquille.aucune_capacite.action` |
| À propos | `coquille.a_propos` |
| Retour | `coquille.retour` |
| Élèves | `famille.ELEVES` |
| Enseignement | `famille.ENSEIGNEMENT` |
| Gestion | `famille.GESTION` |
| Communication | `famille.COMMUNICATION` |
| Paramètres | `famille.PARAMETRES` |
| Appel du jour | `entree.appel_du_jour` |
| Absences et retards | `entree.absences` |

### Les canaux

| Mot | Clé |
|---|---|
| En ligne | `canal.EN_LIGNE` |
| WhatsApp | `canal.WHATSAPP` |
| SMS | `canal.SMS` |
| Papier | `canal.PAPIER` |

### La session

| Mot | Clé |
|---|---|
| Suivez la scolarité de vos enfants | `session.numero.titre` |
| Votre numéro de téléphone | `session.numero.champ` |
| Recevoir le code par SMS | `session.numero.action` |
| Entrez le code à six chiffres | `session.code.titre` |
| Code reçu par SMS | `session.code.champ` |
| Ouvrir ma session | `session.code.ouvrir` |
| Renvoyer le code | `session.code.renvoyer` |
| Recevoir un nouveau code | `session.code.nouveau` |
| Modifier | `session.code.modifier` |
| Le SMS n’est pas encore arrivé ? | `session.code.pas_arrive.titre` |
| Fermer la session | `session.fermer` |
| Votre session est terminée | `session.revoquee.titre` |
| Votre accès est fermé | `session.suspendu.titre` |
| Choisissez un code à quatre chiffres | `session.pin.titre` |
| Code à quatre chiffres | `session.pin.champ` |
| Le même code, une seconde fois | `session.pin.confirmation` |
| Enregistrer ce code | `session.pin.enregistrer` |
| Plus tard : me connecter par SMS | `session.pin.plus_tard` |
| Votre code personnel | `session.ouverture.champ` |
| Ouvrir ma session | `session.ouverture.ouvrir` |
| Code personnel verrouillé après cinq essais | `session.ouverture.verrou` |
| Code personnel défini | `session.ouverture.pin_defini` |
| Pas encore de code personnel | `session.ouverture.pin_absent` |
| Qui ouvre la session ? | `session.choix.titre` |
| Code vérifié | `session.choix.verifie` |
| Un autre numéro | `session.ouverture.autre_numero` |
| Ce lien ne fonctionne plus | `session.activation.invalide.titre` |
| Entrer mon numéro et recevoir un code | `session.activation.numero` |
| Changer mon numéro | `session.telephone.titre` |
| Nouveau numéro | `session.telephone.nouveau` |
| Recevoir le code sur le nouveau numéro | `session.telephone.action` |
| Confirmer le nouveau numéro | `session.telephone.confirmer` |
| Votre numéro est changé | `session.telephone.change` |

### Le menu de compte

| Mot | Clé |
|---|---|
| Établissement | `coquille.etablissement` |
| Année de travail | `coquille.annee` |
| Mon numéro | `coquille.mon_numero` |

**Trois états n'ont encore aucun écran, et n'ont donc aucun mot : à venir.** L'état d'un compte
(`invite`, `actif`, `suspendu`) et le partage familial d'un numéro entrent au lexique avec T1b, qui
les affiche le premier ; l'écart E-03 de T1a le dit, et rien ne les dessine d'ici là. Les deux états
de l'année, eux, ont leur code de pastille et leur mot dès maintenant, parce que l'en-tête les
montre.

## La règle de rédaction

Un refus s'annonce avant la saisie, et il dit son **versant positif**
([05-design.md § 8.2](../05-design.md)) : « Aucun élève sélectionné : sélectionnez-en au moins un
pour enregistrer », « L'effectif dépasse les 34 élèves inscrits : saisissez un nombre entre 0 et
34 ». Un message dit un fait, jamais un jugement.
