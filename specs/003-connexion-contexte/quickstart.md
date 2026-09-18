# Démarrage rapide et validation : T1a, se connecter et savoir où l'on est

Ce guide prouve la tranche de bout en bout, user story par user story. Il ne contient aucun corps
d'implémentation : les formes sont dans [contracts/](contracts/), le modèle dans
[data-model.md](data-model.md), les décisions dans [research.md](research.md).

## Prérequis sur le poste

Ceux de T0a et T0b ([001 quickstart](../001-socle-serveur/quickstart.md),
[002 quickstart](../002-socle-interface/quickstart.md)) : Docker Compose, `uv`, `pnpm`, les deux
moteurs Playwright installés une fois. Rien de plus : aucune passerelle réelle, aucun compte tiers.

## Démarrer

```bash
docker compose up -d
uv sync && pnpm install --frozen-lockfile
cp -n .env.exemple .env                 # NELO_SECRET_JETON, NELO_INDICATIF_DEFAUT, NELO_COOKIES_SECURE=false
scripts/bd-vierge.sh --avec-jeu-d-essai # quatre schémas ; deux tenants ; un compte, une personne, une année, une affectation par tenant ; deux packs
uv run fastapi dev api/main.py          # :8000
NELO_DEMONSTRATION=1 pnpm --filter nelo-web dev   # :3000 ; le relais /api/v1/** est dans Nuxt
```

Le jeu d'essai imprime, en forme `export`, `ETAB_A`, `ETAB_B`, `NUMERO_A` (le numéro du compte du
tenant A, au format E.164) et `COMPTE_A`. Le journal des messages simulés est dans
`NELO_SMS_JOURNAL` (`.env`), une ligne JSON par envoi.

## US1 : ouvrir par code reçu

Dans le navigateur : `http://localhost:3000/` redirige vers `/connexion`. Saisir `NUMERO_A`,
« Recevoir le code ». Lire le code dans le journal des messages, le saisir. Attendu : l'écran du
code personnel (US3), puis l'accueil, qui affiche « aucun domaine » avec le nom et le téléphone de
l'administrateur d'essai.

En ligne de commande, la propriété qui compte :

```bash
REQ=$(uv run python -c "import uuid; print(uuid.uuid7())")
demander() { curl -s -o /dev/null -w "%{http_code} %{size_download} %{time_total}\n" \
  -X POST localhost:8000/api/v1/auth/otp -H "X-Nelo-Requete: $(uv run python -c 'import uuid; print(uuid.uuid7())')" \
  -H "Content-Type: application/json" -d "{\"identifiant\":\"$1\"}"; }
demander "$NUMERO_A"          # 204 0 …   et une ligne de plus dans le journal des messages
demander "+2250100000000"     # 204 0 …   et aucune ligne de plus
```

Attendu : même statut, même taille, un temps du même ordre ; `pytest tests/authentification/test_reponse_identique.py`
mesure l'écart des médianes sur cent demandes (SC-003). Rejouer `demander` avec le **même**
`X-Nelo-Requete` : pas de second message. Cinq codes faux → `AUT_OTP_TENTATIVES_EPUISEES` ; une
seconde demande dans la minute → `429` avec `Retry-After`.

## US2 : deux tenants, quatre en-têtes

```bash
# une session sur A (voir tests/authentification/outils.py::ouvrir pour le même geste en Python)
curl -s -c cookies.txt -X POST localhost:8000/api/v1/auth/otp/verification -H "X-Nelo-Requete: $REQ" \
  -H "Content-Type: application/json" -d "{\"identifiant\":\"$NUMERO_A\",\"code\":\"$CODE\"}" | jq -r .jeton_acces > jeton.txt
J="Authorization: Bearer $(cat jeton.txt)"
curl -s localhost:8000/api/v1/parametres -H "$J" -H "X-Nelo-Etablissement: $ETAB_A" | jq .parametres[0]   # 200
curl -s localhost:8000/api/v1/parametres -H "$J" -H "X-Nelo-Etablissement: $ETAB_B" | jq .code           # TEN_ETABLISSEMENT_NON_AUTORISE, 403
curl -s localhost:8000/api/v1/parametres -H "X-Nelo-Etablissement: $ETAB_A" | jq .code                   # AUT_JETON_MANQUANT, 401
curl -s localhost:8000/api/v1/parametres -H "$J" | jq .code                                              # TEN_ETABLISSEMENT_REQUIS, 400
```

Attendu : un établissement inexistant (`uuidgen`) rend le **même** `403` que `ETAB_B`. La route
d'essai pédagogique n'existe qu'en test : `pytest tests/en_tetes/` prouve `400 ANN_ANNEE_REQUISE`
sans repli et `404` pour une année hors établissement. `pytest tests/isolation/` couvre chaque
table neuve.

## US3 : le code personnel

Après US1, définir `1234` deux fois. Fermer la session (en-tête de la coquille). Rouvrir
`http://localhost:3000/` : l'écran propose le nom du compte et quatre chiffres ; aucune ligne
n'apparaît dans le journal des messages. Sur un profil de navigateur neuf (fenêtre privée), le
code personnel n'est pas proposé. Cinq codes faux → le verrou, et le versant positif.

## US4 : le contexte

```bash
curl -s localhost:8000/api/v1/moi/capacites -H "$J" -H "X-Nelo-Etablissement: $ETAB_A" | jq '{compte, etablissement_actif, annee_active, capacites, country_pack: .country_pack.devise}'
```

Attendu : la forme de [03-api.md § 1.9](../../docs/03-api.md), `capacites: []`, la devise du pack
semé, `administrateur` renseigné. Le jeu d'essai rattache aussi le compte A à un second
établissement : la coquille demande lequel, et le changement relit le contexte. Avec le tenant
fictif du jeu d'essai (`NUMERO_FICTIF`), le contexte porte l'autre devise et l'autre vocabulaire
sans qu'une ligne de code diffère.

## US5 : révocation, fermeture, rotation

```bash
curl -s -X POST localhost:8000/api/v1/comptes/$COMPTE_A/suspension -H "$J_ADMIN" -H "X-Nelo-Etablissement: $ETAB_A" -H "X-Nelo-Requete: $(uuidgen)"   # 204
curl -s localhost:8000/api/v1/parametres -H "$J" -H "X-Nelo-Etablissement: $ETAB_A" | jq .code   # AUT_SESSION_REVOQUEE, à la requête suivante
```

Rotation : `POST /auth/rafraichissement` avec `cookies.txt` rend un nouveau cookie ; représenter
l'ancien après dix secondes → `401` et la session entière tombe (`pytest tests/authentification/test_rotation.py`).
Dans le navigateur, après ouverture : outils de développement, stockage local et de session
vides, `document.cookie` sans aucun `nelo_` (`pnpm --filter nelo-web test:e2e tests/e2e/session.spec.ts`).

## US6 : l'invitation

```bash
curl -s -X POST localhost:8000/api/v1/comptes -H "$J_ADMIN" -H "X-Nelo-Etablissement: $ETAB_A" -H "X-Nelo-Requete: $(uuidgen)" \
  -H "Content-Type: application/json" -d "{\"personne_id\":\"$PERSONNE_NOUVELLE\",\"identifiant\":\"+2250700000002\"}" | jq .
```

Attendu : `201`, `statut: invite`, `invite_le`, **pas** de jeton ; une ligne dans le journal des
messages avec un lien `/activation/…` sous 160 caractères. Ouvrir le lien dans le navigateur :
session ouverte, écran du code personnel ; le rouvrir : `AUT_INVITATION_INVALIDE` avec ses deux
issues.

## US7 : changer de numéro

Depuis la coquille, « Mon numéro » → nouveau numéro → code lu dans le journal → confirmation.
Attendu : le journal porte le code vers le **nouveau** numéro puis le message d'information vers
l'ancien ; la session courante tient. Par la route administrative, les sessions du compte tombent
(`pytest tests/authentification/test_changement.py`).

## US8 : deux comptes, un numéro

```bash
# second compte sur NUMERO_A, sans déclaration → 422 AUT_IDENTIFIANT_DEJA_UTILISE ; avec "partage_familial": true → 201
demander "$NUMERO_A"          # une seule ligne dans le journal
# vérification → {"resultat":"CHOIX_REQUIS","comptes":[…deux noms…]} ; rappel avec compte_id → session
```

## Les portes

```bash
scripts/verifier.sh           # treize étapes de T0b, plus tests/authentification, tests/en_tetes, tests/contexte ; P-05 et P-10 avec la session semée
scripts/tests-negatifs.sh     # + les mutations de T1a : révocation non consultée, réponse différente selon le compte, repli sur l'année active, jeton en stockage
```

Attendu : vert en une commande, sous cinq minutes (SC-012) ; chaque mutation fait échouer la
porte en la nommant, le dépôt reste intact.

## Ce que la tranche a mesuré, le 2026-09-18

Sur un poste de développement (Apple Silicon, PostgreSQL et Valkey en conteneurs locaux). Les
mesures d'écran viennent de P-10, celles de temps des suites qui les portent.

| Critère | Attendu | Mesuré |
|---|---|---|
| **SC-003** écart des médianes entre un numéro connu et un inconnu | sous 50 ms | **2,8 ms** (connu 5,2 ms, inconnu 2,4 ms), sur cent demandes alternées |
| **SC-006** aucun jeton lisible d'un script | aucun | **aucun** : `nelo_acces`, `nelo_refresh` et `nelo_appareils` sont `HttpOnly`, et rien qui ressemble à un jeton ne se lit dans le stockage (`web/tests/e2e/session.spec.ts`) |
| **SC-008** délai de remise à la passerelle simulée | quelques secondes | **sous 1 s** : le travailleur passe toutes les 500 ms, et les tests lisent le message sans attente perceptible |
| **SC-009** poids des écrans de la connexion | 120 Ko d'application, 45 Ko de polices (60 avec la police du champ de code) | `connexion` **118,1 Ko** et 58,4 Ko de polices ; `connexion-code` **116,7 Ko** ; `connexion-pin` **117,3 Ko** ; `activation` **110,4 Ko** ; `compte-telephone` **118,6 Ko** ; `accueil-session` **113 Ko** |
| **SC-012** durée de `scripts/verifier.sh` | sous cinq minutes | **3 min 22 s**, dix portes vertes |
| durée de `scripts/tests-negatifs.sh` | non budgétée | **10 min 53 s**, treize mutations, treize échecs obtenus |

**SC-001** (ouvrir par code reçu en trois écrans et moins de 90 s) et **SC-002** (rouvrir par code
personnel sous 10 s) se chronomètrent à la main sur un téléphone, en 3G simulée : les trois écrans
existent et le parcours passe de bout en bout dans un navigateur réel, mais la mesure au
chronomètre reste à faire avec l'utilisateur. P-10 mesure le premier affichage utile à **640 ms**
en 3G lente, sur un plafond de 2 000 ms.

## Tout éteindre

```bash
docker compose down            # les données de développement restent dans les volumes
```
