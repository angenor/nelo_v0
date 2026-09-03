# ADR 004 — Rust en façade, Python cantonné au sidecar IA

**Statut** : accepté · **Date** : 2026-08-21

> **Renversé par [ADR 017](017-fastapi-et-pydantic-remplacent-rust-et-actix.md) — cet ADR est devenu
> sans objet.** Son raisonnement reste vrai historiquement : tant que la façade était en Rust,
> cantonner Python à un sidecar était le bon arbitrage. **La façade étant elle-même FastAPI, le
> sidecar n'a plus de raison d'être** — les deux capacités du MVP sont un paquet du socle,
> `modules/socle/assistance/`. La propriété qui comptait ne disparaît pas : le produit reste
> pleinement opérationnel avec l'assistance suspendue par un réglage serveur, et c'est toujours un
> test. **Le corps ci-dessous n'est pas corrigé** : un journal de décisions ne se réécrit pas.

## Contexte

Le produit a besoin de Python : l'écosystème IA y vit. La question est de savoir *où* il vit.

Placer FastAPI en façade devant la logique métier est séduisant — un seul langage côté serveur,
l'écosystème IA à portée. C'est un mauvais choix ici, pour des raisons chiffrables : latence
supplémentaire par requête (sérialisation Python, GIL, boucle asyncio) là où Actix répond sous la
milliseconde ; empreinte mémoire d'un ordre de grandeur supérieure ; concurrence limitée par le GIL
sur les tâches CPU.

Sur des serveurs à ressources contraintes, avec un prix de vente par élève en francs CFA, chaque Mo de
RAM et chaque milliseconde ont un coût direct dans la marge.

## Décision

**Rust / Actix Web porte la totalité de la logique métier et de l'API.**

**Python vit dans un sidecar FastAPI, appelé en HTTP interne, uniquement pour les requêtes
d'inférence** — et ce sidecar est **optionnel au déploiement**.

## Conséquences

- **Un établissement peut tourner sans aucune fonctionnalité IA.** Ce n'est pas une intention, c'est
  un test : `docker compose stop sidecar-ia` doit laisser le produit pleinement opérationnel — les
  appréciations se saisissent à la main, l'import se fait par correspondance manuelle de colonnes.
- Le sidecar n'a **aucun accès à la base**. Il reçoit ce dont il a besoin dans la requête et renvoie
  une sortie. Il ne connaît ni le tenant, ni le schéma.
- Le coût d'inférence est suivi par tenant et par période. **Le coût par élève est un budget, pas un
  résultat.**
- Ce qui est déterministe ne passe jamais par un modèle de langage : calcul de moyennes, application
  de barèmes, relances d'échéance, contrôle de complétude, génération de bulletin. *Les faire passer
  par un modèle est plus lent, plus cher, moins fiable — et transforme une opération vérifiable en
  une opération à auditer.*

**Le prix accepté** : deux langages, donc deux chaînes de build et deux jeux de dépendances. Le
sidecar reste délibérément minuscule — une capacité par module, aucune logique métier — pour que ce
coût ne grandisse pas.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| FastAPI en façade | Latence, mémoire, GIL — sur une infrastructure contrainte et à prix bas, ce n'est pas un raffinement |
| Inférence appelée directement depuis Rust | Ferme l'écosystème Python, et rend l'IA non désactivable |
| Pas d'IA du tout | C1 et C5 ont une valeur réelle : l'appréciation de bulletin et l'import de fichiers désordonnés |
