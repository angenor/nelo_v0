# ADR 000 — Nuxt et Rust, un seul dépôt, une seule application

**Statut** : accepté · **Date** : 2026-08-21

> **Amendé par [ADR 017](017-fastapi-et-pydantic-remplacent-rust-et-actix.md)** — le monolithe est
> en FastAPI, plus en Rust. **La décision de cette note n'est pas touchée** : une application Nuxt,
> un monolithe, un seul dépôt, six surfaces composées à partir des capacités. Seule la langue du
> serveur change. Lire « monolithe Rust » comme « monolithe ».

## Contexte

Le produit doit servir six surfaces qui n'ont ni le même appareil, ni le même réseau, ni le même
besoin : le téléphone d'un enseignant en salle de classe, la tablette de saisie de notes, le poste de
l'économe, le portail d'un parent sur un appareil d'entrée de gamme, le portail d'un élève, et la
console de l'éditeur.

La tentation est d'en faire six applications. Elle est mauvaise pour un développeur seul : six bases
de code, six chaînes de build, six déploiements, et surtout **six endroits où la même règle métier
peut diverger**.

## Décision

**Une application Nuxt 4, un monolithe Rust, un seul dépôt.**

Les six surfaces sont des **compositions de la même interface**, produites par les capacités
effectives de la personne connectée. Une personne cumulant deux rôles voit une seule interface
réunissant les deux — voir [ADR 015](015-l-interface-se-compose-a-partir-des-capacites.md).

Le monolithe n'expose que des API ; le front-end est entièrement découplé. La seule exception est le
rendu des documents, produit côté serveur — la mise en page d'un bulletin ne peut pas dépendre du
terminal de l'utilisateur.

## Conséquences

- Le back-office, le portail parent et le portail élève partagent leurs composants, leurs jetons de
  design et leur client d'API généré.
- Un changement de règle métier se fait à un endroit.
- **La stratégie de rendu diffère par surface** : statique pour le site public, rendu serveur pour les
  portails, rendu client pour le back-office. C'est une hypothèse de travail, notée dans
  [progress.md](../progress.md).
- Le budget de poids devient un indicateur produit suivi par écran (porte P-10) : dans une base
  unique, rien n'empêche mécaniquement une dépendance du back-office d'atterrir dans l'écran d'appel.

**Le prix accepté** : un bundle unique demande une discipline de découpage — chargement différé par
route, aucun import transversal paresseux. Sans elle, l'écran le plus léger porte le poids du plus
lourd. C'est exactement ce que P-10 mesure.

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Une application par profil | Six bases de code pour un développeur seul, et six endroits où une règle diverge |
| Next.js / React | Le design system existant est en HTML et CSS purs, sans framework ; l'écart d'écriture entre les deux est nul ici |
| Rendu serveur de l'interface par Rust | Perd la composition dynamique par capacités, et impose une chaîne de gabarits en plus |
