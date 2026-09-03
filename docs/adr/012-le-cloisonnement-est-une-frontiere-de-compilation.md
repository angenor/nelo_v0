# ADR 012 — Le cloisonnement est une frontière de compilation, pas une convention d'accès

**Statut** : accepté · **Date** : 2026-08-21

> **Amendé par [ADR 017](017-fastapi-et-pydantic-remplacent-rust-et-actix.md) — et c'est
> l'amendement le plus lourd du corpus.** **En Python, il n'y a pas de frontière de compilation** :
> un `import` traversant s'exécute parfaitement. Le titre et le corps de cet ADR restent, et son
> intention aussi ; la garantie, elle, devient une **frontière d'import vérifiée par la porte
> P-11**. **Un compilateur refusait, un test signale — c'est plus faible, et il faut le dire.** En
> compensation, P-11 tient trois verrous là où elle n'en avait qu'un : aucun paquet ne déclare
> `protection` dans ses dépendances · un test de graphe d'imports échoue si un `import` traversant
> est introduit, **y compris différé au fond d'une fonction** ·
> `modules/metier/protection/__init__.py` n'expose rien hors de son interface de service. Les
> niveaux 2 et 3 de la décision — refus de configuration, attribution nominative — sont
> **inchangés**, et ne dépendaient d'aucun langage.

## Contexte

Certaines données sortent du système de rôles : dossier médical et infirmerie, dossier psychosocial,
signalements de protection de l'enfance, dossier disciplinaire en cours d'instruction, éléments de
paie individuels.

Un système d'habilitations classique les traiterait comme n'importe quelle autre capacité : un code de
plus dans un modèle de rôle. **Cela suffirait à ce qu'un jour, quelqu'un ajoute
`protection.signalement.consulter` au rôle « Direction » pour dépanner** — et ouvre le dossier
psychosocial de tous les élèves de l'établissement.

C'est le domaine où une erreur de conception a les conséquences les plus graves, humaines comme
juridiques.

## Décision

**Le cloisonnement est structurel, à trois niveaux :**

1. **Frontière de compilation.** Le crate `modules/protection/` n'est référencé par **aucun** autre
   crate. Un module qui pourrait lire un signalement finirait par le lire. Porte P-11.
2. **Refus de configuration.** Une capacité portant `cloisonnee = true` **échoue** si on tente de
   l'ajouter à un modèle de rôle — `HAB_CAPACITE_CLOISONNEE_NON_ROLABLE`. Ce refus ne se contourne par
   aucun réglage.
3. **Attribution nominative.** Ces capacités s'accordent une personne à la fois, avec motif, date de
   fin obligatoire et traçabilité.

**Et une garantie qui sert de test à toute la couche** : *un chef d'établissement n'a pas accès par
défaut au contenu d'un signalement qui le concerne.*

## Conséquences

- Toute route du bloc `PRO_` écrit dans `journal_acces` — **y compris en lecture, y compris en cas de
  refus**. C'est la seule famille de routes où le refus lui-même est une donnée.
- Un accès anormal alerte le responsable.
- `POST /signalements` **n'exige aucune capacité** : tout membre du personnel peut signaler, y compris
  de façon confidentielle (`auteur_id` nullable). C'est délibéré, et c'est la raison d'être du
  registre.
- La politique de conservation de ces données est distincte de celle du dossier scolaire.
- **Une exception délibérée** : la fiche d'urgence et les allergies sont accessibles au personnel
  encadrant, et imprimables par classe. *Un choc anaphylactique ne se traite pas en demandant une
  habilitation.*
- Le circuit est humain et nommé : un référent désigné, des délais, une escalade vers la direction
  puis vers les autorités compétentes. L'IA peut au mieux alerter une personne nommée — jamais
  qualifier, jamais décider, jamais notifier une famille.

**Le prix accepté** : la frontière de compilation interdit à un tableau de bord d'afficher « trois
signalements en cours » à côté des autres indicateurs. Il faudrait une route dédiée, appelée avec un
accès nominatif. **C'est un inconfort réel, et il est le point.**

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Traiter le cloisonnement comme une capacité ordinaire | Un ajout à un rôle largement distribué ouvre tout |
| Chiffrer sans cloisonner l'accès | Le chiffrement protège du vol de base, pas de l'accès légitime abusif |
| Un module séparé, mais référencé par le tableau de bord | La dépendance existe alors, et la frontière n'est plus vérifiable mécaniquement |
