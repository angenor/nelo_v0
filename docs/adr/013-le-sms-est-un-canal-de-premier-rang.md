# ADR 013 — Le SMS est un canal de premier rang, pas un repli

**Statut** : accepté · **Date** : 2026-08-21

## Contexte

Une part significative des responsables légaux, en particulier hors d'Abidjan, dispose d'un téléphone
basique ou d'un smartphone sans forfait data actif. Un produit dont la notification d'absence passe
par une notification push n'atteint pas ces familles — c'est-à-dire une partie substantielle de la
clientèle de l'établissement.

Le SMS est aussi le **poste de coût majeur** du modèle économique. Les deux faits sont vrais
simultanément, et c'est ce qui rend la conception difficile.

## Décision

**Le SMS est un canal de premier rang.** Trois conséquences de modèle, pas d'interface :

1. **Chaque type de message porte une variante par canal, rédigée séparément.** *Un SMS n'est pas un
   push tronqué.* La variante SMS tient sous 160 caractères, et la longueur est vérifiée **à
   l'enregistrement du modèle, pas à l'envoi** — découvrir à 7 h du matin qu'un modèle dépasse coûte
   deux SMS par famille.
2. **Une politique de routage par établissement** : quel événement part sur quel canal, pour quel
   profil de destinataire, avec quel budget mensuel et quelle fenêtre horaire.
3. **Un budget SMS paramétrable, vérifié avant l'envoi**, avec alerte de dépassement et facturation à
   l'établissement au coût réel majoré — poste distinct de l'abonnement.

## Conséquences

- **Le SMS unitaire est réservé aux événements réellement critiques** : absence non justifiée,
  convocation, échéance dépassée. Le reste passe par l'espace en ligne, WhatsApp ou le papier.
- **Les notifications non urgentes se regroupent en un récapitulatif périodique** — un seul message
  hebdomadaire au lieu d'un SMS par événement. Sans ce regroupement, le modèle économique ne tient
  pas.
- Les fenêtres d'envoi respectent les heures ouvrables et les jours de repos.
- L'**avis de situation imprimé**, remis à l'élève ou disponible à l'accueil, couvre le besoin de
  situation complète sans coûter un SMS.
- Le **SMS entrant par mot-clé** — `SOLDE`, `ABSENCE` — est reporté en V2, mais conçu dès maintenant :
  numéro long virtuel fourni par l'agrégateur, contrôle d'accès **par le numéro appelant**, réponse
  automatique sous 160 caractères, et **réponse générique sans donnée personnelle à un numéro
  inconnu**.

**Le prix accepté, et il est lourd** : sans consultation gratuite en libre-service au MVP,
l'information circule surtout en flux sortant, donc **à la charge de l'établissement**. Le
regroupement et le routage restrictif compensent en partie. C'est la première raison pour laquelle le
SMS entrant est prioritaire en V2.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Notification push comme canal principal | N'atteint pas les familles sans smartphone ni data — c'est-à-dire celles qu'il faut atteindre |
| WhatsApp seul | Dépend de la data, et le coût par conversation n'est pas plus faible |
| SMS pour tout | Modèle économique intenable ; le coût unitaire tue la marge |
| Code court opérateur | Se négocie avec chaque opérateur ; un numéro long virtuel s'obtient auprès de l'agrégateur sans négociation |
