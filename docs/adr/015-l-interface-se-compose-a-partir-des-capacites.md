# ADR 015 — L'interface se compose à partir des capacités, jamais des rôles

**Statut** : accepté · **Date** : 2026-08-21

## Contexte

Il est tentant de livrer « l'interface du censeur », « l'interface de l'économe », « l'interface de
l'enseignant ». C'est faux dès le premier client.

La répartition des fonctions varie énormément d'un établissement à l'autre, **à segment identique**.
Dans un collège privé de 400 élèves, une seule personne tient la scolarité, la pédagogie et l'emploi
du temps. Dans un groupe scolaire de 3 000 élèves, ce sont trois personnes et parfois trois services
distincts.

Un produit qui impose un découpage fixe oblige le petit établissement à jongler entre plusieurs
comptes — **avec le partage de mots de passe qui s'ensuit** — et force le grand à accorder des droits
trop larges.

## Décision

**Il n'y a pas d'interface par rôle. Il y a un back-office unique dont la surface se compose à partir
des capacités effectives de la personne connectée.**

- Chaque service expose des **capacités nommées par verbe métier** : `scolarite.inscription.valider`,
  `evaluation.note.saisir`, `finance.encaissement.saisir`. Ordre de grandeur : 5 à 12 par service.
- Un **rôle** est un ensemble nommé de capacités, livré sous forme de **modèle préconfiguré par
  segment**, que l'établissement clone et ajuste **lui-même, sans intervention de l'éditeur**.
- Une **affectation** lie une personne à un rôle **et à un périmètre** — site, cycle, classes,
  matières, année. *Un rôle sans périmètre ne veut rien dire.*
- Les capacités effectives sont l'**union** des affectations. **Le cumul de rôles est le cas normal,
  pas l'exception.**

## Conséquences

- **Aucune liste de rôles n'est codée en dur côté front.** Le front compose sa navigation à partir de
  `GET /moi/capacites`. Sinon chaque nouveau modèle de rôle exigerait un déploiement.
- **Pas de menu grisé.** Un domaine n'apparaît que si la personne y détient au moins une capacité. Un
  menu visible mais inaccessible est du bruit et une invitation à réclamer des droits.
- **Une fiche élève unique**, dont les onglets varient : l'éducateur y voit la discipline, l'économe
  le solde, l'enseignant les notes de ses seules matières. Une fiche, plusieurs vues — jamais quatre
  écrans concurrents.
- **Un export n'est jamais une porte dérobée** vers ce que l'écran refuse d'afficher.
- **Le serveur reste la seule autorité** : l'interface masque, l'API refuse. Chaque appel revérifie la
  capacité **et** le périmètre.
- Les affectations sont rattachées à une année et **expirent avec elle**. À la bascule, une personne
  non reconduite voit un message clair, pas une interface vide.
- Une capacité introduite par une mise à jour **n'est jamais accordée automatiquement** : elle est
  proposée à l'administrateur de l'établissement, qui décide.

**Le prix accepté** : le cumul rend les tests combinatoires. On ne teste pas toutes les combinaisons
possibles mais un jeu de **personas** correspondant aux cumuls réellement observés chez les pilotes —
à collecter pendant la phase de découverte. C'est la raison pour laquelle « qui fait quoi, nommément ? »
est l'une des questions à poser aux cinq premiers établissements.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Une interface par rôle | Faux dès le premier client, et pousse au partage de comptes dans les petits établissements |
| Rôles fixes non modifiables par l'établissement | Chaque organisation différente devient une demande à l'éditeur |
| RBAC sans périmètre | *Un rôle sans périmètre ne veut rien dire* : un enseignant verrait les notes de toutes les classes |
| Ajouter l'ABAC plus tard | Un système de rôles fixes ne se transforme pas par ajout : il se remplace, et avec lui toutes les vérifications d'accès du produit |
