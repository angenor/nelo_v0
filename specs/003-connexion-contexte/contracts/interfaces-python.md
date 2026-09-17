# Interfaces de service : T1a, se connecter et savoir où l'on est

Ce que chaque paquet expose par son `__init__.py`, et **rien d'autre n'en sort**
([01-stack.md § 2.5](../../../docs/01-stack.md) point 4). Les dépendances sont injectées, jamais
importées depuis un autre module. Signatures en Python typé ; les corps appartiennent à
l'implémentation. Les formes HTTP sont dans [openapi-attendu.yaml](openapi-attendu.yaml).

## `modules.socle.habilitations` : le module de la tranche

```python
__all__ = [
    # schémas de contrat
    "CorpsDemandeCode", "CorpsVerificationCode", "ReponseVerificationCode", "SessionOuverte",
    "ChoixCompte", "CorpsOuverturePin", "CorpsDefinitionPin", "ReponseAppareil",
    "CorpsCreationCompte", "CompteCree", "CorpsChangementTelephone", "CorpsVerificationChangement",
    "CorpsChangementAdministratif",
    # identité et session
    "normaliser", "demander_code", "verifier_code", "ouvrir_par_pin", "definir_pin",
    "comptes_de_l_appareil", "rafraichir", "fermer_session", "activer_par_invitation",
    "verifier_jeton_acces", "session_valide",
    # en-têtes
    "affectation_vivante", "rattachements",
    # administration
    "creer_compte", "renvoyer_invitation", "changer_identifiant_administratif", "suspendre",
    "identifiant_partage",
    # changement en libre-service
    "demander_changement", "verifier_changement",
    # travailleur
    "consommer_envoi", "consommer_lot", "reprendre_evenements",
    # seeds et tests
    "creer_affectation",
]

def normaliser(brut: str, indicatif_defaut: str) -> str:
    """E.164 ou ErreurMetier('AUT_NUMERO_INVALIDE', statut=422)."""

async def demander_code(identifiant: str, adresse_client: str, *, valkey, politique) -> None:
    """Toujours silencieux. Limites (429 API_LIMITE_DEBIT). Écrit otp:*, otp_texte:* et l'événement
    habilitations.otp.demande dans l'outbox du tenant du premier compte, seulement si un compte
    actif ou invité porte le numéro ; sinon fait le même travail sans rien écrire."""

async def verifier_code(identifiant: str, code: str, compte_id: UUID | None, appareil: Appareil,
                        *, valkey, politique) -> SessionOuverte | ChoixRequis:
    """AUT_OTP_EXPIRE, AUT_OTP_INVALIDE (details.tentatives_restantes), AUT_OTP_TENTATIVES_EPUISEES,
    AUT_COMPTE_SUSPENDU. Active un compte `invite`. Rend le choix si plusieurs comptes et aucun choisi."""

async def ouvrir_par_pin(compte_id: UUID, pin: str, appareil: Appareil, *, valkey, politique) -> SessionOuverte:
    """AUT_APPAREIL_INCONNU, AUT_PIN_ABSENT, AUT_PIN_INVALIDE, AUT_PIN_TENTATIVES_EPUISEES (verrou
    durable), AUT_COMPTE_SUSPENDU (et l'appareil oublie le compte)."""

async def definir_pin(session: SessionCourante, pin: str, pin_courant: str | None, *, valkey) -> None:
    """Exige pin_courant si un code existe, sauf dans DISPENSE_PIN_COURANT après une ouverture par
    code reçu ou par lien. Événement habilitations.pin.defini."""

async def comptes_de_l_appareil(appareil: Appareil, *, valkey) -> ReponseAppareil
async def rafraichir(refresh: str, *, valkey, politique) -> SessionOuverte
    """Rotation ; réutilisation hors fenêtre → révocation de la session, AUT_JETON_INVALIDE."""
async def fermer_session(session: SessionCourante, *, valkey) -> None
async def activer_par_invitation(jeton: str, appareil: Appareil, *, valkey) -> SessionOuverte
    """AUT_INVITATION_INVALIDE, AUT_COMPTE_SUSPENDU."""

def verifier_jeton_acces(jeton: str, secret: str) -> JetonAcces:
    """Signature et expiration ; ValueError → AUT_JETON_INVALIDE côté middleware."""
async def session_valide(session_id: UUID, compte_id: UUID, *, valkey) -> bool:
    """La liste de révocation : la clé session:{sid} existe et porte ce compte."""

async def affectation_vivante(tenant_id: UUID, compte_id: UUID, etablissement_id: UUID,
                              annee_id: UUID | None = None) -> bool
async def rattachements(tenant_id: UUID, compte_id: UUID) -> list[Rattachement]:
    """(etablissement_id, annee_id) des affectations vivantes ; le contexte en dérive."""

async def creer_compte(tenant_id: UUID, personne_id: UUID, identifiant: str, partage_familial: bool,
                       cree_par: UUID, *, valkey, langue: str) -> CompteCree:
    """TEN_RESSOURCE_INTROUVABLE (personne invisible), TEN_RESSOURCE_DEJA_EXISTANTE (déjà un compte),
    AUT_IDENTIFIANT_DEJA_UTILISE (sans déclaration). Événements compte.cree puis compte.invite."""
async def renvoyer_invitation(tenant_id: UUID, compte_id: UUID, *, valkey) -> CompteCree
async def changer_identifiant_administratif(tenant_id: UUID, compte_id: UUID, nouveau: str, par: UUID, *, valkey) -> None
async def suspendre(tenant_id: UUID, compte_id: UUID, par: UUID, *, valkey) -> None:
    """Statut suspendu + événement dans la transaction ; après COMMIT : révocation des sessions,
    oubli des appareils (éphémère)."""
async def identifiant_partage(tenant_id: UUID, compte_id: UUID) -> bool:
    """Ce que T1b lira avant de poser un rattachement de personnel."""

async def demander_changement(session: SessionCourante, nouveau: str, *, valkey, politique) -> None
async def verifier_changement(session: SessionCourante, code: str, *, valkey) -> None

async def consommer_envoi(tenant_id: UUID, evenement: Evenement, passerelle: PasserelleSms,
                          valkey, gabarits: Gabarits) -> None:
    """Lit le texte en clair dans Valkey par envoi_id, compose, envoie, efface. Idempotent."""
```

`Appareil` est le secret lu du cookie `nelo_appareils` par la route, jamais par le service ;
`SessionCourante` vient de `scope["state"]`. Le service reçoit `valkey` et `politique`
(`PolitiqueSecurite`) en paramètres : il n'importe ni `api` ni la configuration.

**Fonctions d'accès** (`acces.py`, toutes exercées ou P-12 échoue) : `inserer_compte`,
`lire_compte`, `lire_comptes_par_identifiant_dans_tenant`, `appeler_comptes_par_identifiant`,
`appeler_compte_par_invitation`, `appeler_compte_par_id_sans_tenant`, `poser_statut`,
`poser_pin`, `poser_verrou_pin`, `poser_invitation`, `poser_identifiant`,
`poser_derniere_connexion`, `compter_meme_identifiant`, `inserer_affectation`,
`affectation_vivante`, `lire_rattachements`, `inserer_evenement`, et les trois de l'outbox
partagée.

## `modules.socle.personnes` : le noyau

```python
__all__ = ["Identite", "lire_identite", "lire_identites", "creer_personne"]

async def lire_identite(tenant_id: UUID, personne_id: UUID) -> Identite | None   # nom, prenoms, langue
async def lire_identites(tenant_id: UUID, personne_ids: list[UUID]) -> dict[UUID, Identite]
async def creer_personne(tenant_id: UUID, nom: str, prenoms: str, langue: str, telephone: str | None) -> UUID
    """Seeds et tests ; T3a livre la route."""
```

## `modules.socle.annees` : le noyau

```python
__all__ = ["Annee", "lire_annees", "etablissement_de_annee", "creer_annee"]

async def lire_annees(tenant_id: UUID, etablissement_id: UUID) -> list[Annee]   # id, libelle, etat
async def etablissement_de_annee(tenant_id: UUID, annee_id: UUID) -> UUID | None
async def creer_annee(tenant_id: UUID, etablissement_id: UUID, libelle: str, debut: date, fin: date, etat: str) -> UUID
    """Seeds et tests ; aucune transition. T2a livre le cycle de vie."""
```

## `modules.socle.tenants` : ce que la tranche y ajoute

```python
# retiré : tenant_de_etablissement (provisoire jusqu'à T1a)
# ajouté :
async def lire_etablissements(tenant_id: UUID, ids: list[UUID]) -> list[Etablissement]   # nom, telephone, fuseau, administrateur_compte_id
async def designer_administrateur(tenant_id: UUID, etablissement_id: UUID, compte_id: UUID | None) -> None
async def lire_pack(pays_code: str, version: int) -> Pack   # devise, langues, decoupage, telephone, vocabulaire
```

`consommer_lot`, `reprendre_evenements` et `tenants_pour_travailleur` restent ; la prise, le
marquage et la reprise deviennent génériques dans `modules/shared/outbox.py`, appelés par chaque
module sur sa table.

## `modules.socle.communication` : ce qui change

```python
@dataclass(frozen=True, slots=True)
class EnvoiSimule:
    destinataire_e164: str; texte: str; reference: ReferenceEnvoi; envoye_le: datetime

class SimulationPasserelleSms(PasserelleSms):
    def __init__(self, mode: ModeSimulation, delai: timedelta, journal: Path | None = None): ...
    envoyes: list[EnvoiSimule]
```

## `modules.shared` : ce qui change

- `outbox.py` : `prendre(connexion, table, tenant_id, n)`, `marquer_traite`, `marquer_echec`,
  `reprendre_pris_orphelins`, `reprendre_en_echec` : les mêmes requêtes que T0a, paramétrées par
  la table du module.
- `contexte.py` : `Administrateur.prenoms` accepte la chaîne vide ; rien d'autre.
- `erreurs.py` : `ErreurMetier` gagne `en_tetes: dict[str, str]` (pour `Retry-After`).

## `api` : la composition

| Élément | Fichier | Rôle |
|---|---|---|
| utilitaires ASGI | `api/asgi.py` | `CHEMINS_LIBRES`, `en_tete`, `chemin_de_route`, repris de l'ancien provisoire |
| session | `api/session.py` | le middleware : `Authorization` → Valkey → `scope["state"]` (R-04) |
| établissement | `api/etablissement.py` | `X-Nelo-Etablissement` contre `affectation_vivante` |
| année | `api/annee.py` | `X-Nelo-Annee` et `ROUTES_PEDAGOGIQUES` |
| idempotence | `api/idempotence.py` | clé `idem:auth:` sur les chemins libres |
| limitation | `api/limitation.py` | `compter(valkey, cle, plafond, fenetre)` |
| consommateurs | `api/consommateurs.py` | `aiguilleur(passerelle, valkey, configuration)` |
| routes | `api/routes/authentification.py`, `moi.py`, `comptes.py` | les quinze routes de [openapi-attendu.yaml](openapi-attendu.yaml) |
| contrat | `api/contrat.py` | `EN_TETE_AUTHORIZATION`, `EN_TETE_ANNEE` (routes pédagogiques), chemins sans établissement élargis, `ContexteCapacites` retiré des schémas sans route |
| configuration | `api/configuration.py` | `secret_jeton`, `indicatif_defaut`, `cookies_secure`, `nom_produit`, `url_publique`, `sms_journal`, `relais_de_confiance` |

`api/` compose et **ne porte aucune règle métier** : la normalisation, les limites, les
transitions du compte, la rotation vivent dans `habilitations`.

## `web` : les briques neuves

| Brique | Fichier | Expose |
|---|---|---|
| relais | `web/server/api/v1/[...].ts` | `/api/v1/**` → API ; `nelo_acces` ↔ `Authorization` (R-09) |
| client | `web/app/core/api/client.ts`, `uuid7.ts`, `composables/useApi.ts` | `appeler(methode, chemin, corps?, { etablissement?, annee?, ecriture })`, rejeu après rafraîchissement |
| source | `web/app/core/contexte/api.ts` | `SourceApi implements SourceContexte` |
| session | `web/app/core/session/etat.ts`, `composables/useSession.ts` | `ouvrir*`, `fermer`, `comptesDeLAppareil` ; aucun jeton en mémoire |
| choix d'appareil | `web/app/core/appareil/choix.ts` | `lireEtablissementChoisi(stockage)`, `ecrire…`, idem année |
| garde | `web/app/middleware/session.global.ts` | sans contexte → `/connexion` |
| écrans | `web/app/pages/connexion.vue`, `connexion/code.vue`, `connexion/pin.vue`, `activation/[jeton].vue`, `compte/telephone.vue` | `sansCoquille`, composants de T0b |
| coquille | `CoquilleEntete.vue`, `Coquille.vue`, `app.vue` | `changerEtablissement`, `changerAnnee`, `deconnexion` |
| écrans déclarés | `web/ecrans.json`, `core/ecrans.ts` | champ `session` |
| portes | `web/tests/session.setup.ts`, `portes/outils.ts` | la session semée (R-11) |
