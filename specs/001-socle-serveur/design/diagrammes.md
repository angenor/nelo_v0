# T0a — Le socle serveur : planche de diagrammes

Revue visuelle de forme B pour [spec.md](../spec.md). Cinq diagrammes, un par question. Ce qui
n'y figure pas n'est ni dans la spécification, ni dans [docs/01-stack.md](../../../docs/01-stack.md),
ni dans [docs/03-api.md](../../../docs/03-api.md), ni dans [docs/02-domaine.md](../../../docs/02-domaine.md).

## 1. La hiérarchie des paquets et ses deux arêtes interdites — US4

Rend visible ce qu'un paquet a le droit d'importer, et les deux imports que P-04 et P-11 arrêtent.

```mermaid
graph LR
    domaine["modules/domaine/"]
    shared["modules/shared/"]
    socle["modules/socle/"]
    subgraph metier["modules/metier/"]
        protection["protection/ — cloisonné"]
    end
    segments["modules/segments/"]
    api["api/"]

    socle --> domaine
    socle --> shared
    metier --> domaine
    metier --> shared
    metier --> socle
    segments --> domaine
    segments --> shared
    segments --> socle
    segments --> metier
    api --> domaine
    api --> shared
    api --> socle
    api --> metier
    api --> segments

    tous["tout paquet, hors protection lui-même"]

    socle -. "P-04 refuse" .-> metier
    tous -. "P-11 refuse" .-> protection
```

## 2. Une écriture sur le module doré, du rejeu identique au rejeu divergent — US1, US2, US3

Rend visible l'ordre des barrières sur `PUT /parametres/{cle}` : identifiant de requête, tenant,
schéma, règle métier, puis valeur et événement dans une seule transaction.

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant A as api/
    participant T as socle/tenants
    participant B as PostgreSQL
    participant M as Mémoire des réponses (24 h)

    C->>A: PUT /parametres/{cle}<br/>X-Nelo-Requete: R<br/>en-tête d'établissement
    alt X-Nelo-Requete absent ou malformé
        A-->>C: 400 (enveloppe, requete_id)
    end
    A->>A: résoudre le tenant (provisoire jusqu'à T1a)
    A->>A: point d'insertion capacité tenant.parametre.definir (vide jusqu'à T1b)
    A->>A: valider le corps (Pydantic)
    alt corps invalide
        A-->>C: 422 VAL_SCHEMA_INVALIDE<br/>details : chemin de chaque champ
    end
    A->>M: réponse mémorisée pour (tenant, R) ?
    M-->>A: aucune
    A->>T: definir(cle, portee, portee_id, valeur)
    T->>B: BEGIN
    T->>B: SET LOCAL app.current_tenant
    T->>B: lire parametre_catalogue(cle)
    alt clé hors catalogue
        T-->>A: TEN_PARAMETRE_INCONNU
        A-->>C: 422 (enveloppe, details)
    else portée sous la portée la plus basse, ou hors tenant
        T-->>A: TEN_PORTEE_INVALIDE
        A-->>C: 422 (enveloppe, details)
    end
    T->>B: UPSERT parametre_valeur
    T->>B: INSERT événement (même transaction)
    T->>B: COMMIT
    T-->>A: valeur posée
    A->>M: mémoriser (tenant, R, empreinte du corps, statut, corps)
    A-->>C: 200 (contrat)

    C->>A: rejeu : mêmes en-têtes, même corps, R
    A->>M: réponse mémorisée pour (tenant, R) ?
    M-->>A: trouvée, empreinte identique
    A-->>C: 200 identique, aucun effet réexécuté

    C->>A: rejeu : R, corps différent
    A->>M: réponse mémorisée pour (tenant, R) ?
    M-->>A: trouvée, empreinte différente
    A-->>C: 409 REQUETE_REJOUEE_DIFFEREMMENT
```

## 3. Le cycle de vie d'un événement de la table d'événements — US3

Rend visible qu'un événement ne quitte la table que traité, et qu'un échec le ramène en attente
plutôt que de le perdre.

```mermaid
stateDiagram-v2
    [*] --> Ecrit : INSERT dans la transaction du changement d'état
    Ecrit --> [*] : ROLLBACK — rien n'est écrit
    Ecrit --> EnAttente : COMMIT
    EnAttente --> Pris : travailleur du même processus, ordre d'écriture par tenant
    Pris --> Traite : traitement réussi
    Pris --> EnEchec : traitement échoué ou interrompu
    EnEchec --> EnAttente : reprise — livraison possible une seconde fois
    EnAttente --> EnAttente : travailleur arrêté — l'événement s'accumule
    Traite --> [*]
```

## 4. La chaîne de vérification et le test négatif de chaque porte — US5

Rend visible les sept portes de `scripts/verifier.sh` dans un ordre proposé du contrôle le moins
coûteux au plus coûteux — le corpus ne le fixe pas, le plan le fixera —, l'arrêt au premier rouge
en trait épais, et en pointillé le test négatif qui casse chaque porte.

```mermaid
graph LR
    debut([scripts/verifier.sh]) --> P02
    P02["P-02<br/>épinglage et verrouillage"] --> P07
    P07["P-07<br/>licences"] --> P04
    P04["P-04<br/>socle n'importe pas metier"] --> P11
    P11["P-11<br/>trois verrous protection"] --> P01
    P01["P-01<br/>migrations sur base vierge, RLS, aucune FK inter-schémas"] --> P12
    P12["P-12<br/>tout accès aux données exercé"] --> P03
    P03["P-03<br/>client régénéré sans écart"] --> suspension
    suspension["assistance.suspendue posée<br/>reparcours du module doré"] --> ok([succès])

    P02 ==> E02[/"échec : P-02, dépendance nommée"/]
    P07 ==> E07[/"échec : P-07, dépendance nommée"/]
    P04 ==> E04[/"échec : P-04, arête nommée"/]
    P11 ==> E11[/"échec : P-11, verrou nommé"/]
    P01 ==> E01[/"échec : P-01, table nommée"/]
    P12 ==> E12[/"échec : P-12, fonction nommée"/]
    P03 ==> E03[/"échec : P-03, écart affiché"/]

    N02["dépendance en intervalle<br/>ou uv.lock absent"] -.-> P02
    N07["dépendance copyleft fort"] -.-> P07
    N04["socle importe metier"] -.-> P04
    N11["import de protection différé dans une fonction<br/>ou chemin en chaîne<br/>ou __init__ exposant un accès aux données<br/>ou dépendance déclarée"] -.-> P11
    N01["table sans politique RLS<br/>ou FK traversant un schéma"] -.-> P01
    N12["colonne renommée, requête inchangée<br/>ou fonction d'accès sans test"] -.-> P12
    N03["client typé modifié à la main"] -.-> P03
```

## 5. Les trois dépendances externes simulées, et l'assistance dans le socle — US6, US7

Rend visible que chaque dépendance externe est appelée par son abstraction, simulée par défaut,
et que l'assistance est un paquet suspendu par une clé du catalogue, jamais un service.

```mermaid
graph LR
    subgraph socle["modules/socle/"]
        tenants["tenants<br/>parametre_catalogue"]
        assistance["assistance<br/>six capacités connues<br/>aucune livrée : refus explicite"]
    end

    tenants -- "assistance.suspendue<br/>portée ETABLISSEMENT" --> assistance
    assistance -- "état : non livrée | suspendue | disponible" --> ecran["interface : affordance absente"]

    subgraph abstractions["abstractions, une par dépendance externe"]
        sms["passerelle de messages courts<br/>face au fournisseur réel, remplacée en T4a"]
        paiement["agrégateur de paiement<br/>face au fournisseur réel, remplacée en T8b"]
        inference["service d'inférence<br/>face au fournisseur réel"]
    end

    assistance --> inference

    sms --> simSms["simulation SMS<br/>par défaut"]
    paiement --> simPaiement["simulation paiement<br/>par défaut"]
    inference --> simInference["simulation inférence<br/>par défaut"]

    subgraph modes["modes, depuis la configuration"]
        m0["succès : accusé rendu"]
        m1["accusé en retard"]
        m2["accusé en double"]
        m3["jamais reçu : délai borné, pas de blocage"]
        m4["indisponible : 503 avec enveloppe"]
    end

    simSms --> modes
    simPaiement --> modes
    simInference --> modes

    compose["compose.yml : PostgreSQL, Valkey, Garage"]
    compose -. "n'y figure pas" .-> inference
    compose -. "n'y figure pas" .-> assistance
```
