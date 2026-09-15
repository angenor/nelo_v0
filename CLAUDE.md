# Nelo

Plateforme de gestion pour établissements scolaires. Pilote : établissements privés d'Abidjan,
Côte d'Ivoire — **par le cycle primaire, seul segment du MVP**
([ADR 018](docs/adr/018-le-mvp-commence-par-le-primaire.md)). Backend FastAPI/Pydantic, application
Nuxt 4 mobile-first, assistance IA **intégrée au socle et désactivable par réglage**, PostgreSQL,
Valkey, Garage.

**Toute la documentation est dans [`docs/`](docs/). Lis ce dont tu as besoin, ne devine pas.**

| Fichier | Quand le lire |
|---|---|
| [docs/00-brief.md](docs/00-brief.md) | Comprendre le problème, les objectifs et surtout **ce qui est hors périmètre** |
| [docs/01-stack.md](docs/01-stack.md) | Structure du dépôt, commandes, hiérarchie des paquets, portes de vérification |
| **[docs/02-domaine.md](docs/02-domaine.md)** | **Source de vérité** — entités, relations, invariants, machines à états |
| **[docs/03-api.md](docs/03-api.md)** | **Source de vérité** — conventions, ressources, codes d'erreur |
| [docs/04-roadmap.md](docs/04-roadmap.md) | Onze epics, **vingt-et-une tranches**, chacune en prompt `/speckit-specify` prêt à coller |
| [docs/05-design.md](docs/05-design.md) | Jetons, quatorze composants, langue, règles d'écran |
| [docs/06-apres-mvp.md](docs/06-apres-mvp.md) | **Fermé — ne pas lire pendant le MVP.** Les segments, pays et modules futurs, leur ordre, leur coût. Pour l'humain qui arbitre, jamais pour coder une tranche |
| [docs/progress.md](docs/progress.md) | **Où on en est, et ce qui attend une réponse.** À ouvrir en arrivant |
| [docs/adr/](docs/adr/) | Les décisions et leur motif |

## Sources de vérité projet

`docs/02-domaine.md` et `docs/03-api.md` font foi au niveau projet.

Toute phase de planification **doit** :

- lire ces deux fichiers avant de produire un modèle ou un contrat local ;
- en **dériver**, jamais inventer une entité ou un endpoint ;
- si un changement est nécessaire, le proposer comme **diff explicite sur le fichier projet AVANT de
  continuer** — ne pas diverger localement.

`docs/design/theme.css` fait foi sur les valeurs visuelles, et le vocabulaire visible vient du
**country pack**, jamais d'une chaîne littérale.

## Méthode

- **Spec Kit est installé** (v0.16.5, `--integration claude`, scripts `sh`). Il livre des *skills*
  dans `.claude/skills/` : l'invocation est `/speckit-specify`, avec un tiret. Le détail de ce qui a
  été posé est dans [docs/01-stack.md § 2.2](docs/01-stack.md).
- **La constitution est encore le gabarit vide.** C'est l'étape zéro, avant toute tranche : tant que
  `.specify/memory/constitution.md` porte ses jetons `[PRINCIPLE_N_NAME]`, aucun `plan` n'est
  contrôlé contre quoi que ce soit. Le prompt est en tête de
  [docs/04-roadmap.md](docs/04-roadmap.md#étape-0--la-constitution). **Ne l'écris pas de toi-même** —
  c'est un arbitrage de l'utilisateur.
- **Une tranche de la roadmap = un cycle Spec Kit** : `specify` → `plan` → `tasks` → `implement`.
  Le prompt est déjà rédigé dans [docs/04-roadmap.md](docs/04-roadmap.md). **La numérotation suit
  l'epic, pas l'ordre d'exécution** — la colonne « rang » de la vue d'ensemble donne l'ordre réel.
- **Toute production visuelle lit d'abord le système de design.** Artboard, maquette, artifact,
  composant : on ouvre `docs/design/theme.css` et `docs/design/ecrans/` **avant** de dessiner, et on
  n'invente **aucune** valeur de couleur, d'espacement, de rayon ou de durée. `theme.css` est la seule
  source ; la répéter ailleurs — ici compris — créerait une seconde vérité qui divergerait.
- **Après chaque `specify` conclu, produis le prompt de revue visuelle** — mais **choisis sa forme
  avant de l'écrire**, en te posant une seule question : *cette tranche produit-elle un écran qu'une
  personne regarde ?*
  - **Oui** → un bloc `/design`, **un artboard par user story**.
  - **Non** — socle, moteur, contrat, vérification → **une planche de diagrammes Mermaid**, un seul
    fichier `diagrammes.md`, trois à cinq diagrammes. **On ne lance pas `/design`** : un artboard qui
    représente une migration ou un test est du texte mis en page.

  Dans les deux cas, en **session dédiée** après `specify` et avant `plan` — jamais pendant `implement`. Les deux gabarits
  sont en fin de [docs/05-design.md](docs/05-design.md).
- **Quand l'utilisateur valide une maquette** — « c'est bon », « validé », « on garde » — applique la
  procédure de rangement **sans qu'il ait à la demander** : sources au bon endroit, adresse du canvas
  reportée dans le `spec.md`, une ligne pour dire ce qui a été rangé. Elle est en fin de
  [docs/05-design.md](docs/05-design.md).
- **`scripts/verifier.sh` passe en une commande**, sinon rien n'est terminé.
- **Le journal se met à jour en fin de session**, dans [docs/progress.md](docs/progress.md).

## Ce que le produit ne fait pas

Le savoir évite d'écrire du code qui n'a pas lieu d'être. Ce qui viendra **après** le MVP est dans
[docs/06-apres-mvp.md](docs/06-apres-mvp.md), et ce document **est fermé** : rien ne s'en construit
avant qu'un établissement pilote n'édite ses bulletins dans Nelo.

**Ne l'ouvre pas pour coder.** Ce qu'une tranche doit respecter tient en huit contrôles mécaniques —
la porte **P-08**, [docs/01-stack.md § 7.1](docs/01-stack.md). Lire la stratégie multi-segments au
moment d'écrire une tranche expose au premier risque du projet : sur-généraliser un socle qui n'a
encore aucun client.

- **pas d'autre segment que le primaire au MVP** — le préscolaire, le secondaire général, le
  technique et le supérieur viennent après, **dans cet ordre**
  ([ADR 018](docs/adr/018-le-mvp-commence-par-le-primaire.md)) ;
- **pas de mode hors connexion au MVP** — **différé, pas exclu** ; quatre fondations se posent
  maintenant ([ADR 001](docs/adr/001-hors-connexion-differe.md)) ;
- **pas d'application native au MVP** — **la PWA est la cible**, installable dès le MVP ; Capacitor
  (mobile) et Tauri (poste) l'empaqueteront plus tard, sans réécriture
  ([ADR 002](docs/adr/002-web-d-abord-capacitor-plus-tard.md)) ;
- **pas un agent IA par service** — six capacités, dont deux au MVP
  ([ADR 011](docs/adr/011-six-capacites-ia-pas-trente-quatre-agents.md)) ;
- pas de contenu pédagogique, pas de LMS, pas de comptabilité certifiée, pas de paie déclarative, pas
  de concours nationaux, pas de reconnaissance faciale ;
- pas de microservices, pas de file de messages, pas de Kubernetes, pas d'ORM.

## Les règles qui ne se négocient pas

1. **Toute donnée d'élève est une donnée de mineur.** Base légale, durée de conservation et journal
   d'accès sont définis pour chaque traitement, dans le modèle.
2. **Tout montant est un entier d'unité mineure**, avec l'exposant porté par la devise. **Toute note
   est `NUMERIC`. Toute absence est un intervalle `[début, fin)`.**
3. **Toute entité pédagogique porte son année.** Rien n'est global — ni une classe, ni un coefficient,
   ni un tarif, ni une affectation de rôle.
4. **Tout référentiel est versionné.** Un bulletin réédité trois ans plus tard reflète le barème de
   l'époque, pas le barème courant.
5. **RLS activée et forcée sur chaque table**, `SET LOCAL app.current_tenant` dans chaque transaction,
   **et** vérification applicative de la capacité et du périmètre. Double barrière.
6. **Les modules ne partagent jamais de transaction.** Et **aucun paquet n'importe `protection`** :
   le cloisonnement est une **frontière d'import**, tenue par trois verrous — déclaration de
   dépendances, graphe d'imports, surface de l'`__init__.py` (porte **P-11**). Un compilateur
   refusait, un test signale : **c'est plus faible, et c'est écrit**
   ([ADR 017](docs/adr/017-fastapi-et-pydantic-remplacent-rust-et-actix.md)). La famille métier
   s'appelle **`modules/metier/`**, jamais `modules/modules/`.
7. **Aucune logique métier ne dépend du pays autrement que par le country pack.** Aucun
   `if pays == "CI"`, aucune borne d'échelle en dur.
8. **Le serveur calcule, le client affiche.** Aucune moyenne, aucune mention, aucun rang, aucun solde
   côté client. **Une action non autorisée est absente de l'écran, jamais grisée.**
9. **Un refus s'annonce avant la saisie**, avec son versant positif. **Aucune chaîne d'interface en
   dur** : les clés `fr` et `en` naissent ensemble.
10. **Tout changement d'état métier écrit un événement outbox dans la même transaction**, et **toute
    écriture porte sa clé d'idempotence**. Aucune saisie ne se perd.

## Langue

Le produit, le code, les commentaires et la documentation sont **en français**, accents compris
partout. Le bilinguisme `fr`/`en` est dans le socle, pas dans une phase ultérieure (règle 9).
