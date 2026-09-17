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

## La règle de rédaction

Un refus s'annonce avant la saisie, et il dit son **versant positif**
([05-design.md § 8.2](../05-design.md)) : « Aucun élève sélectionné : sélectionnez-en au moins un
pour enregistrer », « L'effectif dépasse les 34 élèves inscrits : saisissez un nombre entre 0 et
34 ». Un message dit un fait, jamais un jugement.
