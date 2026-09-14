# Prompt de revue visuelle — forme B — T0a Le socle serveur

*Cette tranche ne produit aucun écran. On ne lance pas `/design`. On lance ce bloc en session
dédiée, après `specify` et avant `plan`, et il écrit un seul fichier : `diagrammes.md`, à côté de
celui-ci. Gabarit : [docs/05-design.md § Forme B](../../../docs/05-design.md).*

```text
Produis la planche de diagrammes de la tranche T0a — Le socle serveur, à partir de
specs/001-socle-serveur/spec.md.

Pas d'écran dans cette tranche : ne dessine aucune interface, n'ouvre ni le fichier de composants,
ni le dossier d'écrans, ni le lexique. Aucun mode sombre, aucune cible tactile, aucun jeton de
couleur — ce sont des diagrammes, pas des maquettes.

Écris UN SEUL fichier : specs/001-socle-serveur/design/diagrammes.md, composé de blocs mermaid
séparés par un titre de niveau 2 et une phrase qui dit ce que le diagramme rend visible.

Cinq diagrammes, pas un de plus. Pour chacun : sa grammaire, ce qu'il montre, et les user stories
qu'il couvre.
  1. graph LR — la hiérarchie des paquets domaine, shared, socle, metier, segments, api, avec les
     arêtes autorisées en trait plein et les DEUX arêtes interdites en pointillé, chacune portant
     la porte qui la refuse (P-04 : socle → metier ; P-11 : n'importe quoi → protection) —
     couvre US4
  2. sequenceDiagram — une écriture sur le module doré, de la requête à la réponse : en-tête
     d'identifiant de requête, résolution du tenant, variable de tenant posée dans la
     transaction, validation de schéma (refus VAL_ avant toute règle), refus métier TEN_,
     écriture de la valeur ET de l'événement dans la même transaction, mémorisation de la
     réponse, puis le rejeu identique et le rejeu divergent — couvre US1, US2, US3
  3. stateDiagram-v2 — le cycle de vie d'un événement de la table d'événements : écrit dans la
     transaction, en attente, pris par le travailleur, traité, ou en échec puis repris — jamais
     perdu, possiblement livré deux fois — couvre US3
  4. graph LR — la chaîne de vérification scripts/verifier.sh : les sept portes P-01, P-02, P-03,
     P-04, P-07, P-11, P-12 dans l'ordre d'enchaînement, la sortie en échec explicite au premier
     rouge, et pour chaque porte le test négatif qui la casse, en pointillé — couvre US5
  5. graph LR — les trois dépendances externes derrière leur abstraction : passerelle de messages
     courts, agrégateur de paiement, service d'inférence, chacune avec sa simulation active par
     défaut et ses quatre modes (accusé en retard, en double, jamais reçu, indisponible → 503) ;
     et, à côté, le paquet d'assistance dans le socle, suspendu par le réglage du catalogue —
     couvre US6, US7

À lire avant, et à ne pas dépasser : specs/001-socle-serveur/spec.md, docs/01-stack.md § 2.4,
§ 2.5 et § 7, docs/03-api.md § 1.3, § 1.6 et § 1.8, docs/02-domaine.md § 0 et § 1.

Ne rien inventer hors de ces fichiers. Le but est de rendre visible une dérive : une entité, une
étape ou un contrôle qui n'existe pas dans le corpus doit sauter aux yeux. Aucune prose hors des
phrases d'introduction.
```
