# Recherche : T1a, se connecter et savoir où l'on est

**Phase 0 du plan** · 2026-09-17 · Chaque décision cite ce dont elle dérive. Rien n'est tranché
ici qui contredise [docs/01-stack.md](../../docs/01-stack.md), [docs/02-domaine.md](../../docs/02-domaine.md),
[docs/03-api.md](../../docs/03-api.md) ou la [constitution](../../.specify/memory/constitution.md) ;
ce qui manquait au corpus est appliqué comme diff explicite, listé en fin de fichier, selon
l'arbitrage délégué du 2026-09-14. Deux explorations du dépôt ont précédé : le socle serveur de T0a
(composition, middlewares, outbox, migrations, portes) et le socle d'interface de T0b (source de
contexte, coquille, plateforme, portes) ; ce que la recherche affirme du code existant vient de là.

## R-01 : Trois bibliothèques, épinglées, sous licence autorisée

- **Décision** : `phonenumbers` **9.0.39** (Apache-2.0) pour normaliser tout numéro en E.164 ;
  `PyJWT` **2.14.0** (MIT) pour le jeton d'accès signé ; `argon2-cffi` **25.1.0** (MIT) pour
  l'empreinte du code personnel. Relevées sur PyPI le 2026-09-17 ; l'implémentation réépingle si
  une version stable plus récente est parue, et `uv.lock` fige le tout (P-02, P-07).
- **Motif** : le format de numéro vient du pack et l'indicatif par défaut de la configuration
  (FR-002) ; une bibliothèque qui connaît les plans de numérotation évite d'écrire une règle par
  pays. HS256 suffit à un monolithe qui signe et vérifie seul ; PyJWT sans extra `crypto`.
  Argon2id est la recommandation courante pour une empreinte de secret court, et le paquet est
  maintenu.
- **Écartées** : une expression régulière par pays (une littérale de pays par pays, contraire à
  R8) ; `python-jose` (moins maintenu) ; `bcrypt` (borné à 72 octets, sans paramètre de mémoire) ;
  un jeton opaque sans signature (une lecture Valkey de plus par requête pour ce que la signature
  donne gratuitement, la révocation restant de toute façon une lecture Valkey, R-06).

## R-02 : Un module `habilitations`, et les noyaux `personnes` et `annees`

- **Décision** : trois paquets neufs dans `modules/socle/`, trois schémas, trois dossiers de
  migrations. **`habilitations`** porte le compte, l'affectation (noyau), les sessions, les codes,
  les appareils, les invitations, le changement de numéro : tout ce que [02-domaine.md § 3](../../docs/02-domaine.md)
  range dans ce schéma. **`personnes`** ne porte que `personne` avec les quatre colonnes que le
  contexte lit ; **`annees`** ne porte que `annee_scolaire` avec ses colonnes de § 4.1, sans
  transition. Chacun a son `pyproject.toml` déclaratif, son `__init__.py` à surface explicite, son
  `tables.py`, son `acces.py` (nom imposé par P-12), son `service.py`, son `schemas.py`, et son
  `evenement_outbox`. `pyproject.toml` racine les ajoute aux membres de l'espace de travail ;
  `api/pyproject.toml` les déclare.
- **Les trois contraintes du socle minimal**, écrites dans la spec et opposables ici : chaque
  colonne posée porte le nom que le domaine lui donne ; T3a et T2a complètent sans renommer ni
  retirer ; aucune règle de ces tranches (transition d'année, lien de responsabilité, calcul de
  capacité) n'est implémentée. `annees` pose déjà les deux index partiels d'unicité de § 4.5
  (une seule `active`, une seule `preparation` par établissement) : c'est une contrainte, pas une
  règle, et T2a la trouvera en place.
- **Ce que ça touche dans le socle** : `scripts/bd-vierge.sh` applique un seul `alembic.ini` en
  dur ; il boucle désormais sur `migrations/*/` dans l'ordre `tenants`, `personnes`, `annees`,
  `habilitations` (les noyaux avant ce qui les référence, pour le jeu d'essai).
  `scripts/portes/p12_acces_exerces.py` déclare les quatre schémas dans `DECLARATIONS`.
  `tests/isolation/test_deux_tenants.py` énumère les tables depuis `information_schema` : les
  tables neuves y entrent seules, à condition d'avoir une ligne par tenant, ce que la fixture
  `tenants_ab` garantit (R-18).
- **Motif** : [01-stack.md § 2.3](../../docs/01-stack.md) nomme `tenants · personnes ·
  habilitations · annees` comme les modules du socle ; le domaine interdit de porter le nom d'une
  personne sur le compte ; la constitution (XI) interdit qu'une transaction traverse deux schémas.
- **Écartées** : un seul module « authentification » qui porterait aussi nom et année (deux
  entités hors de leur schéma, une reprise garantie en T2a et T3a) ; porter nom, prénoms et langue
  sur `compte` (le domaine dit le contraire).

## R-03 : Le rattachement est l'affectation, et elle porte son établissement

- **Décision** : `habilitations.affectation` (noyau : compte, année, établissement, début, fin)
  porte **`etablissement_id`**, copié de l'année au moment de l'écriture, en plus de `annee_id`.
  Les deux middlewares d'en-tête font **une seule requête** sur cette table, dans une transaction
  tenantée : « ce compte a-t-il une affectation vivante sur cet établissement (et cette année) ? ».
  L'invariant « l'établissement de l'affectation est celui de son année » est tenu par le service
  à l'écriture et vérifié par un test. **Diff appliqué** sur [02-domaine.md § 3.2](../../docs/02-domaine.md).
- **Motif** : le domaine fait dériver l'établissement d'une affectation de son année ; sans la
  colonne, vérifier `X-Nelo-Etablissement` exigerait à chaque requête une lecture de `annees` par
  son interface, deux allers-retours sur le chemin de toute requête. R13 admet le rattachement par
  identifiant ; l'intégrité est applicative et testée.
- **« Vivante »** : `debut <= aujourd'hui` et (`fin IS NULL` ou `fin > aujourd'hui`), date
  calculée **en UTC** dans cette tranche. Le fuseau de l'établissement rendrait la borne juste à
  l'heure près autour de minuit ; il exigerait une lecture de `tenants` par requête. **Écart
  nommé** : T1b, propriétaire de l'affectation complète, pose le fuseau quand elle pose le rôle.
- **Écartées** : mettre les rattachements en cache dans la session Valkey (une nouvelle
  affectation ne serait visible qu'à la session suivante, et T1b devrait invalider) ; lire
  `annees` par requête.

## R-04 : La chaîne de middlewares, et la fin du tenant provisoire

- **Décision** : quatre middlewares ASGI purs, dans `api/`, ajoutés de l'intérieur vers
  l'extérieur, donc exécutés dans cet ordre : **`Session`** (`api/session.py`) → **`Etablissement`**
  (`api/etablissement.py`) → **`Annee`** (`api/annee.py`) → **`Idempotence`** (existant). Le
  fichier `api/tenant_provisoire.py` est **supprimé** ; ses trois utilitaires (`CHEMINS_LIBRES`,
  `en_tete`, `chemin_de_route`) passent dans `api/asgi.py`. La fonction `SECURITY DEFINER`
  `tenants.tenant_de_etablissement` est retirée par la migration `0002` de `tenants` et son
  enveloppe de service avec elle ; `tests/portes/test_security_definer.py::ATTENDUES` devient
  `{tenants_pour_travailleur, comptes_par_identifiant, compte_par_invitation, compte_par_id_sans_tenant}`.
  - `Session` : chemins libres (`/sante`, `/auth/*`, la documentation) ; sinon lit `Authorization`
    (`401 AUT_JETON_MANQUANT` absent ou sans `Bearer`), vérifie la signature et l'expiration
    (`401 AUT_JETON_INVALIDE`), lit `session:{sid}` dans Valkey (`401 AUT_SESSION_REVOQUEE` si
    absente ou si son compte n'est plus celui du jeton), dépose `compte_id`, `tenant_id`,
    `session_id` dans `scope["state"]`. **C'est la liste de révocation consultée à chaque
    requête** (FR-026).
  - `Etablissement` : sur toute route hors chemins libres, lit `X-Nelo-Etablissement`
    (`400 TEN_ETABLISSEMENT_REQUIS` absent ou malformé), puis, dans `transaction(tenant_id)`,
    `habilitations.acces.affectation_vivante(...)` ; aucune ligne → `403
    TEN_ETABLISSEMENT_NON_AUTORISE`, que l'établissement soit d'un autre tenant, inexistant ou non
    rattaché : la RLS et la requête ne le distinguent pas, et c'est voulu. Dépose
    `etablissement_id`.
  - `Annee` : lit `X-Nelo-Annee` s'il est présent (`400 ANN_ANNEE_REQUISE` si malformé) ; sur une
    route **déclarée pédagogique**, absent → `400 ANN_ANNEE_REQUISE` ; présent → une requête sur
    `affectation` (compte, établissement, année) sinon `404 TEN_RESSOURCE_INTROUVABLE`. La
    déclaration est un ensemble de motifs de chemin `ROUTES_PEDAGOGIQUES` dans `api/annee.py`,
    que chaque routeur alimente ; en T1a il est vide, et un test enregistre une route d'essai
    (le patron de `tests/simulations/test_indisponible_503.py`) pour exercer les trois refus.
  - `Idempotence` : la clé devient `idem:{tenant_id}:{requete_id}` quand la session a posé le
    tenant, **`idem:auth:{requete_id}`** sur les chemins libres d'écriture (`/auth/otp`,
    `/auth/otp/verification`, `/auth/pin`, `/auth/rafraichissement`, `/auth/invitation/{jeton}`).
    Le rejeu d'une demande de code rend le `204` mémorisé sans second événement (US1-8).
  - `api/erreurs.envoyer_erreur_asgi` accepte des en-têtes supplémentaires, pour `Retry-After`.
- **Motif** : [03-api.md § 1.2](../../docs/03-api.md) : « ces quatre en-têtes sont lus par un
  middleware, chacun le sien, avant que FastAPI n'ait validé quoi que ce soit ». Le `403` de
  l'en-tête « prend alors son objet », comme la docstring du provisoire l'annonçait.
- **Écartées** : un seul middleware pour les quatre en-têtes (les chemins libres et les routes
  pédagogiques diffèrent par en-tête) ; des dépendances `Header(...)` (le `400` deviendrait un
  `422`, la table de § 1.2 serait fausse).

## R-05 : La limitation de débit, en Valkey, avant toute lecture

- **Décision** : `api/limitation.py`, une fonction `compter(valkey, cle, plafond, fenetre) ->
  int | None` (`INCR` + `EXPIRE NX`) appelée par le service de demande de code : par numéro
  (`otp_debit:{identifiant}`, cinq par heure), par client (`otp_debit_client:{adresse}`, vingt
  par heure), et le délai de renvoi (`otp_renvoi:{identifiant}`, soixante secondes). Un plafond
  atteint lève `ErreurMetier("API_LIMITE_DEBIT", statut=429, details={"reprise_dans": n})` que
  `api/erreurs.py` traduit avec `Retry-After`. **L'adresse du client** est celle de
  `X-Forwarded-For` quand la requête vient du relais Nuxt (R-09), dont l'adresse est déclarée
  dans `NELO_RELAIS_DE_CONFIANCE` ; sinon `scope["client"]`.
- **Motif** : [ADR 007](../../docs/adr/007-valkey-pour-l-ephemere.md) range la limitation de
  débit dans l'éphémère ; « une fenêtre perdue n'a aucune conséquence ». Derrière le relais, toutes
  les requêtes ont la même adresse source : sans l'en-tête transmis, la limite par client
  bloquerait tout le monde.
- **Écartées** : une bibliothèque de limitation (une dépendance pour trois `INCR`) ; une limite
  par compte (le compte n'est pas connu, et le dire serait une fuite).

## R-06 : La session, le jeton d'accès et la rotation du refresh

- **Décision** : l'ouverture d'une session écrit `session:{sid}` et `sessions_compte:{compte}`
  dans Valkey, avec pour durée `securite.duree_session_minutes` lue par
  `tenants.valeur_effective` à l'ouverture ; rend un JWT HS256 de soixante minutes (`sub`, `ten`,
  `sid`, `iat`, `exp`, `jti`) et pose le cookie `nelo_refresh` (32 octets aléatoires,
  `secrets.token_urlsafe`), dont Valkey ne garde que le SHA-256. **Rotation** : chaque
  rafraîchissement crée un jeton neuf et marque l'ancien `remplace_le` avec une durée de vie
  réduite à la **fenêtre de concurrence** (dix secondes) ; un ancien jeton présenté dans la
  fenêtre rend le même jeton neuf (deux onglets) ; hors fenêtre, ou un jeton inconnu, révoque la
  session entière et écrit `session.fermee(REUTILISATION)`. **Révocation** : `DEL session:{sid}`
  et de ses refresh ; la suspension et le changement administratif parcourent
  `sessions_compte:{compte}`. La fermeture (`DELETE /auth/session`) fait de même pour une session
  et efface le cookie. Les cookies : `HttpOnly; Secure; SameSite=Strict`, chemin borné ; `Secure`
  levé par `NELO_COOKIES_SECURE=false` en développement seulement.
- **Motif** : [03-api.md § 1.2](../../docs/03-api.md) et [01-stack.md § 5.1](../../docs/01-stack.md)
  mot pour mot ; [ADR 007](../../docs/adr/007-valkey-pour-l-ephemere.md) : « sessions et liste de
  révocation : reconstructible, au pire tout le monde se reconnecte » (US5-7).
- **Écartées** : une liste noire de `jti` (il faudrait écrire à chaque révocation et lire à chaque
  requête ; l'absence de session est la même lecture, sans écriture) ; un refresh en JWT (rien à
  signer, tout est dans Valkey) ; une durée de session lue à chaque requête (elle est figée à
  l'ouverture ; un changement de paramètre vaut pour les sessions suivantes, et c'est dit).

## R-07 : Le code à usage unique, avant tout tenant

- **Décision** : `POST /auth/otp` normalise le numéro (R-14), applique les trois limites (R-05),
  appelle `habilitations.comptes_par_identifiant` (fonction `SECURITY DEFINER`, tous tenants,
  par `sans_tenant()`), et **quoi qu'il trouve** rend `204` avec les mêmes en-têtes. S'il trouve
  au moins un compte `actif` ou `invite` : génère six chiffres (`secrets.randbelow`), écrit
  `otp:{identifiant}` (empreinte SHA-256 salée par `envoi_id`, tentatives, la liste des comptes
  avec leur tenant, `envoi_id`) et `otp_texte:{envoi_id}` (le code en clair, dix minutes), puis
  ouvre `transaction(tenant_du_premier_compte)` pour écrire `habilitations.otp.demande`
  (`identifiant`, `envoi_id`, `langue`) dans l'outbox de **ce** tenant. Le consommateur (R-08)
  lit `otp_texte`, compose le message, envoie, efface le texte. S'il ne trouve aucun compte, il
  exécute quand même la génération et le calcul d'empreinte, sans les écrire, pour que le temps
  de réponse ne dise rien (SC-003).
- `POST /auth/otp/verification` lit `otp:{identifiant}` : absent → `AUT_OTP_EXPIRE` ; empreinte
  fausse → tentatives + 1, `AUT_OTP_INVALIDE` avec `tentatives_restantes`, et à cinq
  `AUT_OTP_TENTATIVES_EPUISEES` avec destruction ; juste → si un seul compte, session ouverte
  (et activation si `invite`, FR-033) ; si plusieurs, `ChoixRequis` avec les noms lus par
  `personnes.lire_identites` dans une transaction par tenant concerné, et la même route rappelée
  avec `compte_id` ouvre la session choisie (le code reste valide jusqu'au choix, une seule fois).
- **Motif** : la contrainte non négociable du prompt, et l'observation qu'une passerelle
  indisponible publierait l'existence des comptes si l'envoi était synchrone (cas limite de la
  spec) ; le code en clair ne doit jamais entrer dans une table conservée (principe X : l'outbox
  est un grand livre).
- **Écartées** : le code dans la charge de l'événement (durable, en clair) ; un événement par
  tenant (deux messages) ; l'envoi synchrone (fuite par le `503`).

## R-08 : Le travailleur aiguille par type, la passerelle lui est injectée

- **Décision** : `api/consommateurs.py` expose `aiguilleur(passerelle, configuration) ->
  Consommateur` : une fermeture qui, selon le préfixe de `evenement.type`, appelle
  `habilitations.consommer_envoi(tenant_id, evenement, passerelle, valkey)` pour les quatre types
  qui envoient un message (`otp.demande`, `compte.invite`, `identifiant.change` ; le message
  d'information part vers l'ancien numéro), et le journal pour tout le reste. `main.py`
  construit `Travailleur(configuration, aiguilleur(...))`. Le travailleur parcourt désormais les
  quatre tables d'outbox : `tenants.consommer_lot` devient générique sur le schéma
  (`modules/shared/outbox.py` porte la prise, le marquage et la reprise, chaque module l'appelle
  sur sa table ; `tenants` garde son interface). Livraison au moins une fois : un texte déjà
  effacé fait du second passage un non-événement journalisé.
- **Motif** : T0a l'avait laissé à « la première tranche qui a un vrai consommateur » ; c'est
  celle-ci, avant T4a. Le patron d'injection par fermeture est celui de `assistance_suspendue`
  dans `main.py`.
- **Écartées** : un registre global de consommateurs (un bus qui ne dit pas son nom) ; faire
  envoyer par la route (R-07).

## R-09 : L'API sous l'origine de Nuxt, et le jeton d'accès hors de portée du script

- **Décision** : un relais Nitro, `web/server/api/v1/[...].ts`, reçoit toute requête
  `/api/v1/**` du navigateur et la transmet à l'API (`runtimeConfig.apiBase`, `NUXT_API_BASE`,
  `http://localhost:8000` par défaut) avec `proxyRequest` de h3. Il fait trois choses de plus :
  il transforme le cookie **`nelo_acces`** en `Authorization: Bearer` vers l'API ; sur les
  réponses qui portent `jeton_acces` (vérification du code, code personnel, lien,
  rafraîchissement), il range ce jeton dans `nelo_acces` (`HttpOnly; Secure; SameSite=Strict;
  Path=/`, durée du jeton) et le **retire du corps** ; il transmet tels quels les `Set-Cookie`
  de l'API (`nelo_refresh`, `nelo_appareils`) et pose `X-Forwarded-For`. Le client
  (`web/app/core/api/client.ts`, `useApi()`) appelle des adresses relatives `/api/v1/…` avec
  `$fetch`, pose `X-Nelo-Etablissement`, `X-Nelo-Annee`, `X-Nelo-Requete` (UUID v7 généré par
  `core/api/uuid7.ts`), et sur `401 AUT_JETON_INVALIDE` appelle une fois `/auth/rafraichissement`
  puis rejoue. **Au rendu serveur**, `SourceApi` utilise `useRequestFetch()`, qui transmet les
  cookies de la requête entrante au relais, lequel les transforme comme pour le navigateur ; un
  rafraîchissement fait au rendu serveur renvoie ses `Set-Cookie` dans la réponse HTML.
- **Ce que ça vaut au regard de la spec** : FR-011 tient (l'API rend le jeton d'accès dans sa
  réponse, le refresh en cookie non lisible) ; FR-012 tient plus fort que demandé : **aucun
  jeton n'est jamais visible d'un script**, ni en stockage ni en mémoire de page. La règle P-06
  reste intacte : `document.cookie` n'est touché nulle part.
- **Motif** : T0b n'a laissé ni client d'API ni relais ; l'API est sur `:8000`, l'application
  sur `:3000` ; un cookie `SameSite=Strict` ne voyage pas entre deux origines, et le corpus
  impose `Strict`. Le rendu serveur de la coquille ([T0b R-06](../002-socle-interface/research.md))
  exige que le serveur Nuxt puisse lire le contexte : il le peut par les cookies, jamais par un
  jeton en mémoire de navigateur. En production, le même relais tient ; un mandataire inverse
  devant Nuxt suffit, sans CORS.
- **Écartées** : CORS avec `credentials` (`SameSite=Strict` l'interdit, et `Lax` affaiblit la
  règle du corpus) ; le jeton d'accès en mémoire JavaScript (le rendu serveur n'y a pas accès :
  premier affichage en squelette, contraire à R-06 de T0b) ; `routeRules` `proxy` seul (ne
  transforme ni cookie ni corps).

## R-10 : La source de démonstration ne vit que dans les constructions d'essai

- **Décision** : `web/app/plugins/contexte.ts` choisit sa source : `SourceDemonstration` si la
  construction porte `__NELO_DEMONSTRATION__` (constante Vite `define`, posée par
  `NELO_DEMONSTRATION=1` à la construction) **et** que l'adresse porte `?persona=` ; `SourceApi`
  sinon. En production, la constante vaut `false` et l'import dynamique des personas est
  élagué : le code de démonstration ne voyage pas. Sur un `401`, la source laisse le contexte
  nul et le middleware de route `session.global.ts` envoie vers `/connexion`, sauf pour les pages
  `sansCoquille`. `scripts/verifier.sh` construit une fois avec la constante, pour P-05, P-10 et
  les e2e de composition de T0b, qui gardent leurs personas.
- **Motif** : FR-051 (la coquille lit le contexte réel) et la réalité de T1b : jusqu'à elle,
  aucune capacité réelle n'existe, donc les quatre situations de la coquille (mono-domaine,
  cinq, sept, aucune) ne peuvent s'observer qu'en démonstration ; les retirer ferait perdre les
  tests de T0b sans rien prouver de plus. Un test P-10 sur l'accueil **réel** (session semée,
  R-11) vérifie qu'aucun morceau de personas n'est chargé.
- **Écartées** : supprimer la démonstration (perte des tests de composition) ; la laisser en
  production (des données fictives et un poids inutile).

## R-11 : Les portes ouvrent une session semée

- **Décision** : `scripts/avec-serveur-dev.sh` lance aussi l'API (`uvicorn api.main:app` sur
  `NELO_PORT_API_TEST`, base `nelo_web_test` semée par `scripts/bd-vierge.sh --avec-jeu-d-essai`,
  Valkey base 2, `NELO_SMS_JOURNAL` vers un fichier temporaire, `NELO_DEMONSTRATION=1`) avant
  l'application. Un `globalSetup` Playwright (`web/tests/session.setup.ts`) demande un code pour
  le compte d'essai, lit le code dans le journal des messages, le vérifie, définit un code
  personnel et enregistre l'état (`storageState`) ; les entrées de `web/ecrans.json` qui portent
  `"session": true` sont visitées avec cet état, les autres sans. Les écrans neufs : `connexion`
  (`/connexion`, sans session, 120/45), `connexion-code` (`/connexion/code`), `connexion-pin`
  (`/connexion/pin`), `activation` (`/activation/[jeton]`, sans session, visitée avec un jeton
  invalide pour l'état de refus), `compte-telephone` (`/compte/telephone`, session), et
  `accueil-session` (`/`, session, sans persona, 120/45). P-05 et P-10 lisent le nouveau champ ;
  `web/app/core/ecrans.ts` le valide.
- **Motif** : FR-053 (chaque écran atteignable dans les deux moteurs), FR-056 (le poids de
  l'écran de connexion), SC-006 (aucun jeton dans le stockage : le test d'inspection s'exécute sur
  la session semée) ; « aucun serveur d'API n'est lancé pour les e2e aujourd'hui » (rapport T0b).
- **Écartées** : un double de l'API en Node (deux vérités du contrat) ; ouvrir une session par un
  raccourci de test côté serveur (un chemin d'ouverture qui n'existe pas en production).

## R-12 : La simulation garde ce qu'elle envoie

- **Décision** : `SimulationPasserelleSms` gagne `envoyes: list[EnvoiSimule(destinataire,
  texte, reference, envoye_le)]` en mémoire, et, si `NELO_SMS_JOURNAL` est posé, écrit chaque
  envoi en une ligne JSON dans ce fichier. Les tests Python lisent `application.state.passerelle_sms.envoyes` ;
  les e2e lisent le fichier. Rien de tout cela n'existe en production : la configuration est
  absente et une passerelle réelle n'a pas de journal.
- **Motif** : « la simulation ne conserve ni le destinataire ni le texte » (rapport T0a) ; la spec
  demande de « lire le code sur la passerelle simulée ».
- **Écartées** : une route de développement qui expose les messages (une route de plus au contrat,
  à protéger) ; lire Valkey depuis Playwright (un client Valkey en Node).

## R-13 : Le code personnel, son empreinte et ses protections

- **Décision** : Argon2id (`argon2.PasswordHasher(time_cost=2, memory_cost=19456,
  parallelism=1)`, le minimum recommandé, pour tenir sur un serveur contraint) sur le code
  personnel concaténé à l'identifiant du compte ; `verify` à temps constant. Le code seul n'ouvre
  rien : il faut le **secret d'appareil** (32 octets, cookie `nelo_appareils`, empreinte en
  Valkey), cinq tentatives (`pin_tentatives:{compte}`) puis un **verrou durable**
  (`pin_verrouille_le`) levé par une ouverture par code reçu ou par lien. Un compte suspendu
  ouvert par code personnel fait retirer son secret du cookie et de Valkey.
- **Motif** : quatre chiffres n'ont pas d'entropie ; la maquette A1 et le domaine les veulent
  pour l'usage fréquent. Ce qui protège est la conjonction : possession de l'appareil, cinq
  essais, verrou, et l'empreinte qui ne sert qu'en cas de fuite de la base.
- **Écartées** : six chiffres (contraire à la maquette, gain faible) ; un code personnel sans
  appareil connu (un mot de passe à quatre chiffres) ; le verrou en Valkey seul (une perte du
  magasin déverrouillerait).

## R-14 : La normalisation du numéro

- **Décision** : `phonenumbers.parse(brut, region)` avec `region =
  region_code_for_country_code(NELO_INDICATIF_DEFAUT)`, `is_valid_number`, puis
  `format_number(E164)`. Tout ce que le service reçoit (demande de code, création, changement)
  passe par `habilitations.normaliser(brut)` ; un échec lève `AUT_NUMERO_INVALIDE` (`422`).
  L'écran de connexion propose l'indicatif que `runtimeConfig.public.indicatifDefaut` porte,
  lu de `NUXT_PUBLIC_INDICATIF_DEFAUT`, la même valeur que le serveur, posée par le déploiement.
- **Motif** : FR-001 et FR-002 ; le format d'affichage du pack sert après la session, jamais
  avant.
- **Écartées** : lire l'indicatif du pack avant la session (le tenant n'est pas connu) ; une
  liste d'indicatifs codée dans l'interface (une littérale de pays).

## R-15 : Le pack de pays a enfin sa table

- **Décision** : `tenants.country_pack` ([02-domaine.md § 1.2](../../docs/02-domaine.md)) par
  la migration `0002_pack_et_administrateur` de `tenants`, avec deux packs semés : la Côte
  d'Ivoire, sous-ensemble utile au contexte (devise, langues, découpage, indicatif, vocabulaire
  de § 15), et le **pack fictif** du test d'agnosticité (échelle sur 10, deux périodes, un autre
  indicatif, un vocabulaire différent). `tenants.lire_pack(pays_code, version)` est l'interface ;
  `GET /moi/capacites` le projette en `CountryPackContexte`. Les valeurs de pays ne vivent que
  dans les lignes semées de la migration et dans les fixtures : la future porte P-09 devra
  exclure `migrations/*/versions/` et `tests/` de sa recherche, et c'est écrit ici pour T6a.
- **Motif** : FR-050 et principe V ; T0a nommait cette table comme provision.
- **Écartées** : un JSON de pack dans `modules/` (un fichier de pays dans le code) ; le pack en
  paramètre du catalogue (la table existe dans le domaine).

## R-16 : Le catalogue et les constantes de sécurité

- **Décision** : les trois clés `securite.pin_tentatives_max`, `securite.appareil_connu_jours`,
  `securite.invitation_validite_jours` entrent dans `catalogue_seed.CATALOGUE` et sont insérées
  par la migration `0002` de `tenants` ; `tests/isolation/test_deux_tenants.py` passe de 17 à
  20. Les constantes évaluées avant tout tenant vivent dans
  `modules/socle/habilitations/politique.py` (data-model § « Entités hors base »). Les secrets et
  les valeurs de déploiement vont dans `Configuration` : `secret_jeton` (obligatoire, sans
  défaut), `indicatif_defaut`, `cookies_secure`, `nom_produit`, `sms_journal`,
  `relais_de_confiance` ; `.env.exemple` les documente.
- **Motif** : FR-060 ; « aucune constante métier n'est écrite dans le code » ; une clé de tenant
  ne peut pas être lue avant que le tenant soit connu.

## R-17 : Les messages courts sont des gabarits, rédigés dans les deux langues

- **Décision** : `modules/socle/habilitations/messages/fr.json` et `en.json`, trois gabarits
  (`otp`, `invitation`, `changement_ancien_numero`), paramètres `{produit}`, `{etablissement}`,
  `{code}`, `{lien}`, `{minutes}`, `{jours}`, `{nouveau}` ; un test rend chaque gabarit avec les
  valeurs les plus longues possibles et exige moins de 160 caractères ; la langue est celle de la
  personne du compte (`personnes.lire_identite`), `fr` avant tout compte. Le lien d'invitation
  est `{NELO_URL_PUBLIQUE}/activation/{jeton}`.
- **Motif** : [ADR 013](../../docs/adr/013-le-sms-est-un-canal-de-premier-rang.md) et la
  constitution (XIII) : rédigé pour le canal, vérifié à l'enregistrement, pas à l'envoi. T4a
  reprendra ces gabarits dans `modele_message` ; ils sont écrits pour être déplacés, pas
  réécrits.

## R-18 : Les tests, et ce qu'ils exigent des fixtures de T0a

- **Décision** : `tests/conftest.py` étend `tenants_ab` : pour chaque tenant, une personne, une
  année active, un compte actif avec son affectation, et le pack posé ; une fixture `sessions_ab`
  ouvre une session par tenant **par l'API** (demande de code, lecture de `passerelle_sms.envoyes`,
  vérification) et rend jeton et cookies ; `tests/module_dore/outils.en_tetes(session, ...)`
  pose désormais `Authorization`. Les suites de T0a (`module_dore`, `isolation`, `idempotence`)
  passent par cette session ; le reparcours sous suspension inclut donc la session. Nouveaux
  paquets : `tests/authentification/` (code, code personnel, appareil, rotation, révocation,
  invitation, changement, partage, temps de réponse), `tests/contexte/`, `tests/en_tetes/`
  (les trois middlewares et la route d'essai pédagogique). Le test de contrat attendu lit **les
  deux** fichiers `openapi-attendu.yaml` (T0a et T1a). `test_contexte_au_contrat.py` retourne
  son assertion : une route sert désormais le contexte, et `ContexteCapacites` quitte
  `SCHEMAS_SANS_ROUTE` (FastAPI le publie par la route, la fusion lèverait sur la collision).
- **Motif** : FR-046 ; SC-003 exige une mesure (cent demandes alternées, écart des médianes) qui
  est un test marqué lent, exécuté dans `verifier.sh`.

## R-19 : Le contexte, servi

- **Décision** : `api/routes/moi.py::lire_contexte` compose `ContexteCapacites` par les
  interfaces : `habilitations.rattachements(compte)` (établissements et années par affectations
  vivantes), `tenants.lire_etablissements(ids)` avec sites (aucun site n'existe avant T2b :
  liste vide), cycles actifs et modules actifs (vides : `cycle_actif` et `module_actif` n'ont pas
  de table avant les tranches qui les créent ; le contexte porte `[]`, la coquille de T0b
  l'accepte), `administrateur` par `administrateur_compte_id` → `personnes.lire_identite`, avec le
  repli sur le nom et le téléphone de l'établissement (FR-049 ; `Administrateur.prenoms` de
  `modules/shared/contexte.py` accepte la chaîne vide : **le seul changement du schéma**, une
  contrainte relâchée, aucun champ ajouté ni retiré, P-03 régénéré) ; `annees` par
  `annees.lire_annees` filtrées par les affectations ; `country_pack` par `tenants.lire_pack` ;
  `parametres_effectifs` projetés en `{cle: valeur}` depuis `lire_parametres_effectifs` ;
  `capacites`, `acces_nominatifs`, `alertes` vides.
- **Motif** : FR-047 à FR-050 ; principe XI (chaque lecture par l'interface du propriétaire).

## R-20 : La route qui liste les comptes d'un appareil

- **Décision** : `GET /auth/appareil` rend, pour les secrets du cookie `nelo_appareils` encore
  connus, `{compte_id, nom, prenoms, pin_defini}` ; jamais un numéro. Sans elle, l'écran du code
  personnel ne peut proposer un nom (FR-021). **Diff appliqué** sur [03-api.md § 2.1](../../docs/03-api.md).
- **Écartées** : les noms dans le cookie (périmés au premier changement) ; demander le numéro
  avant le code personnel (contraire à FR-021 et à la maquette).

## R-21 : Les écrans, la coquille et le choix sur l'appareil

- **Décision** : pages `sansCoquille` assemblées avec les composants de T0b, sans composant neuf :
  `connexion.vue` (numéro ; ou, si `GET /auth/appareil` rend des comptes, l'écran du code
  personnel d'abord, avec le lien « un autre numéro »), `connexion/code.vue` (le code, le compte
  à rebours par `CanonAlerte` niveau `attente`, l'orientation vers le secrétariat, et le choix de
  la personne quand `ChoixRequis`), `connexion/pin.vue` (définition), `activation/[jeton].vue`,
  `compte/telephone.vue`. Le champ du numéro et des codes est `CanonChamp type="nombre"`
  (`inputmode="decimal"` existe ; `inputmode="numeric"` et `autocomplete="one-time-code"` sont
  deux attributs ajoutés à `Champ.vue` sous une prop `saisie: 'code'`, pas un composant neuf).
  `CoquilleEntete.vue` reçoit `etablissements`, `annees` et émet `changerEtablissement`,
  `changerAnnee`, `deconnexion` ; `app.vue` relit le contexte au changement. Le choix
  d'établissement et d'année vit sur l'appareil par `core/appareil/choix.ts` (le patron de
  `core/theme.ts`, prend `Stockage`) ; au rendu serveur, l'en-tête d'établissement envoyé est
  celui du cookie **`nelo_etablissement`** posé par le client à chaque choix (non `HttpOnly`,
  sans secret : un identifiant d'établissement que le compte a le droit de voir), sinon le premier
  rattachement. Les clés `fr`/`en` sous l'espace `session.` ; le lexique s'étend.
- **Motif** : FR-051 à FR-057 ; la coquille attend un contexte au rendu serveur, et le choix
  mémorisé en `localStorage` n'y est pas lu (écart E-13 de T0b) : sans cookie, un compte à deux
  établissements verrait le premier puis l'autre à l'hydratation.
- **Écartées** : un composant « saisie de code en cases » (un composant neuf, arrêt de cycle
  pour un gain visuel) ; le choix d'établissement côté serveur (FR-051 l'interdit).

## R-22 : Ce que la tranche ne fait pas, et le dit

- La levée de suspension, la gestion de ses appareils, le verrouillage par inactivité, la
  biométrie, l'appel vocal, le profil : hors périmètre par la spec.
- Le fuseau horaire dans la vivacité d'une affectation (R-03) : T1b.
- Les portes P-08 et P-09 : toujours sans matière ; R-15 laisse une consigne à T6a.
- Une seconde construction de production pour prouver l'élagage de la démonstration : remplacée
  par la mesure P-10 de l'accueil réel (R-10).

## Après la revue visuelle : sept écarts tranchés

La planche ([spec.md § Revue visuelle](spec.md#revue-visuelle), validée le 2026-09-17) a rendu
visibles sept écarts. Aucun n'est un choix produit : chacun se tranche par le corpus ou par une
contrainte déjà écrite, et chacun est reporté dans la spec.

| | Écart | Décision | Ce qui tranche |
|---|---|---|---|
| **E-01** | Avant la session, le tenant n'est pas connu : ni nom d'établissement sur l'écran du numéro, ni numéro du secrétariat sur la carte du code | L'écran du numéro porte le nom du produit ; la carte oriente vers le secrétariat **sans numéro** | La contrainte non négociable ; un numéro de déploiement serait celui de l'éditeur |
| **E-02** | Six cases et pavé numérique d'A1 | Refusés ; `CanonChamp` avec `saisie: 'code'` (`inputmode="numeric"`, `autocomplete="one-time-code"`) | [05-design.md § 9.1](../../docs/05-design.md), cas 2 : les composants existent, on assemble |
| **E-03** | Trois états sans code ni mot | `ANNEE_ACTIVE` (neutre) et `ANNEE_PREPARATION` (ocre) dans `ETATS_METIER` et au lexique ; compte et partage « à venir » | Un état porte une forme et un mot ; aucun écran de T1a n'affiche un état de compte |
| **E-04** | Le refus « identifiant déjà utilisé » n'est pas prévisible | Libre-service : refus **différé à la vérification du code** (jamais d'oracle sur les numéros). Secrétariat : `POST /comptes/verification`, **diff appliqué** sur [03-api.md § 2.5](../../docs/03-api.md) | La contrainte non négociable, puis la règle 3 de [03-api.md § 3](../../docs/03-api.md) |
| **E-05** | Pas de place pour « Fermer la session » à 390 px | L'avatar ouvre le **menu de compte** ; dès `md`, le geste est aussi direct dans l'en-tête | FR-015 reformulée : accessible en un geste depuis l'en-tête, jamais enfoui |
| **E-06** | « SMS » ou « message court » | **SMS** à l'écran ; « message court » reste un mot de documentation | A1, la pastille de canal (`canal.SMS`), le terrain |
| **E-07** | Le mot d'écran du compte suspendu | « Votre accès est fermé » + administrateur nommé quand le compte est connu ; « Votre session est terminée » + « Ouvrir une nouvelle session » ; rien à la demande de code | [05-design.md § 8.2](../../docs/05-design.md) règle 1 ; [02-domaine.md § 3.4](../../docs/02-domaine.md) « aucune capacité » |

R-21 s'en trouve précisé (le menu de compte, la prop `saisie`), R-07 inchangé (E-04 ne touche que
`/moi/telephone/verification`), et le lexique gagne ses entrées à `implement`.

## Diffs sur les documents projet

Appliqués le 2026-09-17, tracés au journal ; chacun dérive du corpus ou d'une contrainte
mécanique du dépôt.

| Fichier | Quoi | Statut |
|---|---|---|
| `02-domaine.md § 1.2, § 16, § 17` | administrateur désigné, états du compte, trois clés | Appliqué à `specify` |
| `03-api.md § 1.8, § 2.1, § 2.2, § 2.5` | `API_LIMITE_DEBIT`, neuf codes `AUT_`, `/moi/telephone`, `/comptes` | Appliqué à `specify` |
| `02-domaine.md § 3.2` | `affectation` porte `etablissement_id` (R-03) | **Appliqué** |
| `03-api.md § 2.1` | `GET /auth/appareil` (R-20) | **Appliqué** |
| `03-api.md § 2.5` | `POST /comptes/verification` (E-04) | **Appliqué** |
| `01-stack.md § 2.1, § 3` | l'état du dépôt et la commande de l'API en test | À `implement`, avec le code |
| `progress.md` | Q30 ouverte à `specify` ; l'entrée du plan | Fin de session |
