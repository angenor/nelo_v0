# ADR 014 — La localisation passe par le country pack, jamais par une branche de code

**Statut** : accepté · **Date** : 2026-08-21

## Contexte

La séquence de déploiement est délibérée : Côte d'Ivoire, puis l'Afrique de l'Ouest et Centrale
francophone (même monnaie, même droit comptable, même référentiel du supérieur), puis l'Afrique
anglophone.

**Le passage au monde anglophone n'est pas une traduction : c'est un changement de modèle
d'évaluation.** Si le socle n'est pas conçu dès le départ pour l'absorber, la troisième vague sera une
réécriture.

Et le risque ne se manifeste pas d'un coup : il commence par un `if pays == "CI"` écrit pour dépanner,
qui se multiplie.

## Décision

**Un `country_pack` est un ensemble de données de référence versionnées, chargé au provisionnement
d'un tenant. Aucune logique métier ne dépend du pays autrement que par ce pack.**

Contenu : structure des cycles et niveaux avec libellés `fr`/`en` · découpage de l'année · référentiel
d'évaluation ([ADR 010](010-le-referentiel-d-evaluation-est-une-donnee-versionnee.md)) · examens
officiels et calendrier · séries et filières · plan comptable et régime fiscal · opérateurs de
paiement · autorité de protection des données et formalités · ministères de tutelle et formats de
remontée · devise et son exposant, formats de date et de téléphone, langues · **vocabulaire métier**.

**Le vocabulaire visible n'est jamais une littérale.** Chaque entité de référentiel porte un `code`
neutre et stable — `CLASSE`, `PERIODE`, `PROFESSEUR_PRINCIPAL` — et ses libellés viennent du pack.

## Conséquences

- **La porte P-09 est mécanique** : aucune littérale `CI`, `XOF`, `BEPC`, `trimestre`, `SYSCOHADA`,
  `CNPS`, `ARTCI` dans `domaine/` ni `socle/` ; aucune borne d'échelle en dur ; aucun `match pays`
  dans le moteur de calcul.
- Le **test d'agnosticité** est permanent : un country pack fictif — un cycle, un niveau, une échelle
  sur 10, deux périodes — fonctionne de bout en bout. *S'il tombe, le pays s'est glissé dans la
  logique sans qu'on le voie.*
- Un pack est versionné et jamais modifié en place. Le changement de version est explicite et
  journalisé, jamais implicite au déploiement.
- Une entité qui existe dans un pack et pas dans un autre **ne crée aucune colonne conditionnelle** :
  elle vit dans le `contenu` JSONB, ou elle n'existe pas.
- Le code, les commentaires et la documentation restent en français ; ce sont les **libellés
  utilisateur** qui naissent en `fr` et `en` ensemble.

**Le prix accepté** : écrire une règle en donnée coûte plus cher que l'écrire en code, à chaque fois.
Un développeur pressé écrira toujours plus vite `if pays == "CI"`. C'est pourquoi la porte P-09 existe
et pourquoi elle est mécanique : **la discipline seule ne tient pas trois ans.**

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Une branche de code par pays | Se multiplie, ne se retire jamais, et rend chaque correction à faire N fois |
| Un déploiement par pays | Multiplie l'infrastructure et les migrations pour un développeur seul |
| Localiser après le premier pays | *Le passage à l'anglophone est un changement de modèle, pas une traduction.* Rattraper coûte une réécriture |
