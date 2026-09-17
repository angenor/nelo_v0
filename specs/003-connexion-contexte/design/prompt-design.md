# Prompt de revue visuelle, forme A, T1a Se connecter et savoir où l'on est

*Cette tranche produit des écrans qu'une personne regarde. On lance `/design` en session dédiée,
après `specify` et avant `plan`. Gabarit : [docs/05-design.md § Forme A](../../../docs/05-design.md).
La maquette A1 (`01_connexion-mobile.html`) est la référence de facture du parcours ; trois de ses
éléments sont contredits par le corpus et doivent apparaître encadrés en pointillé ocre : l'écran
« numéro inconnu », l'empreinte digitale, l'appel vocal.*

```text
/design Représente les user stories de specs/003-connexion-contexte/spec.md pour la tranche T1a,
Se connecter et savoir où l'on est.

Un artboard par user story, nommé par son identifiant, huit artboards :
  US1 : le parcours par code reçu à 390 px : l'écran du numéro (un champ, un bouton, l'indicatif
        proposé, la langue fr/en), l'écran du code à six chiffres avec le compte à rebours du
        renvoi, l'annonce que le message peut tarder et que le code vaut dix minutes, l'orientation
        vers le secrétariat avec son numéro ; les états « code faux, N tentatives restantes »,
        « code expiré » et « trop de demandes, reprise dans N s », chacun avec son versant positif.
        L'écran « numéro inconnu » de la maquette A1 en pointillé ocre, barré : le contrat gagne.
  US2 : un diagramme de séquence des quatre en-têtes : session absente (401), établissement absent
        (400), établissement non rattaché (403, même réponse pour un autre tenant), année absente
        sur une route pédagogique (400, jamais de repli), année hors établissement (404). À côté,
        deux tenants et un compte chacun, la barrière RLS et la barrière applicative dessinées
        toutes deux, aucune n'étant seule.
  US3 : la définition du code personnel (pourquoi avant quoi, deux saisies, « Plus tard »), puis
        l'ouverture par code personnel sur un appareil connu : le nom de la personne, jamais son
        numéro, quatre chiffres ; le poste partagé avec trois noms ; l'état « code personnel
        verrouillé, recevez un code » ; l'empreinte digitale de la maquette A1 en pointillé ocre,
        barrée : le domaine gagne.
  US4 : la coquille de T0b sur le contexte réel : l'écran « aucun domaine » qui nomme
        l'administrateur avec son téléphone ; le choix de l'établissement quand il y en a deux ;
        le changement d'année dans l'en-tête, avec l'année active et l'année en préparation ; à
        390 px et à 1200 px.
  US5 : un flux de gauche à droite : ouverture, rafraîchissement avec rotation, réutilisation d'un
        jeton tourné qui fait tomber la session, suspension qui refuse la requête suivante, fermeture
        depuis l'en-tête ; et la coupe d'un navigateur où le stockage est vide et le cookie non
        lisible.
  US6 : le message court d'invitation sous 160 caractères avec le nom de l'établissement, l'écran
        d'activation depuis le lien qui enchaîne sur le code personnel, l'état « lien déjà utilisé
        ou expiré » avec ses deux issues (entrer son numéro, demander un nouveau lien).
  US7 : le changement de numéro depuis son espace : nouveau numéro, code reçu sur le nouveau,
        confirmation, message d'information à l'ancien ; et la variante secrétariat pour une carte
        SIM perdue, avec l'avertissement que les sessions tombent.
  US8 : deux parents, un téléphone : après le code, l'écran « Qui ouvre la session ? » avec les
        deux noms ; la création du second compte au secrétariat avec la déclaration de partage
        familial et le refus sans déclaration, dit avant la saisie.

À lire avant de dessiner, et à ne pas dépasser :
- docs/02-domaine.md, sections 3.1, 3.2, 3.6, 16 et 17 : le compte, ses états, ses invariants,
  les clés de sécurité
- docs/03-api.md, sections 1.2, 1.9, 2.1, 2.2 et 2.5 : les en-têtes et leur table de refus, le
  contexte, les routes et les codes d'authentification
- docs/design/theme.css : les jetons, seule source des couleurs
- docs/design/ecrans/13_systeme-de-design.html : les quatorze composants et leurs états
- docs/design/ecrans/01_connexion-mobile.html : la maquette A1, référence de facture du parcours
- docs/design/ecrans/06_navigation-composee.html : le shell composé
- docs/05-design.md : la synthèse, la langue et les règles d'écran
- docs/01-stack.md, section 5.1 : la session sur poste partagé

Contraintes non négociables : mobile-first mais responsive · mode clair ET mode sombre, les deux ·
52 px de cible tactile en classe, 48 ailleurs, 44 en plancher absolu · un état n'est jamais porté par
la couleur seule, il porte aussi une forme et un mot · l'ocre porte l'attente, jamais l'erreur · le
rouge est réservé à l'impayé et à l'absence non justifiée · une action non autorisée est absente de
l'écran, jamais grisée · un refus s'annonce avant la saisie et dit son versant positif · aucun
libellé métier en dur, ils viennent du country pack · aucun écran ne dit qu'un numéro est inconnu ·
aucun numéro de téléphone n'apparaît dans une liste, seulement dans le détail de sa propre saisie ·
aucun code personnel ni aucun code reçu n'est jamais affiché après saisie · les données de
démonstration sont celles du PRIMAIRE : CM1, maîtresse titulaire : jamais « 6e A » ni professeur de
matière.

Écris les fichiers de travail dans specs/003-connexion-contexte/design/ : un .dc.html par artboard,
plus canvas.json. Ils se versionnent ; le fichier assemblé, non. Reporte l'adresse du canvas publié
dans specs/003-connexion-contexte/spec.md, sous « Revue visuelle ».

Ne rien inventer hors de ces fichiers. Le but de cette planche est de rendre visible une dérive :
un écran, un état, un champ ou un mot qui n'existe pas dans le contrat, dans le domaine ou dans le
système de design doit sauter aux yeux.
```
