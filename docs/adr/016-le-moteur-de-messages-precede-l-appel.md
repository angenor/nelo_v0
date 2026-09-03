# ADR 016 — Le moteur de messages précède l'appel

**Statut** : accepté · **Date** : 2026-08-21 · **Décision d'ordre, pas de découpage**

## Contexte

L'ordre naturel d'une roadmap scolaire place l'appel de séance tôt : c'est l'écran le plus visible, le
plus démontrable, et celui qui décide de l'adoption. La communication, elle, ressemble à de
l'infrastructure — un sujet qu'on branche quand le métier existe.

Cet ordre est faux ici, et il coûte deux fois.

## Décision

**T4a — le moteur de messages, le routage et le budget — est construit AVANT T5, l'appel.**

Rang 9 pour le moteur, rang 10 pour l'appel. Les deux tranches restent séparées : elles n'ont ni le
même mode de défaillance ni la même méthode de test.

## Conséquences

**Ce que la décision reconnaît** : un appel sans message court n'est pas un demi-produit, **c'est un
autre produit**. Une feuille de présence numérique remplace une feuille de papier — sans plus. Ce qui
fait acheter, c'est que la famille sache que l'enfant est absent **avant midi**, et le délai entre
l'absence et le message est l'un des sept indicateurs du brief.

**Ce que l'ordre inverse coûterait** :

| Coût | Détail |
|---|---|
| Un chemin de notification provisoire | Écrit pour la démonstration, puis remplacé — donc écrit deux fois |
| Une démonstration sans son argument | On montre pendant des semaines un produit privé de ce qui le vend |
| Un budget découvert tard | Le coût par message et le regroupement en récapitulatif changent le dessin de l'écran d'appel : combien d'événements il produit, et lesquels |
| Une politique de routage rétro-ajustée | Elle décide de quel événement part sur quel canal. La brancher après, c'est reprendre les événements déjà émis |

**Ce qui rend la décision tenable** : la porte est déjà posée. L'abstraction de la passerelle de
messages et son implémentation simulée existent depuis T0a ; T4a **remplace** la simulation, il ne la
découvre pas.

**Le prix accepté** : le produit ne montre aucun écran de classe avant sa dixième tranche. C'est long,
et c'est visible dans une démonstration intermédiaire. Les neuf premières tranches posent ce sans quoi
l'écran de classe serait à refaire — et refaire l'écran d'appel, c'est refaire l'écran le plus
contraint du produit.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| L'appel d'abord, le message ensuite | Écrit deux fois le chemin de notification, et démontre un produit sans son argument de vente |
| Fusionner les deux tranches | Deux natures de risque — l'ergonomie sous réseau instable et le coût d'un tiers facturé à l'envoi — dans un seul point de validation |
| Un message court « en dur » pour l'appel, le moteur plus tard | C'est exactement le chemin provisoire que la décision évite. Et un modèle de message non vérifié à l'enregistrement coûte deux messages par famille |
