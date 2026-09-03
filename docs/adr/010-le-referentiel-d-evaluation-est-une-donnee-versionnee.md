# ADR 010 — Le référentiel d'évaluation est une donnée versionnée, pas du code

**Statut** : accepté · **Date** : 2026-08-21 · **Décide de la viabilité de l'extension régionale**

> **Amendé par [ADR 017](017-fastapi-et-pydantic-remplacent-rust-et-actix.md)** — la décision est
> intacte, et elle ne dépendait d'aucun langage. Lire « pas une fonction Rust par pays » comme « pas
> une fonction de calcul écrite par pays » : le moteur est un interpréteur de formules déclaratives,
> il vit dans `domaine/`, sans E/S, et aucune branche n'y est conditionnée par le pays.

## Contexte

Le modèle francophone et le modèle anglophone d'évaluation sont irréconciliables si le calcul est codé
en dur :

| Dimension | Francophone | Anglophone |
|---|---|---|
| Échelle | Note sur 20 | Pourcentage sur 100 |
| Restitution | Moyenne pondérée par coefficient | Grade code A1 à F9, C4-C6 valant *credit* |
| Découpage | Trimestres ou semestres | *Three terms* |
| Composition | Devoirs + compositions | *Continuous assessment* 30 % + examen externe 70 % |
| Classement | Rang, moyenne générale | *Position in class*, par matière et globale |

Et une contrainte transverse, indépendante du pays : **un bulletin réédité trois ans plus tard doit
refléter le barème de l'époque**, pas le barème courant.

## Décision

**Le référentiel d'évaluation est une entité versionnée par pays et par année**, contenant :

- l'échelle de notation et ses bornes ;
- la table de conversion note → mention, le cas échéant ;
- la formule de composition de la note périodique — **un arbre de calcul déclaratif, pas du code** ;
- les règles d'arrondi ;
- les règles de rang, d'ex æquo et de mention ;
- le gabarit de bulletin associé.

**Le moteur de calcul est un interpréteur de formules déclaratives, pas une fonction Rust par pays.**
Il vit dans `domaine/`, sans E/S, et ne contient aucun `match pays`.

**Toute moyenne calculée porte la version du référentiel qui l'a produite** et est recalculable à
l'identique.

## Conséquences

- Un nouveau pays est une **donnée**, pas un déploiement.
- Un changement de barème en cours d'année crée une nouvelle version ; les bulletins déjà publiés
  restent exacts.
- **Les règles d'arrondi sont écrites et versionnées.** Elles sont une source majeure de contestation,
  et une convention implicite du langage n'est pas défendable devant un parent.
- Une route de simulation permet de rejouer une formule sur un jeu d'essai avant publication.
- Un référentiel publié est figé (`EVA_REFERENTIEL_FIGE`) : on en crée une version, on ne le modifie
  pas.

**Le prix accepté** : un interpréteur de formules est plus lent et plus complexe à écrire qu'une
fonction de moyenne pondérée — quelques centaines de lignes contre une dizaine, et un langage
d'expression à concevoir et à documenter. **C'est cher, et c'est payé une seule fois.** Coder la
moyenne sur 20 en dur, c'est condamner l'extension anglophone à une réécriture du module
d'évaluation, du bulletin et de tous les bulletins archivés.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Une fonction de calcul par pays | Chaque nouveau pays devient un déploiement, et le code double |
| Barème sur 20 en dur, conversion au moment de l'affichage | Ne couvre ni le *continuous assessment*, ni les *grade codes*, ni les règles de rang |
| Un moteur de règles existant | Dépendance lourde, souvent copyleft, pour un besoin de quelques dizaines d'opérateurs |
| Formules en code, référentiel en donnée | Le point dur est la formule, pas l'échelle. La moitié de la solution ne résout rien |
