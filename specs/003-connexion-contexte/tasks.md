# Tâches : Se connecter et savoir où l'on est (T1a)

**Entrée** : les documents de conception de `specs/003-connexion-contexte/` : [plan.md](plan.md),
[spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/openapi-attendu.yaml](contracts/openapi-attendu.yaml),
[contracts/interfaces-python.md](contracts/interfaces-python.md), [quickstart.md](quickstart.md),
et les huit artboards validés de [design/](design/) avec leurs sept écarts tranchés (E-01 à E-07).

**Tests** : la spécification les exige (FR-045, FR-061, FR-062, SC-003 à SC-011, la définition de
terminé de [01-stack.md § 8.3](../../docs/01-stack.md)). Chaque story livre ses tests **avant** son
implémentation, et ils doivent échouer avant qu'elle n'existe. C'est la première frontière de
sécurité du produit : un test qui passe avant l'implémentation est un test faux, et un
comportement de sécurité sans test n'existe pas.

**Organisation** : par user story, dans l'ordre de priorité de la spec. La règle de T0a traverse
toutes les phases : **les portes se construisent avec ce qu'elles vérifient**, et
`scripts/verifier.sh` reste vert à chaque point de contrôle. Le lexique, les clés `fr`/`en` et les
gabarits de messages s'écrivent avec le code qu'ils servent, jamais après.

## Format : `[ID] [P?] [Story] Description`

- **[P]** : parallélisable, fichiers différents, aucune dépendance sur une tâche inachevée
- **[Story]** : la user story servie (US1 à US8)
- Chaque description porte son chemin exact, relatif à la racine du dépôt

## Conventions de chemins

Celles de [plan.md](plan.md) « Structure du projet » : `modules/socle/{habilitations,personnes,annees,tenants,communication}/`,
`modules/shared/`, `migrations/<schema>/`, `api/`, `api/routes/`, `tests/{authentification,en_tetes,contexte,isolation,module_dore,portes}/`,
`scripts/`, `scripts/portes/`, `web/app/{core,composables,components/canon,pages,plugins,middleware}/`,
`web/server/api/v1/`, `web/tests/{unit,e2e,portes}/`, `docs/`. Tables, colonnes, fonctions et
fichiers en français sans accent dans les identifiants ; accents partout ailleurs. **Aucun tiret
cadratin**, nulle part. Chaque fonction de `acces.py` est exercée par un test, ou P-12 échoue en la
nommant.

---

## Phase 1 : Mise en place (infrastructure partagée)

**But** : les trois bibliothèques, les trois paquets vides, la configuration et les constantes de
sécurité existent ; P-02, P-04, P-07 et P-11 sont verts ; rien ne sert encore.

- [ ] T001 Ajouter à `pyproject.toml` (racine) les dépendances épinglées `phonenumbers==9.0.39`, `PyJWT==2.14.0`, `argon2-cffi==25.1.0` (réépingler si une version stable plus récente est parue, [research.md R-01](research.md)), et les trois membres `modules/socle/habilitations`, `modules/socle/personnes`, `modules/socle/annees` dans `[tool.uv.workspace].members` ; `uv lock` ; commiter `uv.lock` ; vérifier `scripts/portes/p-02.sh` et `scripts/portes/p-07.sh` verts
- [ ] T002 Créer les trois paquets vides sur le modèle de `modules/socle/tenants/` : pour chacun un `pyproject.toml` déclaratif (`[tool.uv] package = false`, dépendance `modules/shared` en `{ workspace = true }`), un `__init__.py` avec `__all__ = []` et sa docstring « l'interface de service, et rien d'autre », un `tables.py` avec `metadata = MetaData(schema=...)`, un `acces.py` et un `service.py` vides, un `schemas.py` vide ; déclarer les trois dans `api/pyproject.toml` ; vérifier `scripts/portes/p-04.sh` et `p-11.sh` verts (`tests/frontieres/test_declarations.py` et `test_graphe.py`)
- [ ] T003 [P] Écrire `modules/socle/habilitations/politique.py` : la classe gelée `PolitiqueSecurite` avec les constantes de [data-model.md § Entités hors base](data-model.md) (`OTP_LONGUEUR = 6`, `OTP_VALIDITE = timedelta(minutes=10)`, `OTP_TENTATIVES = 5`, `OTP_RENVOI = timedelta(seconds=60)`, `OTP_PAR_HEURE_PAR_NUMERO = 5`, `OTP_PAR_HEURE_PAR_CLIENT = 20`, `PIN_LONGUEUR = 4`, `FENETRE_CONCURRENCE_REFRESH = timedelta(seconds=10)`, `DISPENSE_PIN_COURANT = timedelta(minutes=10)`, `JETON_ACCES = timedelta(minutes=60)`), une instance `POLITIQUE`, et une docstring qui renvoie à Q30 ; test `tests/authentification/test_politique.py` : chaque valeur est celle de la spec, et le module ne lit aucune configuration
- [ ] T004 [P] Étendre `api/configuration.py` : `secret_jeton: str` (**obligatoire, sans défaut**), `indicatif_defaut: str` (obligatoire), `cookies_secure: bool = True`, `nom_produit: str = "Nelo"`, `url_publique: str`, `sms_journal: Path | None = None`, `relais_de_confiance: str | None = None` ; documenter chaque variable `NELO_*` dans `.env.exemple` avec un secret d'exemple et `NELO_COOKIES_SECURE=false` ; adapter `tests/conftest.py` pour poser `NELO_SECRET_JETON` et `NELO_INDICATIF_DEFAUT` avant l'import de la configuration
- [ ] T005 [P] Étendre `modules/shared/erreurs.py` : `ErreurMetier.en_tetes: dict[str, str]` (défaut vide) ; `api/erreurs.py` : `_refus_metier` pose ces en-têtes sur la `JSONResponse`, et `envoyer_erreur_asgi(..., en_tetes: dict[str, str] | None = None)` les ajoute ; test `tests/en_tetes/test_erreurs_en_tetes.py` : un `ErreurMetier(..., statut=429, en_tetes={"Retry-After": "42"})` levé par une route d'essai sort avec l'en-tête
- [ ] T006 Étendre `scripts/bd-vierge.sh` : appliquer `alembic -c migrations/<schema>/alembic.ini upgrade head` en boucle sur `tenants`, `personnes`, `annees`, `habilitations` (dans cet ordre, les noyaux avant ce qui les référence) ; étendre `scripts/portes/p12_acces_exerces.py::DECLARATIONS` aux quatre schémas et à leurs `tables.py` ; vérifier P-01 et P-12 encore verts sur des schémas vides (un dossier de migrations sans version est un échec de P-01 : créer les dossiers seulement à la phase 2, ou avec une migration vide et réversible)

---

## Phase 2 : Fondations (prérequis bloquants)

**But** : les quatre schémas migrés sous RLS avec leurs seeds, les noyaux et leurs interfaces,
l'outbox générique, la simulation qui garde ses messages, les fixtures de test, et côté web le
relais, le client et la source de contexte, prêts à recevoir la première session.

**⚠️ CRITIQUE** : aucune story ne commence avant la fin de cette phase.

### Les migrations et les tables

- [ ] T007 Écrire `migrations/personnes/{alembic.ini,env.py}` et `migrations/personnes/versions/0001_noyau_personnes.py` sur le modèle de `migrations/tenants/` : `personnes.personne` ([data-model.md § personnes](data-model.md)) et `personnes.evenement_outbox` (copie de celle de `tenants`), `ENABLE` + `FORCE ROW LEVEL SECURITY`, politiques `isolation_tenant` (et les trois de l'outbox), `GRANT USAGE` et `SELECT, INSERT, UPDATE` à `nelo_app`, `downgrade` complet ; déclarer les mêmes tables dans `modules/socle/personnes/tables.py`
- [ ] T008 [P] Écrire `migrations/annees/{alembic.ini,env.py}` et `migrations/annees/versions/0001_noyau_annees.py` : `annees.annee_scolaire` avec `CHECK` sur `etat`, les **deux index partiels d'unicité** (`active`, `preparation` par `(tenant_id, etablissement_id)`), `annees.evenement_outbox`, RLS, politiques, grants, `downgrade` ; `modules/socle/annees/tables.py`
- [ ] T009 [P] Écrire `migrations/habilitations/{alembic.ini,env.py}` et `migrations/habilitations/versions/0001_compte_affectation.py` : `habilitations.compte` (unicité `(tenant_id, personne_id)`, index `(tenant_id, identifiant)` et `(identifiant)`, `CHECK` sur `statut`), `habilitations.affectation` (FK **intra-schéma** vers `compte`, index `(tenant_id, compte_id, etablissement_id, annee_id)`), `habilitations.evenement_outbox`, RLS, politiques, grants, et les trois fonctions `SECURITY DEFINER` `comptes_par_identifiant(text)`, `compte_par_invitation(text)`, `compte_par_id_sans_tenant(uuid)` (`STABLE`, `search_path = pg_catalog, pg_temp`, `REVOKE ... FROM PUBLIC`, `GRANT EXECUTE` à `nelo_app`), `downgrade` ; `modules/socle/habilitations/tables.py`
- [ ] T010 Écrire `migrations/tenants/versions/0002_pack_et_administrateur.py` : `ALTER TABLE tenants.etablissement ADD COLUMN administrateur_compte_id uuid` ; table `tenants.country_pack` avec politique `lecture_tenantee` et `GRANT SELECT` ; `DROP FUNCTION tenants.tenant_de_etablissement` ; insertion des trois clés `securite.pin_tentatives_max` (5), `securite.appareil_connu_jours` (90), `securite.invitation_validite_jours` (7) au catalogue ; seed des **deux packs** (Côte d'Ivoire : devise `XOF` exposant 0 symbole « F », langues `fr`,`en`, découpage `TRIMESTRES`, indicatif `225`, le vocabulaire des dix-sept codes de [02-domaine.md § 15](../../docs/02-domaine.md) ; pack fictif `ZZ` : échelle sur 10 en réserve, deux périodes, exposant 2, indicatif `999`, un vocabulaire où « classe » se dit autrement), `downgrade` complet ; mettre à jour `modules/socle/tenants/tables.py` et `catalogue_seed.CATALOGUE` ; passer `tests/isolation/test_deux_tenants.py` de `== 17` à `== 20` ; mettre `tests/portes/test_security_definer.py::ATTENDUES` à `{tenants_pour_travailleur, comptes_par_identifiant, compte_par_invitation, compte_par_id_sans_tenant}` ; vérifier P-01 vert : quatre schémas, aucune clé étrangère traversante

### Les noyaux, l'outbox générique, le pack

- [ ] T011 [P] Écrire `modules/shared/outbox.py` : `prendre(connexion, table, tenant_id, n)` (la CTE `MATERIALIZED` avec `FOR UPDATE SKIP LOCKED` de T0a), `marquer_traite`, `marquer_echec`, `reprendre_pris_orphelins`, `reprendre_en_echec`, `inserer(connexion, table, tenant_id, evenement)`, paramétrés par la `Table` ; faire appeler ces fonctions par `modules/socle/tenants/acces.py` sur sa table (les fonctions de `tenants/acces.py` restent, P-12 les exerce déjà) ; `modules/shared/__init__.py` n'exporte rien de neuf (les modules importent `modules.shared.outbox`) ; test `tests/outbox/test_outbox_generique.py` : la même prise sur `tenants.evenement_outbox` et sur `habilitations.evenement_outbox`
- [ ] T012 [P] Écrire `modules/socle/personnes/{acces.py,service.py,schemas.py,__init__.py}` : `Identite(nom, prenoms, langue)`, `lire_identite`, `lire_identites`, `creer_personne` ([contracts/interfaces-python.md](contracts/interfaces-python.md)), fonctions d'accès `inserer_personne`, `lire_personne`, `lire_personnes` ; test `tests/contexte/test_personnes_noyau.py` : création, lecture, identité inconnue → `None`, langue hors `^[a-z]{2}$` refusée
- [ ] T013 [P] Écrire `modules/socle/annees/{acces.py,service.py,schemas.py,__init__.py}` : `Annee(id, libelle, etat)`, `lire_annees`, `etablissement_de_annee`, `creer_annee` ; fonctions d'accès `inserer_annee`, `lire_annees_etablissement`, `lire_annee` ; test `tests/contexte/test_annees_noyau.py` : deux années `active` sur le même établissement refusées par l'index partiel (`IntegrityError` traduite en `ErreurMetier("ANN_ANNEE_ACTIVE_UNIQUE", statut=409)`), `preparation` idem, aucune transition disponible
- [ ] T014 Étendre `modules/socle/tenants/` : `lire_pack(pays_code, version) -> Pack` (devise, langues, decoupage, telephone, vocabulaire, depuis `contenu`), `lire_etablissements(tenant_id, ids)` (nom, telephone, fuseau_horaire, administrateur_compte_id), `designer_administrateur(tenant_id, etablissement_id, compte_id | None)` ; retirer `tenant_de_etablissement` du service et de `__init__.py` (**garder** `acces.appeler_tenant_de_etablissement` supprimée aussi : la fonction SQL n'existe plus) ; fonctions d'accès `lire_pack`, `lire_etablissements_par_ids`, `poser_administrateur` ; tests `tests/module_dore/test_pack.py` (les deux packs semés se lisent, un pack inconnu rend `None`) et `test_administrateur.py`
- [ ] T015 [P] Étendre `modules/socle/communication/passerelle_sms.py` ([research.md R-12](research.md)) : `EnvoiSimule`, `SimulationPasserelleSms.envoyes`, paramètre `journal: Path | None` qui ajoute une ligne JSON (`destinataire`, `texte`, `reference`, `envoye_le`) par envoi ; `api/main.py` passe `configuration.sms_journal` ; exporter `EnvoiSimule` ; test `tests/simulations/test_passerelle_sms.py` étendu : `envoyes` garde destinataire et texte, le journal s'écrit quand le chemin est posé, jamais sinon

### Les fixtures et le jeu d'essai

- [ ] T016 Étendre `tests/conftest.py::tenants_ab` : pour chaque tenant, `creer_personne` (nom, prénoms, langue `fr` pour A, `en` pour B), `creer_annee` active (libellé `2026-2027`, dates de l'année en cours) et une en `preparation`, un compte `actif` (identifiant E.164 distinct par tenant, `+2250700000001` et `+2250700000002`), une affectation vivante sur l'année active et une sur l'année en préparation, `designer_administrateur` du compte sur l'établissement ; le tenant A porte le pack `CI`, le tenant B le pack fictif `ZZ` (`creer_tenant(..., pays_code="ZZ")`) ; étendre `DeuxTenants` (`personne_a`, `compte_a`, `numero_a`, `annee_a`, `annee_prep_a`, idem B) ; vérifier que `tests/isolation/test_deux_tenants.py` voit une ligne par table neuve et par tenant, et qu'il passe
- [ ] T017 [P] Étendre `scripts/jeu_essai.py` et `scripts/bd-vierge.sh --avec-jeu-d-essai` : les mêmes objets que T016 pour un usage manuel et pour les e2e, plus un **second établissement** du tenant A auquel le compte A est rattaché (US4-3), une personne sans compte (`PERSONNE_NOUVELLE`), un compte du tenant fictif ; impression en forme `export` de `ETAB_A`, `ETAB_A2`, `ETAB_B`, `NUMERO_A`, `NUMERO_B`, `NUMERO_FICTIF`, `COMPTE_A`, `PERSONNE_NOUVELLE` ([quickstart.md](quickstart.md))

### Côté web : le relais, le client, la source, la garde

- [ ] T018 Écrire `web/server/api/v1/[...].ts` ([research.md R-09](research.md)) : `proxyRequest` de h3 vers `useRuntimeConfig().apiBase` ; lit le cookie `nelo_acces` et pose `Authorization: Bearer` ; pose `X-Forwarded-For` ; transmet tels quels les `Set-Cookie` de l'API ; sur une réponse JSON portant `jeton_acces`, range le jeton dans le cookie `nelo_acces` (`HttpOnly; Secure` selon `runtimeConfig.cookiesSecure; SameSite=Strict; Path=/; Max-Age=expire_dans`) et **le retire du corps** ; sur `DELETE /auth/session`, efface `nelo_acces` ; `web/nuxt.config.ts` : `runtimeConfig.apiBase` (`NUXT_API_BASE`, défaut `http://localhost:8000`), `runtimeConfig.cookiesSecure`, `runtimeConfig.public.indicatifDefaut` (`NUXT_PUBLIC_INDICATIF_DEFAUT`), `vite.define.__NELO_DEMONSTRATION__` depuis `process.env.NELO_DEMONSTRATION === '1'` ; `web/app/types/global.d.ts` déclare la constante
- [ ] T019 [P] Écrire `web/app/core/api/uuid7.ts` (un UUID v7 depuis `crypto.getRandomValues` et l'horloge, sans dépendance ; test `web/tests/unit/uuid7.test.ts` : version 7, ordre croissant) et `web/app/core/api/client.ts` : `appeler(methode, chemin, { corps?, etablissement?, annee?, ecriture? })` sur `$fetch` relatif `/api/v1/...`, pose `X-Nelo-Etablissement`, `X-Nelo-Annee`, `X-Nelo-Requete` (v7) sur les écritures, traduit une `EnveloppeErreur` en `ErreurApi(code, details, statut)`, et sur `401 AUT_JETON_INVALIDE` appelle une fois `POST /auth/rafraichissement` puis rejoue ; `web/app/composables/useApi.ts` ; test `web/tests/unit/client-api.test.ts` avec un `$fetch` factice : en-têtes posés, rejeu unique après rafraîchissement, aucun rejeu en boucle
- [ ] T020 [P] Écrire `web/app/core/contexte/api.ts` : `class SourceApi implements SourceContexte` qui appelle `GET /moi/capacites` avec l'établissement choisi (cookie `nelo_etablissement` au rendu serveur via `useRequestHeaders`, sinon le stockage d'appareil, sinon aucun en-tête et le serveur répond `400` : la source demande alors le contexte sans établissement **n'existe pas**, elle lit d'abord la liste par le premier rattachement renvoyé dans l'erreur `TEN_ETABLISSEMENT_REQUIS.details.etablissements` ; voir T053) ; au rendu serveur, `useRequestFetch()` ; sur `401`, rend `null` ; test `web/tests/unit/contexte-source.test.ts` étendu
- [ ] T021 Étendre `web/app/plugins/contexte.ts` ([research.md R-10](research.md)) : `SourceDemonstration` si `__NELO_DEMONSTRATION__ && route.query.persona`, sinon `SourceApi` ; un contexte `null` ne lève plus dans le greffon ; écrire `web/app/middleware/session.global.ts` : sans contexte et hors page `sansCoquille`, `navigateTo('/connexion')` ; `web/app/composables/useContexte.ts` lève toujours si une page à coquille lit un contexte nul (la garde l'en empêche) ; test `web/tests/unit/choix-source.test.ts` sur la fonction pure de choix
- [ ] T022 Étendre `scripts/avec-serveur-dev.sh` ([research.md R-11](research.md)) : lance `uvicorn api.main:app --port ${NELO_PORT_API_TEST:-8010}` avec `NELO_BD_NOM=nelo_web_test` (recréée par `scripts/bd-vierge.sh --avec-jeu-d-essai`, dont il capture les `export`), `NELO_VALKEY_URL` sur la base 2, `NELO_SMS_JOURNAL` vers un fichier temporaire exporté en `NELO_SMS_JOURNAL`, `NELO_COOKIES_SECURE=false`, `NELO_SECRET_JETON` de test ; attend `/api/v1/sante` ; construit ou lance l'application avec `NUXT_API_BASE` sur ce port et `NELO_DEMONSTRATION=1` ; arrête tout à la sortie ; `scripts/verifier.sh` construit avec `NELO_DEMONSTRATION=1` ; vérifier que P-05, P-10 et les e2e de T0b passent inchangés sous ce script
- [ ] T023 [P] Étendre `web/app/components/canon/Champ.vue` d'une prop `saisie?: 'texte' | 'code'` (E-02) : `code` pose `inputmode="numeric"`, `autocomplete="one-time-code"`, `pattern="[0-9]*"`, police mono, sans nouvel état ; mettre à jour `docs/design/composants.md` (le champ : la saisie de code) et `web/app/pages/style.vue` (un exemple) ; test unitaire de rendu de la prop dans `web/tests/unit/composants-etats.test.ts`
- [ ] T024 [P] Étendre `web/ecrans.json` et `web/app/core/ecrans.ts` d'un champ optionnel `session: boolean` (validé : booléen, incompatible avec `personas`) ; étendre `web/tests/portes/outils.ts::visites()` pour distinguer les visites avec et sans session ; écrire `web/tests/session.setup.ts` (projet Playwright `setup` : `POST /auth/otp` pour `NUMERO_A`, lecture du dernier code dans `NELO_SMS_JOURNAL`, `POST /auth/otp/verification`, enregistrement de `storageState` dans `web/test-results/session.json`) et le déclarer en dépendance des projets `chromium`, `webkit`, `p10` dans `web/playwright.config.ts` ; tant qu'aucune route n'existe, le setup échoue : c'est attendu, US1 le rend vert

**Point de contrôle** : `scripts/verifier.sh` vert hors le setup Playwright (à désactiver par
une variable jusqu'à US1, jamais en commentant) ; quatre schémas migrés ; fixtures en place.

---

## Phase 3 : User Story 1, ouvrir sa session par un code reçu par message court (Priorité : P1) 🎯 MVP

**But** : une personne saisit son numéro, reçoit un code par l'outbox, le vérifie, et une session
s'ouvre ; la demande répond de la même façon quel que soit le numéro.

**Test indépendant** : demander un code pour `NUMERO_A` et pour un numéro que personne ne porte,
comparer les deux réponses ; lire le code dans `passerelle_sms.envoyes`, le vérifier, constater la
session ; rejouer, expirer, épuiser.

### Tests pour la User Story 1

- [ ] T025 [P] [US1] Écrire `tests/authentification/outils.py` : `demander(client, numero, requete_id=None)`, `code_recu(application, numero)` (le dernier envoi de `passerelle_sms.envoyes` vers ce numéro, extrait par expression régulière), `ouvrir(client, application, numero, compte_id=None) -> Session(jeton, cookies, compte)`, `en_tetes(session, etablissement_id, *, ecriture=False, annee_id=None)`
- [ ] T026 [P] [US1] Écrire `tests/authentification/test_demande_code.py` : `204` sans corps pour un numéro connu **et** pour un inconnu, en-têtes identiques (hors `date`), un envoi pour le connu, aucun pour l'inconnu, aucun pour un compte suspendu, un envoi pour un compte `invite` ; `422 AUT_NUMERO_INVALIDE` sur `0708` et sur `+999` ; `429 API_LIMITE_DEBIT` avec `Retry-After` à la seconde demande dans la minute, à la sixième dans l'heure, et à la vingt-et-unième par client ; le rejeu avec la même `X-Nelo-Requete` n'ajoute aucun envoi ; l'événement `habilitations.otp.demande` est dans l'outbox du tenant A avec `envoi_id` et sans le code
- [ ] T027 [P] [US1] Écrire `tests/authentification/test_verification_code.py` : session ouverte (`jeton_acces` JWT HS256 vérifiable avec le secret, `expire_dans` 3600, cookie `nelo_refresh` `HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth`, cookie `nelo_appareils`) ; `401 AUT_OTP_INVALIDE` avec `details.tentatives_restantes` décroissant ; `401 AUT_OTP_TENTATIVES_EPUISEES` à la cinquième et le code détruit ; `401 AUT_OTP_EXPIRE` après expiration (TTL posé à la main dans Valkey) ; un second code remplace le premier ; un compte `invite` passe `actif` (FR-033) avec l'événement `compte.active` ; `derniere_connexion` posée ; `session:{sid}` et `sessions_compte:{compte}` existent
- [ ] T028 [P] [US1] Écrire `tests/authentification/test_reponse_identique.py` (marqué `lent`) : cent demandes alternées connu / inconnu, réponses identiques en statut, corps et en-têtes, **écart des médianes de temps sous 50 ms** (SC-003) ; `scripts/verifier.sh` l'inclut
- [ ] T029 [P] [US1] Écrire `tests/authentification/test_messages.py` : chaque gabarit de `modules/socle/habilitations/messages/{fr,en}.json` rendu avec les valeurs les plus longues (nom de produit de 30 caractères, code, lien de 60 caractères, numéro E.164 de 16 caractères) tient sous **160 caractères**, sans abréviation, et les deux fichiers ont les mêmes clés
- [ ] T030 [P] [US1] Écrire `tests/outbox/test_consommateur_envoi.py` : l'aiguilleur passe `habilitations.otp.demande` au consommateur d'envoi, qui lit `otp_texte:{envoi_id}`, envoie par la passerelle, efface le texte, et marque `traite` ; une seconde livraison du même événement n'envoie rien ; une passerelle `INDISPONIBLE` met l'événement `en_echec` et le tour suivant le reprend ; un événement d'un autre type va au journal

### Implémentation de la User Story 1

- [ ] T031 [P] [US1] Écrire `modules/socle/habilitations/normalisation.py` : `normaliser(brut, indicatif_defaut) -> str` par `phonenumbers` ([research.md R-14](research.md)), `ErreurMetier("AUT_NUMERO_INVALIDE", statut=422, champ="identifiant")` ; test `tests/authentification/test_normalisation.py` : `07 08 12 34 56` avec indicatif `225` → `+2250708123456`, `+225 07...` idem, `+33612345678` accepté, `12` refusé
- [ ] T032 [P] [US1] Écrire `modules/socle/habilitations/messages/fr.json` et `en.json` (`otp`, `invitation`, `changement_ancien_numero`, [research.md R-17](research.md)) et `modules/socle/habilitations/gabarits.py` : `rendre(cle, langue, **params)`, langue `fr` si inconnue
- [ ] T033 [US1] Écrire les fonctions d'accès de `modules/socle/habilitations/acces.py` pour cette story : `inserer_compte`, `lire_compte`, `appeler_comptes_par_identifiant` (par `sans_tenant()`), `poser_statut`, `poser_derniere_connexion`, `inserer_evenement` (par `modules.shared.outbox`), `inserer_affectation`, `affectation_vivante`, `lire_rattachements` ; et `schemas.py` : `CorpsDemandeCode`, `CorpsVerificationCode`, `ChoixCompte`, `ChoixRequis`, `SessionOuverte`, `ReponseVerificationCode` (union discriminée par `resultat`), tous `extra="forbid"`
- [ ] T034 [US1] Écrire `modules/socle/habilitations/session.py` : `ouvrir_session(compte, tenant_id, canal, appareil, valkey, politique, duree) -> SessionOuverte` (clé `session:{sid}`, `sessions_compte`, refresh aléatoire et `refresh:{sha256}`, JWT HS256 via PyJWT avec `sub`, `ten`, `sid`, `iat`, `exp`, `jti`), `verifier_jeton_acces(jeton, secret) -> JetonAcces`, `session_valide(session_id, compte_id, valkey)`, `revoquer_session(session_id, valkey)`, `revoquer_toutes(compte_id, valkey)` ; la durée vient de `tenants.valeur_effective("securite.duree_session_minutes")` lue par le service ; tests `tests/authentification/test_session.py` (jeton falsifié, expiré, session absente, révocation)
- [ ] T035 [US1] Écrire `api/limitation.py` : `compter(valkey, cle, plafond, fenetre) -> int | None` (`INCR` + `EXPIRE NX`, rend les secondes de reprise quand le plafond est atteint) et `adresse_client(scope, relais_de_confiance)` ([research.md R-05](research.md)) ; test `tests/authentification/test_limitation.py`
- [ ] T036 [US1] Écrire `modules/socle/habilitations/service.py::demander_code` et `verifier_code` ([research.md R-07](research.md), [contracts/interfaces-python.md](contracts/interfaces-python.md)) : normalisation, trois limites (`429` avec `en_tetes={"Retry-After": ...}`), `comptes_par_identifiant`, génération `secrets.randbelow(10**6)` formatée sur six chiffres, empreinte SHA-256 salée par `envoi_id`, `otp:{identifiant}` et `otp_texte:{envoi_id}` avec TTL, événement `otp.demande` dans `transaction(tenant_du_premier_compte)` ; **le même travail sans écriture** quand aucun compte ; `verifier_code` avec les quatre refus, l'activation d'un compte `invite`, `ChoixRequis` quand plusieurs comptes (les noms par `personnes.lire_identites`), l'ouverture par `session.ouvrir_session`, l'événement `session.ouverte` ; `__init__.py` exporte le tout
- [ ] T037 [US1] Écrire `api/consommateurs.py::aiguilleur(passerelle, valkey, configuration)` ([research.md R-08](research.md)) et `modules/socle/habilitations/service.py::consommer_envoi` (lit le texte, rend le gabarit dans la langue de la charge, `passerelle.envoyer`, efface, idempotent) ; `api/travailleur.py::un_tour` parcourt les quatre tables d'outbox par `modules.shared.outbox` (chaque module expose `consommer_lot` et `reprendre_evenements` sur sa table) ; `api/main.py` construit `Travailleur(configuration, aiguilleur(...))`
- [ ] T038 [US1] Écrire `api/asgi.py` (`CHEMINS_LIBRES` étendu de `/auth/`, `en_tete`, `chemin_de_route`, repris de `api/tenant_provisoire.py`) et `api/session.py` : le middleware ASGI de [research.md R-04](research.md) (chemins libres ; `Authorization` absent ou sans `Bearer` → `401 AUT_JETON_MANQUANT` ; signature ou expiration → `401 AUT_JETON_INVALIDE` ; `session_valide` faux → `401 AUT_SESSION_REVOQUEE` ; dépose `compte_id`, `tenant_id`, `session_id` dans `scope["state"]`) ; adapter `api/idempotence.py` : clé `idem:auth:{requete_id}` quand `etat` n'a pas de `tenant_id` sur un chemin libre ; `api/main.py` ajoute `Session` **sans retirer encore** `TenantProvisoire` (US2 le fait) ; test `tests/en_tetes/test_session_middleware.py` (les trois `401`, chemins libres, `/sante`)
- [ ] T039 [US1] Écrire `api/routes/authentification.py` : `POST /auth/otp` (`204`), `POST /auth/otp/verification` (`200` `ReponseVerificationCode`, pose `nelo_refresh` et `nelo_appareils` par `response.set_cookie`, `Secure` selon `configuration.cookies_secure`) ; les routes lisent `request.app.state.valkey`, `POLITIQUE`, la configuration, et ne portent aucune règle ; `api/main.py` inclut le routeur ; `api/contrat.py` : `CHEMINS_SANS_ETABLISSEMENT` étendu aux `/auth/*`, `EN_TETE_AUTHORIZATION` ajouté sur les routes hors chemins libres, `Set-Cookie` documenté sur les réponses qui ouvrent une session ; régénérer `contrat/` (`uv run python -m api.contrat && pnpm contrat:client`), étendre `tests/portes/test_contrat_attendu.py` pour lire aussi [contracts/openapi-attendu.yaml](contracts/openapi-attendu.yaml) de cette tranche (les deux fichiers, l'un après l'autre) ; P-03 vert
- [ ] T040 [P] [US1] Écrire les clés `session.*` dans `web/app/core/i18n/fr.json` et `en.json` (dans le même commit) : écran du numéro (`session.numero.titre`, `.champ`, `.aide`, `.action`, `.sms_gratuit`, `.indicatif`), écran du code (`.code.titre`, `.envoye_au`, `.modifier`, `.renvoyer_dans`, `.renvoyer`, `.pas_arrive.titre`, `.pas_arrive.corps` (E-01, sans numéro), `.tentatives_restantes`, `.expire`, `.epuise`, `.trop_de_demandes`), le nom du produit par `produit.ts` ; étendre `docs/design/lexique.md` : section 2 (les refus de la tranche avec leur versant positif), section 3 (« SMS » et non « message court » ni « texto » (E-06), « code reçu », « code personnel », « ouvrir une session », « fermer la session ») ; `web/tests/unit/lexique.test.ts` vert
- [ ] T041 [US1] Écrire `web/app/core/session/etat.ts` (fonctions pures : `etapeSuivante(reponse)`, `compteARebours(depuis, delai)`, l'état de l'écran du code) et `web/app/composables/useSession.ts` (`demanderCode(numero)`, `verifierCode(numero, code, compteId?)`, qui appellent `useApi()` et ne gardent **aucun jeton**) ; test `web/tests/unit/session-etat.test.ts`
- [ ] T042 [US1] Écrire `web/app/pages/connexion.vue` (`definePageMeta({ sansCoquille: true, contexteTactile: 'standard' })`) selon l'artboard US1 : le nom du produit, la langue `fr`/`en`, `CanonChamp saisie="code"` pour le numéro avec l'indicatif de `runtimeConfig.public.indicatifDefaut` affiché en préfixe, l'aide « pas besoin d'adresse e-mail », `CanonBouton variante="principal" pleineLargeur` « Recevoir le code par SMS », le format annoncé pendant la saisie (`Champ.erreur` sur `AUT_NUMERO_INVALIDE` traduit avant l'envoi par une vérification de forme locale **de présentation seulement**) ; et `web/app/pages/connexion/code.vue` : six chiffres dans un `CanonChamp saisie="code"`, « Envoyé au … Modifier », le compte à rebours du renvoi en `CanonAlerte niveau="attente"`, la carte « Le SMS n'est pas encore arrivé ? » (E-01), les refus `AUT_OTP_*` avec leur versant positif ; après `SessionOuverte`, navigation vers `/connexion/pin` (US3) ou `/` ; déclarer `connexion` (`/connexion`, 120/45) et `connexion-code` (`/connexion/code`, 120/45) dans `web/ecrans.json`
- [ ] T043 [US1] Écrire `web/tests/e2e/connexion.spec.ts` : le parcours réel sur le serveur de test (numéro → code lu dans `NELO_SMS_JOURNAL` → accueil « aucun domaine » avec l'administrateur nommé), un numéro inconnu qui reçoit le même écran de code sans jamais lire « inconnu », le renvoi bloqué par le compte à rebours ; activer le `setup` Playwright de T024 ; P-05 ouvre les deux écrans neufs dans les deux moteurs et les deux thèmes ; P-10 les pèse

**Point de contrôle** : `scripts/verifier.sh` vert ; US1 démontrable à la main selon
[quickstart.md](quickstart.md) § US1 ; SC-001 et SC-003 mesurés et notés.

---

## Phase 4 : User Story 2, aucun compte d'un tenant ne voit une donnée d'un autre, l'établissement et l'année sont choisis (Priorité : P1)

**But** : les quatre en-têtes sont vérifiés par leurs middlewares contre les rattachements du
compte ; le tenant provisoire de T0a disparaît ; les suites de T0a passent par une session.

**Test indépendant** : deux tenants, deux sessions, un second établissement non rattaché ; la
lecture des paramètres avec les en-têtes dans tous leurs états.

### Tests pour la User Story 2

- [ ] T044 [P] [US2] Écrire `tests/en_tetes/test_etablissement.py` : `400 TEN_ETABLISSEMENT_REQUIS` absent et malformé ; `403 TEN_ETABLISSEMENT_NON_AUTORISE` pour `etab_b` depuis la session A, pour `ETAB_A2` non rattaché, pour un UUID inexistant, **les trois réponses identiques** hors `requete_id` ; `200` pour `etab_a` ; une affectation dont `fin` est passée ne rattache plus
- [ ] T045 [P] [US2] Écrire `tests/en_tetes/test_annee.py` : une route d'essai enregistrée dans `ROUTES_PEDAGOGIQUES` par une application neuve (`creer_application()` + `add_api_route`) ; `400 ANN_ANNEE_REQUISE` absent **même avec une seule année rattachée**, malformé ; `404 TEN_RESSOURCE_INTROUVABLE` pour l'année de B, pour une année inexistante, pour `annee_a` sous l'en-tête `ETAB_A2` (US2-9) ; `200` pour `annee_a` sous `etab_a` ; une route non pédagogique ignore l'absence et refuse le malformé
- [ ] T046 [P] [US2] Étendre `tests/isolation/` : `test_deux_tenants.py` couvre `personnes.personne`, `annees.annee_scolaire`, `habilitations.compte`, `habilitations.affectation` et les trois outbox (énumération automatique, une ligne par tenant) ; nouveau `test_session_tenant.py` : la transaction ouverte par une route protégée porte le tenant du compte de la session, pas de l'en-tête (une session A avec l'en-tête `etab_b` ne voit **rien**, et répond `403` avant)
- [ ] T047 [P] [US2] Écrire `tests/en_tetes/test_sante_et_libres.py` : `/sante`, `/openapi.json`, `/docs` et `/auth/*` répondent sans jeton ; toute autre route enregistrée répond `401` sans jeton (parcours de `application.routes`)

### Implémentation de la User Story 2

- [ ] T048 [US2] Écrire `api/etablissement.py` et `api/annee.py` ([research.md R-04](research.md)) : les deux middlewares ASGI, `ROUTES_PEDAGOGIQUES: set[str]` (motifs de chemin, `re.fullmatch`) alimenté par les routeurs, `affectation_vivante` appelée dans `transaction(tenant_id)` ; `api/main.py` : la chaîne `Session → Etablissement → Annee → Idempotence` ; **supprimer `api/tenant_provisoire.py`** ; `api/contrat.py` : `EN_TETE_ANNEE` ajouté aux seules routes pédagogiques (aucune en T1a) ; régénérer `contrat/`
- [ ] T049 [US2] Écrire `tests/conftest.py::sessions_ab` (ouvre une session par tenant **par l'API**, via `tests/authentification/outils.ouvrir`) ; réécrire `tests/module_dore/outils.py::en_tetes(session, etablissement_id, *, ecriture=False, annee_id=None)` avec `Authorization` ; adapter `tests/module_dore/*`, `tests/idempotence/*`, `tests/assistance/*` et `tests/simulations/*` pour passer par `sessions_ab` ; retirer les tests du provisoire (`test_tenant_provisoire.py` ou équivalent) et les remplacer par ceux de T044 ; `scripts/portes/reparcours-suspension.sh` : même nombre de tests dans les deux passages
- [ ] T050 [US2] Étendre `api/routes/parametres.py` de rien d'autre que ce que la session impose (FR-046 : le contrat ne change pas) ; vérifier P-01, P-12 (chaque fonction d'accès neuve exercée), P-03 ; `scripts/verifier.sh` vert

**Point de contrôle** : le second critère de fin de la roadmap est tenu et prouvé ; SC-004 à
SC-006 partiellement mesurés (la suspension attend US5).

---

## Phase 5 : User Story 3, le code personnel remplace le message court sur un appareil connu (Priorité : P1)

**But** : après une ouverture par code reçu, la personne définit quatre chiffres ; sur cet
appareil elle rouvre par ces quatre chiffres sans message.

**Test indépendant** : ouvrir par code reçu, définir un code personnel, fermer, rouvrir par code
personnel, constater zéro envoi ; sur un client sans cookie d'appareil, `AUT_APPAREIL_INCONNU`.

### Tests pour la User Story 3

- [ ] T051 [P] [US3] Écrire `tests/authentification/test_pin.py` : définition (`204`, `pin_empreinte` non nulle et **jamais renvoyée**, événement `pin.defini`) ; `422 VAL_SCHEMA_INVALIDE` sur trois chiffres ; changement avec `pin_courant` exigé hors dispense, dispense dans les dix minutes après une ouverture par code reçu ; ouverture par PIN (`200`, zéro envoi, événement `session.ouverte` canal `PIN`) ; `401 AUT_APPAREIL_INCONNU` sans cookie ; `AUT_PIN_ABSENT` ; `AUT_PIN_INVALIDE` avec `tentatives_restantes` ; `AUT_PIN_TENTATIVES_EPUISEES` à la cinquième, `pin_verrouille_le` posé, puis levé par une ouverture par code reçu ; `AUT_COMPTE_SUSPENDU` fait disparaître le compte de `nelo_appareils` ; `GET /auth/appareil` rend nom, prénoms, `pin_defini`, **jamais un numéro**, et `[]` sans cookie ; deux comptes connus du même cookie, chacun son PIN (US8-4)
- [ ] T052 [P] [US3] Écrire `web/tests/e2e/pin.spec.ts` : définir `1234`, fermer la session par le menu de compte (US5, ou `DELETE /auth/session` par `request` tant que le menu n'existe pas), rouvrir : l'écran propose le nom, aucun numéro visible, quatre chiffres, zéro ligne de plus dans `NELO_SMS_JOURNAL` ; contexte de navigateur neuf : pas de PIN proposé ; cinq codes faux : le verrou et son versant positif

### Implémentation de la User Story 3

- [ ] T053 [US3] Écrire `modules/socle/habilitations/appareil.py` : `Appareil` (les secrets lus du cookie), `connaitre(compte_id, tenant_id, valkey, jours) -> secret`, `comptes_connus(appareil, valkey)`, `oublier(compte_id, valkey)` (`appareil:{sha256}` et `appareils_compte:{compte}`) ; `service.py` : `definir_pin` (Argon2id [research.md R-13](research.md), `PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)`, empreinte sur `pin + compte_id`, dispense par `session:{sid}.ouverte_le` et `canal`), `ouvrir_par_pin` (les six refus, `pin_tentatives:{compte}`, verrou durable, suspension → `oublier`), `comptes_de_l_appareil` ; fonctions d'accès `poser_pin`, `poser_verrou_pin`, `appeler_compte_par_id_sans_tenant`, `lire_comptes_par_ids` ; `ouvrir_session` (T034) et `verifier_code` (T036) appellent `connaitre` et posent le cookie `nelo_appareils` (`Path=/api/v1/auth`, `Max-Age` = validité la plus lointaine)
- [ ] T054 [US3] Écrire dans `api/routes/authentification.py` : `POST /auth/pin`, `POST /auth/pin/definition` (protégée : sous le middleware de session, donc **hors** chemins libres : `CHEMINS_LIBRES` liste les seuls `/auth/otp*`, `/auth/pin` (ouverture), `/auth/rafraichissement`, `/auth/invitation/`, `/auth/appareil`), `GET /auth/appareil` ; régénérer `contrat/` ; P-03 vert
- [ ] T055 [US3] Écrire `web/app/pages/connexion/pin.vue` (définition : pourquoi avant quoi, deux saisies `CanonChamp saisie="code"`, « Plus tard : me connecter par SMS ») et l'ouverture par code personnel **dans `web/app/pages/connexion.vue`** : si `GET /auth/appareil` rend des comptes, l'écran propose leurs noms (`CanonAvatar` + nom, jamais un numéro), la saisie de quatre chiffres, le lien « Un autre numéro » vers l'écran du numéro ; les refus `AUT_PIN_*` avec leur versant positif ; clés `session.pin.*` `fr`/`en` ; `web/ecrans.json` : `connexion-pin` (`/connexion/pin`, 120/45, `session: true`) ; `web/tests/session.setup.ts` définit le code personnel après l'ouverture (l'état enregistré porte `nelo_appareils`)

**Point de contrôle** : le premier critère de fin (« par code à usage unique **puis par code
personnel** ») est tenu ; SC-002 mesuré ; `scripts/verifier.sh` vert.

---

## Phase 6 : User Story 4, le contexte compose l'interface, et la personne choisit où elle travaille (Priorité : P2)

**But** : `GET /moi/capacites` est servie et la coquille de T0b la lit sans changer d'écran ; la
personne choisit son établissement et son année.

**Test indépendant** : lire le contexte avec la session A, comparer sa forme au contrat ; la
coquille sur la session semée affiche « aucun domaine » avec l'administrateur ; un compte à deux
établissements choisit.

### Tests pour la User Story 4

- [ ] T056 [P] [US4] Écrire `tests/contexte/test_moi_capacites.py` : la forme exacte de [03-api.md § 1.9](../../docs/03-api.md) validée par `ContexteCapacites` ; `etablissements` = les seuls rattachés (jamais `ETAB_A2` si non rattaché, jamais `etab_b`) ; `etablissement_actif` = l'en-tête ; `annees` avec libellé et état, `annee_active` = celle en `active` ; `capacites == []`, `acces_nominatifs == []`, `alertes == []` ; `administrateur` renseigné, repli sur le nom et le téléphone de l'établissement avec `prenoms == ""` quand aucun n'est désigné ou quand le désigné est suspendu ; `country_pack` du tenant B = le pack fictif (devise, vocabulaire) sans qu'une ligne diffère ; `parametres_effectifs` en `{cle: valeur}` ; `compte.langue` = celle de la personne
- [ ] T057 [P] [US4] Retourner `tests/portes/test_contexte_au_contrat.py::test_aucune_route_ne_le_sert_encore` en `test_une_route_le_sert` (`GET /moi/capacites` renvoie `#/components/schemas/ContexteCapacites`) et vérifier qu'aucune collision de nom ne se produit
- [ ] T058 [P] [US4] Écrire `web/tests/e2e/coquille-session.spec.ts` : sur la session semée, `/` affiche `data-situation="AUCUNE_CAPACITE"` avec le nom et le téléphone de l'administrateur d'essai ; le compte A rattaché à `ETAB_A2` voit le choix d'établissement, le change, et la coquille se relit ; le changement d'année (active → préparation) change l'en-tête des requêtes suivantes (intercepté par `page.route`) et la pastille `ANNEE_PREPARATION` s'affiche ; **rien n'est persisté côté serveur** : un contexte de navigateur neuf revient sur le premier rattachement
- [ ] T059 [P] [US4] Écrire `web/tests/unit/appareil-choix.test.ts` (les fonctions pures de `core/appareil/choix.ts` avec un `Stockage` fabriqué) et étendre `web/tests/unit/composants-etats.test.ts` aux codes `ANNEE_ACTIVE` (neutre) et `ANNEE_PREPARATION` (ocre)

### Implémentation de la User Story 4

- [ ] T060 [US4] Écrire `api/routes/moi.py::lire_contexte` ([research.md R-19](research.md)) : `habilitations.rattachements`, `tenants.lire_etablissements`, `personnes.lire_identite(s)` (compte et administrateur), `annees.lire_annees` filtrées par les rattachements, `tenants.lire_pack`, `tenants.lire_parametres_effectifs` projetés, listes vides pour sites, cycles, modules, capacités, accès nominatifs, alertes ; `modules/shared/contexte.py::Administrateur.prenoms` accepte la chaîne vide (le seul changement) ; `api/contrat.py` : retirer `ContexteCapacites` de `SCHEMAS_SANS_ROUTE` ; régénérer `contrat/` ; si `X-Nelo-Etablissement` manque, le middleware répond `400` : **la source web doit connaître un établissement avant la première lecture** ; la réponse `TEN_ETABLISSEMENT_REQUIS` de ce middleware porte, pour un compte authentifié, `details.etablissements` = les identifiants rattachés (une donnée du compte lui-même, jamais d'un tiers), et [03-api.md § 1.2](../../docs/03-api.md) le dit dans une note « *Ajouté par T1a* » (diff à appliquer et tracer au journal)
- [ ] T061 [P] [US4] Écrire `web/app/core/appareil/choix.ts` (`lireEtablissementChoisi(stockage)`, `ecrireEtablissementChoisi`, `lireAnneeChoisie`, `ecrireAnneeChoisie`, sur le modèle de `core/theme.ts`) et `web/app/composables/useChoixAppareil.ts` ; le client (T019) lit ces choix pour poser les en-têtes ; le cookie **`nelo_etablissement`** (non `HttpOnly`, `SameSite=Strict`, un identifiant sans secret) est posé par `core/plateforme/web.ts` (le seul fichier qui touche le navigateur) à chaque choix, et lu au rendu serveur par la source
- [ ] T062 [US4] Étendre `web/app/components/canon/CoquilleEntete.vue` (E-05) : le **menu de compte** ouvert par l'avatar (nom du compte, établissement actif avec la liste des rattachés, année de travail avec la liste, « Mon numéro » (US7), « Fermer la session » (US5)), émis `changerEtablissement(id)`, `changerAnnee(id)`, `deconnexion` ; dès `md`, « Fermer la session » aussi directement dans `.outils` ; la pastille de l'année (`CanonPastilleEtat code="ANNEE_PREPARATION"` quand l'année choisie est en préparation) ; retirer le commentaire « Ni cloche ni déconnexion : T1a » ; `Coquille.vue` relaie ; `web/app/app.vue` : au changement, écrire le choix, relire le contexte par la source, `refreshNuxtData` ; `web/app/core/composants/etats.ts` : `ANNEE_ACTIVE: { voix: 'neutre', cle: 'etat.annee_active' }`, `ANNEE_PREPARATION: { voix: 'ocre', cle: 'etat.annee_preparation' }` ; clés `fr`/`en` et lexique (les deux états, « à venir » pour les états du compte et le partage, E-03) ; `docs/design/composants.md` : la coquille gagne le menu de compte
- [ ] T063 [US4] Déclarer `accueil-session` (`/`, `session: true`, 120/45) dans `web/ecrans.json` ; étendre `web/tests/portes/p10.spec.ts` : sur cette visite, **aucune ressource dont le nom contient `personas` ou `demonstration`** n'est chargée (l'élagage de [research.md R-10](research.md)), et le budget tient avec la réponse du contexte comptée ; P-05 et P-10 verts

**Point de contrôle** : la coquille vit sur des données réelles ; l'écran « aucun domaine » nomme
une vraie personne ; `scripts/verifier.sh` vert.

---

## Phase 7 : User Story 5, la révocation est immédiate, la session se ferme, et le jeton tourne (Priorité : P2)

**But** : suspendre coupe à la requête suivante ; fermer efface ; le refresh tourne et sa
réutilisation fait tomber la session ; aucun jeton n'est visible d'un script.

**Test indépendant** : suspendre un compte en session et rejouer sa requête ; rafraîchir puis
représenter l'ancien jeton ; inspecter le stockage du navigateur après ouverture.

### Tests pour la User Story 5

- [ ] T064 [P] [US5] Écrire `tests/authentification/test_revocation.py` : après `POST /comptes/{id}/suspension` (session administrative B ou A selon la capacité, point d'insertion), la requête suivante du compte avec son jeton encore valable répond `401 AUT_SESSION_REVOQUEE`, le rafraîchissement aussi, le PIN `AUT_COMPTE_SUSPENDU`, `nelo_appareils` ne connaît plus le compte, `session:{sid}` et `sessions_compte:{compte}` sont vides, événements `compte.suspendu` et `session.fermee(SUSPENSION)` ; `exiger_capacite("habilitations.compte.suspendre")` est appelée (espion) ; la suspension est **durable** : `valkey.flushdb()` puis un PIN répond encore `AUT_COMPTE_SUSPENDU` ; une session dont Valkey a perdu la clé mais dont le compte est `actif` répond `AUT_SESSION_REVOQUEE` (US5-7)
- [ ] T065 [P] [US5] Écrire `tests/authentification/test_rotation.py` : le rafraîchissement rend un jeton d'accès neuf et un `nelo_refresh` différent ; l'ancien représenté **dans la fenêtre** de dix secondes rend la même réponse ; représenté **hors fenêtre** (TTL manipulé) → `401 AUT_JETON_INVALIDE` et toute la session révoquée, y compris le jeton neuf, événement `session.fermee(REUTILISATION)` ; un refresh inconnu → `401` ; au-delà de `securite.duree_session_minutes` (valeur posée à 1 minute par `PUT /parametres` puis session ouverte, TTL manipulé) → `401 AUT_SESSION_REVOQUEE` ; `DELETE /auth/session` → `204`, cookie effacé (`Max-Age=0`), jeton d'accès et refresh révoqués, appareil toujours connu, événement `session.fermee(DECONNEXION)`
- [ ] T066 [P] [US5] Étendre `web/tests/portes/p05.spec.ts` d'un test sur la visite `accueil-session` : `localStorage`, `sessionStorage` et `document.cookie` ne contiennent aucune valeur de plus de 20 caractères ressemblant à un jeton (`nelo_acces`, `nelo_refresh`, `nelo_appareils` absents de `document.cookie`, aucun `eyJ`), et les cookies du contexte Playwright portent `httpOnly: true` pour ces trois noms (SC-006) ; écrire `scripts/portes/negatifs/p-05.sh` étendu : muter le relais pour poser `nelo_acces` sans `HttpOnly`, P-05 doit échouer en se nommant
- [ ] T067 [P] [US5] Écrire `web/tests/e2e/session.spec.ts` : « Fermer la session » depuis le menu de compte renvoie à `/connexion` avec le PIN proposé ; un jeton d'accès expiré (cookie `nelo_acces` supprimé par `context.clearCookies({ name: 'nelo_acces' })`) est renouvelé sans que la page change ; après suspension par l'API, la prochaine navigation renvoie à `/connexion` avec le mot d'écran de FR-064

### Implémentation de la User Story 5

- [ ] T068 [US5] Écrire `modules/socle/habilitations/service.py::rafraichir` ([research.md R-06](research.md) : rotation, `remplace_le`, fenêtre, révocation sur réutilisation, borne de durée), `fermer_session`, `suspendre` (statut + événement dans la transaction ; **après** `COMMIT` : `revoquer_toutes` et `appareil.oublier`, et `session_valide` relit le statut du compte à chaque requête pour couvrir une panne entre les deux) ; fonctions d'accès `lire_statut` ; routes `POST /auth/rafraichissement` (chemin libre, lit le cookie), `DELETE /auth/session`, et `api/routes/comptes.py::POST /comptes/{id}/suspension` avec `exiger_capacite("habilitations.compte.suspendre")` ; régénérer `contrat/`
- [ ] T069 [US5] Étendre `web/server/api/v1/[...].ts` : sur `DELETE /auth/session`, effacer `nelo_acces` ; le client (T019) déclenche le rafraîchissement sur `401 AUT_JETON_INVALIDE` **et** quand `nelo_acces` manque (le relais répond `401 AUT_JETON_MANQUANT` sans appeler l'API si le cookie est absent et qu'un `nelo_refresh` existe : il tente d'abord le rafraîchissement lui-même, une fois) ; `useSession().fermer()` ; `app.vue` branche `deconnexion` → `fermer()` → `/connexion` ; clés `session.fermer`, `session.revoquee.*`, `session.suspendu.*` (FR-064, E-07) avec leur versant positif ; la page `/connexion` affiche le mot d'écran quand elle reçoit `?motif=revoquee|suspendu`
- [ ] T070 [US5] Écrire les tests négatifs de P-12 dans `scripts/portes/negatifs/p-12.sh` (en plus de la mutation de T0a, qui reste) : trois mutations au choix du script par argument, chacune exécutée par `scripts/tests-negatifs.sh` comme une entrée distincte (`P-12a`, `P-12b`, `P-12c` dans `PORTES`, le script de porte étant le même) : retirer l'appel à `session_valide` dans `api/session.py` ; faire répondre `404` à `/auth/otp` quand aucun compte n'existe ; faire replier `api/annee.py` sur l'année active quand l'en-tête manque ; chaque mutation fait échouer P-12 en se nommant ; `scripts/tests-negatifs.sh` étendu

**Point de contrôle** : SC-004, SC-006, SC-007 mesurés ; `scripts/verifier.sh` et
`scripts/tests-negatifs.sh` verts.

---

## Phase 8 : User Story 6, activer son compte depuis un lien à usage unique (Priorité : P2)

**But** : le secrétariat crée un compte, un lien part par SMS, le lien active et ouvre une
session ; il ne sert qu'une fois.

**Test indépendant** : créer, lire le lien dans `envoyes`, l'ouvrir, le rouvrir, renvoyer, ouvrir
par code reçu un compte encore invité.

### Tests pour la User Story 6

- [ ] T071 [P] [US6] Écrire `tests/authentification/test_invitation.py` : `POST /comptes` → `201`, `Location`, `statut: invite`, `invite_le`, **aucun jeton dans le corps**, un envoi sous 160 caractères avec le nom de l'établissement et un lien `{url_publique}/activation/{jeton}`, événements `compte.cree` puis `compte.invite`, `exiger_capacite("habilitations.compte.gerer")` appelée, rejeu idempotent (un seul compte, un seul envoi) ; `404` personne d'un autre tenant ; `409 TEN_RESSOURCE_DEJA_EXISTANTE` personne déjà titulaire ; `POST /comptes/verification` dit les bloquages sans écrire ni envoyer (E-04, FR-063) ; `POST /auth/invitation/{jeton}` → `200 SessionOuverte`, compte `actif`, appareil connu, `invitation_empreinte` effacée, événement `compte.active(LIEN)` ; rouvert → `401 AUT_INVITATION_INVALIDE` ; expiré (TTL manipulé) → idem ; `POST /comptes/{id}/invitation` renvoie un lien neuf et invalide l'ancien, `422 AUT_COMPTE_DEJA_ACTIF` sur un compte actif, `AUT_COMPTE_SUSPENDU` sur un suspendu ; un compte `invite` ouvert par code reçu passe `actif` (FR-033)
- [ ] T072 [P] [US6] Écrire `web/tests/e2e/activation.spec.ts` : créer un compte par `request` (session administrative semée), lire le lien dans `NELO_SMS_JOURNAL`, l'ouvrir : session ouverte, écran du code personnel ; le rouvrir : `AUT_INVITATION_INVALIDE` avec ses deux issues ; `/activation/jeton-bidon` sans session : le refus, jamais une erreur technique

### Implémentation de la User Story 6

- [ ] T073 [US6] Écrire `service.py::creer_compte`, `verifier_creation`, `renvoyer_invitation`, `activer_par_invitation` ([contracts/interfaces-python.md](contracts/interfaces-python.md)) : jeton `secrets.token_urlsafe(32)`, empreinte SHA-256 sur le compte, `invitation_expire_le` par `securite.invitation_validite_jours`, texte dans `invitation_texte:{envoi_id}`, événement `compte.invite` consommé par `consommer_envoi` (gabarit `invitation`) ; fonctions d'accès `poser_invitation`, `appeler_compte_par_invitation`, `compter_meme_identifiant`, `lire_compte_par_personne` ; schémas `CorpsCreationCompte`, `CompteCree`, `VerificationCreationCompte`
- [ ] T074 [US6] Écrire `api/routes/comptes.py::POST /comptes`, `POST /comptes/verification`, `POST /comptes/{id}/invitation` (tous sous `exiger_capacite("habilitations.compte.gerer")`, `Location` sur la création) et `api/routes/authentification.py::POST /auth/invitation/{jeton}` (chemin libre) ; régénérer `contrat/` ; P-03 vert
- [ ] T075 [US6] Écrire `web/app/pages/activation/[jeton].vue` (`sansCoquille`) : appelle l'activation au montage, puis `/connexion/pin` ; le refus `AUT_INVITATION_INVALIDE` avec ses deux issues (« entrer mon numéro », « demander un nouveau lien au secrétariat ») ; clés `session.activation.*` ; `web/ecrans.json` : `activation` (`/activation/[jeton]`, 120/45, visitée par P-05 avec un jeton invalide pour l'état de refus)

**Point de contrôle** : `scripts/verifier.sh` vert ; US6 démontrable selon
[quickstart.md](quickstart.md) § US6.

---

## Phase 9 : User Story 7, changer de numéro de téléphone (Priorité : P3)

**But** : en libre-service, un code part vers le nouveau numéro et l'identifiant change à la
vérification ; par le secrétariat, tout tombe et la première ouverture vérifie.

**Test indépendant** : demander un changement, lire le code, vérifier, constater l'identifiant et
le message d'information ; par la route administrative, constater la révocation.

### Tests pour la User Story 7

- [ ] T076 [P] [US7] Écrire `tests/authentification/test_changement.py` : `POST /moi/telephone` → `204`, un envoi vers le **nouveau** numéro, identifiant inchangé, `changement:{compte}` en Valkey ; les mêmes limites et refus que le code reçu ; **un nouveau numéro déjà porté par un autre compte du tenant reçoit quand même le code** et la vérification répond `422 AUT_IDENTIFIANT_DEJA_UTILISE` (E-04, FR-036) ; `POST /moi/telephone/verification` → `204`, identifiant changé, l'ancien numéro reçoit le gabarit `changement_ancien_numero`, la session courante répond encore `200`, événement `identifiant.change(PERSONNE)` ; `POST /comptes/{id}/telephone` → `204`, identifiant changé, **toutes** les sessions du compte révoquées, appareils oubliés, ancien numéro informé, événement `identifiant.change(ADMINISTRATION)`, capacité `habilitations.compte.gerer` exigée, `AUT_IDENTIFIANT_DEJA_UTILISE` sans déclaration de partage, puis ouverture par code reçu sur le nouveau numéro
- [ ] T077 [P] [US7] Écrire `web/tests/e2e/telephone.spec.ts` : depuis le menu de compte, « Mon numéro » → nouveau numéro → code lu dans le journal → confirmation → le journal porte ensuite le message vers l'ancien numéro ; la session tient

### Implémentation de la User Story 7

- [ ] T078 [US7] Écrire `service.py::demander_changement`, `verifier_changement`, `changer_identifiant_administratif` ; fonction d'accès `poser_identifiant` ; routes `POST /moi/telephone`, `POST /moi/telephone/verification` dans `api/routes/moi.py` et `POST /comptes/{id}/telephone` dans `api/routes/comptes.py` ; schémas `CorpsChangementTelephone`, `CorpsVerificationChangement`, `CorpsChangementAdministratif` ; régénérer `contrat/`
- [ ] T079 [US7] Écrire `web/app/pages/compte/telephone.vue` (`sansCoquille: false` : dans la coquille, atteinte par le menu de compte) : nouveau numéro, code reçu sur le nouveau, confirmation, l'avertissement « l'ancien numéro sera informé » ; le refus `AUT_IDENTIFIANT_DEJA_UTILISE` avec son versant positif (« le partage d'un numéro se déclare au secrétariat ») ; clés `session.telephone.*` ; `web/ecrans.json` : `compte-telephone` (`/compte/telephone`, `session: true`, 120/45)

**Point de contrôle** : `scripts/verifier.sh` vert.

---

## Phase 10 : User Story 8, deux parents, un téléphone (Priorité : P3)

**But** : un second compte sur un numéro exige la déclaration de partage ; un seul code part ; la
personne choisit qui elle est, et le choix est tracé.

**Test indépendant** : créer deux comptes sur `NUMERO_A`, sans puis avec déclaration ; demander un
code, vérifier, choisir.

### Tests pour la User Story 8

- [ ] T080 [P] [US8] Écrire `tests/authentification/test_partage.py` : second compte sans `partage_familial` → `422 AUT_IDENTIFIANT_DEJA_UTILISE` avec `details.partage_familial_requis = true` ; avec → `201`, événement `compte.cree(partage_familial=true, cree_par)` ; `POST /comptes/verification` l'annonce ; un seul envoi à la demande de code ; la vérification rend `ChoixRequis` avec les deux noms et l'établissement, sans numéro ; rappelée avec `compte_id` → session pour ce compte, événement `session.ouverte(choix_parmi=2)` ; un `compte_id` hors de la liste → `401 AUT_OTP_INVALIDE` ; le code reste valide jusqu'au choix, une seule fois ; `habilitations.identifiant_partage(tenant, compte)` vrai pour les deux, faux pour un compte seul (FR-040) ; le même numéro dans deux tenants : un seul envoi, `ChoixRequis` avec le nom de chaque établissement, une session pour un seul tenant (cas limite de la spec)
- [ ] T081 [P] [US8] Écrire `web/tests/e2e/partage.spec.ts` : deux comptes sur un numéro (créés par `request`), la demande de code, l'écran « Qui ouvre la session ? » avec les deux noms, le choix, l'arrivée dans l'espace du compte choisi

### Implémentation de la User Story 8

- [ ] T082 [US8] Étendre `service.py::creer_compte` (la règle de partage, `compter_meme_identifiant`), `verifier_code` (`ChoixRequis`, le rappel avec `compte_id`, la validation du choix, `choix_parmi` dans l'événement) et écrire `identifiant_partage` ; exporter ; vérifier P-12
- [ ] T083 [US8] Étendre `web/app/pages/connexion/code.vue` : l'écran « Qui ouvre la session ? » quand la réponse est `ChoixRequis` (une `CanonAvatar` et un nom par compte, l'établissement en dessous, aucune pastille d'état), le rappel avec `compte_id` ; clés `session.choix.*`

**Point de contrôle** : les huit stories sont livrées ; `scripts/verifier.sh` vert.

---

## Phase 11 : Finition et transverse

**But** : le dépôt dit ce qui existe, les mesures sont notées, les tests négatifs couvrent les
règles neuves, rien ne reste marqué « provisoire jusqu'à T1a ».

- [ ] T084 [P] Mettre à jour `docs/01-stack.md` § 2.1 (l'état du dépôt : les trois paquets, les quatre dossiers de migrations, le relais, les écrans) et § 3 (la commande de l'API en test, `NELO_DEMONSTRATION=1`, les variables de sécurité) ; vérifier qu'aucun fichier ne porte plus « PROVISOIRE jusqu'à T1a » (`grep -rn "T1a" api/ modules/ web/app/` ne rend que des renvois historiques)
- [ ] T085 [P] Appliquer et tracer le diff de T060 sur `docs/03-api.md § 1.2` (`details.etablissements` sur `TEN_ETABLISSEMENT_REQUIS` pour un compte authentifié) ; relire [03-api.md § 2.1](../../docs/03-api.md) contre `contrat/openapi.json` : chaque route et chaque code de la tranche y sont, dans les mêmes mots
- [ ] T086 [P] Relire `docs/design/lexique.md` contre `fr.json` : chaque mot de la tranche à sa place, « SMS » partout à l'écran, aucun tiret cadratin ; `web/tests/unit/lexique.test.ts` vert ; relire `docs/design/composants.md` (le champ de code, le menu de compte)
- [ ] T087 Mesurer et noter dans [quickstart.md](quickstart.md) et au journal : SC-001 (trois écrans, temps chronométré à la main sur un téléphone à 390 px en 3G simulée), SC-002, SC-003 (l'écart des médianes réel), SC-008 (délai de remise à la passerelle simulée), SC-009 (les poids de P-10 des cinq écrans), SC-012 (la durée de `scripts/verifier.sh`, sous cinq minutes), la durée de `scripts/tests-negatifs.sh`
- [ ] T088 Relire la définition de terminé de [01-stack.md § 8.3](../../docs/01-stack.md) point par point et la reporter au journal comme T0a l'a fait ; relire le contrôle de constitution du [plan.md](plan.md) contre le code livré (les deux écarts nommés sont-ils toujours les seuls ?) ; écrire l'entrée de journal de fin de tranche dans `docs/progress.md` (fait, décidé, écarts d'implémentation, mesures, Q30 à confirmer) ; ne pas fusionner dans `main`

---

## Dépendances et ordre d'exécution

### Dépendances entre phases

- **Phase 1** : aucune dépendance ; T003, T004, T005 en parallèle après T001 et T002.
- **Phase 2** : dépend de la phase 1. T007, T008, T009 en parallèle ; T010 après T009 (la colonne
  `administrateur_compte_id` référence un compte par identifiant, mais le seed du catalogue et le
  `DROP FUNCTION` exigent que le provisoire ne soit plus appelé : T014 suit T010) ; T011 à T015
  en parallèle après les migrations ; T016 et T017 après T012 à T014 ; T018 à T024 en parallèle
  entre eux, après T004.
- **Phases 3 à 10** : chacune après la phase 2. **US1 est le socle de toutes les autres** (la
  session) ; US2 dépend de US1 ; US3, US4, US5, US6 dépendent de US1 et US2 ; US7 dépend de US5
  (révocation) ; US8 dépend de US6 (création de compte) et de US3 (deux PIN sur un appareil).
- **Phase 11** : après toutes les stories.

### Dépendances entre stories

```text
US1 (code reçu, session) ──► US2 (en-têtes, isolation) ──┬──► US3 (code personnel) ──► US8 (partage)
                                                          ├──► US4 (contexte)                 ▲
                                                          ├──► US5 (révocation) ──► US7       │
                                                          └──► US6 (invitation) ──────────────┘
```

### À l'intérieur d'une story

Tests d'abord (ils échouent), puis fonctions d'accès et schémas, puis service, puis routes et
contrat régénéré, puis clés et écrans, puis e2e et portes. Une fonction de `acces.py` sans test
fait échouer P-12 : écrire le test avec la fonction.

### Possibilités de parallélisme

- Phase 1 : T003, T004, T005 ; phase 2 : T007, T008, T009 ; T011, T012, T013, T015 ; T018 à T024.
- Dans chaque story, les tâches de test marquées [P] s'écrivent d'un trait ; les tâches web
  ([P] côté `web/`) avancent pendant que le serveur se termine, sur des fichiers différents.
- Les phases 8 (US6) et 9 (US7) sont indépendantes l'une de l'autre après US5 ; elles peuvent
  être menées en parallèle par deux sous-agents sur des fichiers différents, la fusion se faisant
  sur `service.py` et `comptes.py` (sections distinctes).

## Exemple de parallélisme : User Story 1

```bash
# Tests d'abord, d'un trait (fichiers différents, tous rouges) :
#   T025 outils.py · T026 test_demande_code.py · T027 test_verification_code.py
#   T028 test_reponse_identique.py · T029 test_messages.py · T030 test_consommateur_envoi.py
# Puis les briques indépendantes :
#   T031 normalisation.py · T032 gabarits et messages · T040 clés fr/en et lexique
# Puis dans l'ordre : T033 accès et schémas → T034 session → T035 limitation → T036 service
#   → T037 consommateur et travailleur → T038 middleware de session → T039 routes et contrat
# Côté web, en parallèle de T036 à T039 : T041 état de session → T042 écrans → T043 e2e
```

## Stratégie d'implémentation

### D'abord le MVP : User Story 1 seule

1. Phases 1 et 2 : quatre schémas sous RLS, les noyaux, le relais, la source ; vérification verte.
2. Phase 3 : la demande de code, la vérification, la session, les deux premiers écrans.
3. **S'arrêter et valider** : `curl` sur `/auth/otp` avec un numéro connu et un inconnu, réponses
   identiques ; le code lu dans le journal des messages ouvre une session ; `scripts/verifier.sh`
   vert. C'est la moitié du premier critère de fin de la roadmap.

### Livraison incrémentale

1. US2 : la double barrière remplace le provisoire, les suites de T0a passent par une session.
2. US3 : le code personnel ; le premier critère de fin est entier.
3. US4 : la coquille vit sur des données réelles.
4. US5 : révocation, rotation, fermeture ; les tests négatifs des règles de sécurité.
5. US6, US7, US8 : l'invitation, le changement, le partage.
6. Finition : le dépôt et le journal disent ce qui existe.

### Un développeur seul : l'ordre recommandé

T001 → T088 dans l'ordre, en respectant les [P] comme des lots à écrire d'un trait, et un commit
par point de contrôle au minimum. `scripts/tests-negatifs.sh` s'allonge de quatre mutations : le
lancer aux points de contrôle des phases 7 et 11, pas à chaque commit.

---

## Notes

- Les tâches [P] touchent des fichiers différents et n'attendent aucune tâche inachevée.
- Le label [Story] rend chaque tâche traçable à sa user story.
- Chaque story est complétable et testable seule, par `pytest` et dans un vrai navigateur.
- Un test qui passe avant l'implémentation est un test faux ; un comportement de sécurité sans
  test n'existe pas.
- **Aucun secret en clair** dans un fichier suivi par git : `.env.exemple` porte un secret
  d'exemple, les tests posent le leur.
- **Q30** (les valeurs par défaut) est appliquée à titre provisoire par `politique.py` et trois
  clés du catalogue ; si l'utilisateur tranche autrement, T003 et T010 changent, rien d'autre.
- Les sept écarts de la revue visuelle (E-01 à E-07) sont portés par T023, T040, T042, T060,
  T062, T069, T073, T076 ; aucun n'est laissé à l'appréciation de l'implémentation.
- Aucun tiret cadratin, nulle part : ni code, ni commentaire, ni clé, ni document.
