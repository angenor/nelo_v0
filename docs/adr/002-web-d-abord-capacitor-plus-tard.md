# ADR 002 — Web d'abord, Capacitor dans une phase ultérieure

**Statut** : accepté · **Date** : 2026-08-21

## Contexte

Le produit est destiné au mobile : l'enseignant fait l'appel sur son téléphone, le parent consulte le
solde sur le sien. La question n'est pas *si* l'expérience doit être mobile, mais *par quel véhicule*.

Une application native — magasin d'applications, installation, mise à jour poussée — ajoute une
chaîne de build, deux processus de validation, un cycle de publication, et **un obstacle à l'adoption
côté parent** : un responsable légal qui doit installer une application depuis un magasin ne
l'installera pas.

## Décision

**Le MVP est une application web installable sur l'écran d'accueil.** Aspect et navigation
d'application native, rien à télécharger, aucune mise à jour à pousser.

**Capacitor enveloppera la même base Nuxt** le jour où l'un de ces besoins deviendra réel :
notifications natives fiables, caméra en usage intensif, présence dans les magasins d'applications
comme argument commercial, ou reprise du hors-connexion ([ADR 001](001-hors-connexion-differe.md)) —
les deux sujets arriveront probablement ensemble.

**Décision reportée, pas écartée.** Ce qui se pose maintenant pour que le report reste indolore :

- aucune dépendance à une API navigateur absente d'un WebView ;
- la navigation et les cibles tactiles dimensionnées pour le doigt dès le premier écran ;
- le stockage de session en cookie `HttpOnly`, qui fonctionne à l'identique dans un WebView.

## Conséquences

- Une seule chaîne de build, un seul déploiement, aucune validation de magasin.
- Un parent accède au produit par un lien SMS. C'est le chemin le plus court qui existe.
- Les notifications passent par le SMS et l'espace en ligne, jamais par une notification native.
- **Le poids de l'application est un indicateur produit** (porte P-10) : sur le web, chaque octet est
  téléchargé à chaque visite.

**Le prix accepté** : pas de notification push fiable côté parent avant Capacitor. C'est
précisément pourquoi le SMS est un canal de premier rang et non un repli —
[ADR 013](013-le-sms-est-un-canal-de-premier-rang.md).

## Alternatives écartées

| Alternative | Motif du refus |
|---|---|
| Native dès le départ | Deux chaînes de build, deux magasins, et un obstacle à l'adoption côté parent |
| Capacitor dès le MVP | Aucun besoin ne le justifie encore ; l'enveloppe s'ajoute quand le besoin existe |
| Tauri | Cible le poste de travail, pas le mobile |
