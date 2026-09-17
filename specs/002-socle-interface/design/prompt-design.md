# Prompt de revue visuelle — forme A — T0b Le socle d'interface

*Cette tranche produit des écrans qu'une personne regarde. On lance `/design` en session dédiée,
après `specify` et avant `plan`. Gabarit : [docs/05-design.md § Forme A](../../../docs/05-design.md).
Particularité de cette tranche : l'artboard de la page de style (US1) est la **planche de style
transverse** — ses sources vont dans `docs/design/canvas/`, pas ici.*

```text
/design Représente les user stories de specs/002-socle-interface/spec.md pour la tranche T0b — Le
socle d'interface.

Un artboard par user story, nommé par son identifiant, huit artboards :
  US1 — la page de style : les quatorze composants, chacun dans tous ses états, chaque état deux
        fois côte à côte, conteneur clair et conteneur sombre. C'est la planche de style transverse
        du produit, celle que toutes les tranches citeront comme référence de facture.
  US2 — le ruban d'état de saisie dans ses trois états — « Tout est enregistré », « Envoi en
        cours », « Hors ligne » — ancré en bas d'un écran de saisie de démonstration à 390 px, avec
        le champ qui continue d'accepter la saisie sous les trois états. Rouge interdit : la coupure
        est ocre.
  US3 — la coquille dans ses quatre situations : mono-domaine (l'accueil EST le domaine), cinq
        domaines à plat, sept domaines regroupés par famille, aucune capacité (le message nomme
        l'administrateur, avec son téléphone, et propose « Demander mes accès »). Chaque situation à
        390 px ET à 1200 px. Aucun menu grisé nulle part.
  US4 — un flux de gauche à droite : installation depuis Chromium et depuis WebKit, ouverture en
        affichage autonome sans barre d'adresse, parcours accueil → domaine → à propos → retour sans
        rechargement, et la mise à jour qui s'applique d'elle-même. À côté, un diagramme de
        l'interface unique de plateforme — réseau, stockage, caméra, notifications — avec son unique
        implémentation web, et les deux implémentations futures (Capacitor, Tauri) en pointillé.
  US5 — le même écran de coquille en fr et en en, et une troisième colonne avec un pack fictif où
        « classe » se dit autrement : ce qui change est surligné, ce qui vient d'une clé
        d'interface et ce qui vient du pack sont distingués.
  US6 — un diagramme de la mesure de poids : l'écran déclare son plafond, un vrai navigateur
        mesure, la porte P-10 échoue au dépassement en nommant écran, plafond, mesure ; le test
        négatif à 300 Ko en pointillé ; l'atterrissage de la coquille budgété à 120 Ko.
  US7 — un diagramme de la chaîne de vérification : sept portes serveur puis P-05, P-06, P-10 ;
        P-05 ouvre Chromium et WebKit, en clair et en sombre ; sortie en échec au premier rouge ;
        pour chaque porte d'interface, son test négatif en pointillé.
  US8 — la ligne de tableau à 390 px (carte, libellé au-dessus de la valeur), 768 px et 1200 px ;
        les cibles tactiles 52 / 48 / 44 cotées ; un composant avec et sans survol pour montrer que
        rien ne se révèle au survol.

À lire avant de dessiner, et à ne pas dépasser :
- docs/02-domaine.md, sections 0, 3.4 et 15 — les règles de composition et les codes neutres
- docs/03-api.md, sections 1.2, 1.4 et 1.9 — les en-têtes, les formats et le contexte qui compose
  l'interface (avec l'administrateur de l'établissement)
- docs/design/theme.css — les jetons, seule source des couleurs
- docs/design/ecrans/13_systeme-de-design.html — les quatorze composants et leurs états
- docs/design/ecrans/06_navigation-composee.html — le shell composé, quatre rattachements
- docs/design/ecrans/ — les douze écrans maquettés, référence de facture
- docs/05-design.md — la synthèse, la langue et les règles d'écran
- docs/adr/002-web-d-abord-capacitor-plus-tard.md — la PWA est la cible

Contraintes non négociables : mobile-first mais responsive · mode clair ET mode sombre, les deux ·
52 px de cible tactile en classe, 48 ailleurs, 44 en plancher absolu · un état n'est jamais porté par
la couleur seule, il porte aussi une forme et un mot · l'ocre porte l'attente, jamais l'erreur · le
rouge est réservé à l'impayé et à l'absence non justifiée · une action non autorisée est absente de
l'écran, jamais grisée · un refus s'annonce avant la saisie et dit son versant positif · aucun
libellé métier en dur, ils viennent du country pack · les chiffres qui s'empilent sont tabulaires ·
les montants avec l'espace fine insécable · tout écran de saisie porte le ruban d'état · rien n'est
masqué derrière un survol · les données de démonstration sont celles du PRIMAIRE — CM2, maître
titulaire, conseil des maîtres — jamais « 6e B » ni professeur de matière.

Écris les fichiers de travail ainsi : l'artboard US1 (la planche de style) dans docs/design/canvas/,
les sept autres dans specs/002-socle-interface/design/ ; un .dc.html par artboard, plus canvas.json.
Ils se versionnent ; le fichier assemblé, non. Reporte l'adresse du canvas publié dans
specs/002-socle-interface/spec.md, sous « Revue visuelle ».

Ne rien inventer hors de ces fichiers. Le but de cette planche est de rendre visible une dérive :
un composant, un état ou un mot qui n'existe pas dans le système de design ou dans le domaine doit
sauter aux yeux.
```
