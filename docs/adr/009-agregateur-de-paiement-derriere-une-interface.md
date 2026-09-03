# ADR 009 — L'agrégateur de paiement derrière une interface interne, dès le premier jour

**Statut** : accepté · **Date** : 2026-08-21

## Contexte

Le paiement est mobile money, pas carte bancaire : Wave, Orange Money, MTN MoMo, Moov. Les agrégateurs
centralisent ces opérateurs en une seule API — CinetPay est le plus utilisé en Côte d'Ivoire, PayDunya
couvre plusieurs marchés d'Afrique de l'Ouest et du Centre.

Le choix « agrégateur contre intégration directe » est une décision d'architecture structurante. Il ne
se tranche pas définitivement aujourd'hui : sur de gros volumes, l'intégration directe devient
rentable, et les conditions commerciales d'un agrégateur changent.

## Décision

**Démarrer via un agrégateur, mais isoler l'agrégateur derrière une interface interne dès le premier
jour.**

Le module `finance` connaît un trait — initier, confirmer, rembourser, réconcilier — et rien de plus.
Aucune structure de données de l'agrégateur ne traverse cette frontière.

**Les exigences non négociables du module de paiement**, indépendantes de l'agrégateur :

| Exigence | Raison |
|---|---|
| **Idempotence stricte** des initiations **et des webhooks** | Les confirmations arrivent en retard, en double, ou jamais |
| **Machine à états explicite** — `initié → en attente → confirmé / échoué / expiré / remboursé` | Sans elle, un paiement en attente et un paiement échoué se confondent |
| **Réconciliation quotidienne automatique** | L'écart entre le journal de la plateforme et le relevé de l'opérateur : **c'est là que naissent les litiges** |
| **Encaissement espèces avec caisse et arrêté quotidien** | Une part majoritaire des paiements reste en espèces |
| **Reçu numéroté, séquentiel, infalsifiable** | Exigence comptable et culturelle |
| **Aucun paiement supprimable** | Annulation par écriture inverse uniquement |

## Conséquences

- Changer d'agrégateur, ou en ajouter un second, ne touche pas la logique métier.
- Il n'existe **aucune route `DELETE` sur un paiement**. `FIN_PAIEMENT_NON_SUPPRIMABLE` est le refus
  explicite qui rend la règle testable.
- La séquence des reçus est vérifiée : une séquence trouée est une anomalie signalée, pas une
  curiosité.
- Le multi-devises — XOF, XAF, GHS, NGN, KES — vit dans le country pack, avec l'exposant de la devise.

**Le prix accepté** : une couche d'indirection en plus, et la nécessité d'écrire une simulation
complète de l'agrégateur pour le développement local. C'est le prix de ne pas être prisonnier d'un
fournisseur sur le poste de revenu le plus critique du produit.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Intégration directe aux quatre opérateurs | Quatre intégrations, quatre contrats, quatre jeux de webhooks — hors de portée d'un développeur seul |
| Agrégateur appelé directement depuis les handlers | Rend le changement d'agrégateur équivalent à une réécriture du module financier |
| Carte bancaire seule | Inutilisable sur le marché cible |
