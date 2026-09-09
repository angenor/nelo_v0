# ADR 002 — Web d'abord, Capacitor dans une phase ultérieure

**Statut** : accepté, **amendé le 2026-09-05** · **Date** : 2026-08-21

> **Amendement du 2026-09-05 — la PWA est la cible.** La décision tient — web d'abord, aucune chaîne
> native au MVP — mais son énoncé est précisé : l'application web installable **n'est pas un confort
> en attendant du natif, c'est la cible**. C'est elle que Capacitor (mobile) et Tauri (poste du
> back-office) empaqueteront ensuite, sans réécriture. **Tauri n'est plus écarté : il est différé,
> comme Capacitor.** Les provisions que le MVP livre pour cela sont en fin de fichier.

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
| Tauri dès le MVP | Il viendra pour le poste du back-office — le censeur, l'économe — après Capacitor ou avec lui, jamais avant qu'un besoin existe. Qu'il cible le poste et non le mobile n'est plus un motif d'exclusion : la PWA sert les deux, et chaque coquille prend la sienne |

## Amendement du 2026-09-05 — la PWA est la cible

Le texte d'origine présentait l'application web installable comme un point de départ, et Capacitor
comme la seule enveloppe possible. L'arbitrage du portefeuille est plus précis : **la PWA est la
cible.** Elle n'est pas un confort en attendant une application native — c'est le socle que les
coquilles natives empaqueteront, **sans réécriture** :

- **Capacitor** pour le mobile — l'enseignant en classe, le parent ;
- **Tauri** pour le poste — le censeur ou l'économe au back-office, celui que la contrainte 6 du brief
  désigne comme administrateur de fait.

Ni l'un ni l'autre n'entre au MVP. Aucune chaîne de build native, aucun magasin. Ils viennent le jour
où un besoin réel les justifie — notifications natives, caméra en usage intensif, présence en magasin
comme argument commercial, reprise du hors-connexion — et Tauri après Capacitor ou avec lui, pas
avant.

**Ce que le MVP livre pour que l'empaquetage reste indolore** :

| Provision | Ce qu'elle exige |
|---|---|
| **PWA complète et installable** sur Chromium et WebKit | Manifeste, icônes, `display: standalone`. L'installation depuis le navigateur est un parcours vérifié, pas un effet de bord |
| **Aucune dépendance à la barre d'adresse ni à un rechargement manuel** | Toute navigation et toute reprise passent par l'application elle-même : une coquille n'a ni barre d'adresse, ni bouton de rechargement |
| **Les capacités de plateforme passent par une interface unique côté client** | Caméra, notifications, état du réseau, stockage : un seul point d'appel, **une seule implémentation — web**. Capacitor et Tauri en fourniront chacun une seconde sans toucher à un écran |
| **Service worker mince** | Sans logique métier, sans cache d'écriture, sans file de synchronisation — le hors-connexion reste différé ([ADR 001](001-hors-connexion-differe.md)) |

Les trois provisions d'origine — aucune API absente d'un WebView, cibles tactiles dimensionnées pour
le doigt, session en cookie `HttpOnly` — restent en vigueur ; les quatre ci-dessus s'y ajoutent. La
tranche **T0b** porte la coquille installable et l'interface de plateforme.

**Ce qui ne change pas** : le SMS reste le canal de premier rang
([ADR 013](013-le-sms-est-un-canal-de-premier-rang.md)), il n'y a toujours pas de notification push
fiable côté parent avant Capacitor, et le poids de l'application reste un indicateur produit
(porte P-10).
