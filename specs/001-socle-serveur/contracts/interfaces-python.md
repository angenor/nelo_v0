# Interfaces de service — T0a, le socle serveur

Ce que chaque paquet expose par son `__init__.py`, et **rien d'autre n'en sort** (FR-007,
[01-stack.md § 2.5](../../../docs/01-stack.md) point 4). Les dépendances sont injectées à la
construction, jamais importées depuis un autre module. Les signatures sont données en Python
typé ; les corps appartiennent à l'implémentation.

## `modules.shared` — ce que tout le monde partage

```python
# modules/shared/__init__.py
__all__ = ["transaction", "EnveloppeErreur", "ErreurMetier", "DependanceIndisponible",
           "ModeSimulation", "uuid7"]

async def transaction(tenant_id: UUID) -> AsyncIterator[AsyncConnection]:
    """L'unique point d'entrée : ouvre la transaction, pose app.current_tenant, la rend, referme."""

class ErreurMetier(Exception):
    code: str          # préfixé par domaine, ex. TEN_PORTEE_INVALIDE
    statut: int        # 422 par défaut, 404 ou 409 selon la règle
    champ: str | None
    details: dict

class DependanceIndisponible(Exception):
    dependance: Literal["PASSERELLE_SMS", "AGREGATEUR_PAIEMENT", "SERVICE_INFERENCE"]

class ModeSimulation(StrEnum):
    SUCCES, ACCUSE_EN_RETARD, ACCUSE_EN_DOUBLE, JAMAIS_RECU, INDISPONIBLE
```

`EnveloppeErreur` est le modèle Pydantic de [03-api.md § 1.6](../../../docs/03-api.md). La table
`evenement_outbox` étant **par module**, `shared` ne porte pas de bus : il porte le contrat
`Evenement(type: str, charge: dict)` que chaque module écrit dans sa propre table.

## `modules.socle.tenants` — le module doré

```python
# modules/socle/tenants/__init__.py
__all__ = ["lire_parametres_effectifs", "poser_parametre", "valeur_effective",
           "tenant_de_etablissement", "ParametreEffectif", "ParametrePose", "Portee",
           "creer_tenant", "creer_etablissement"]

async def lire_parametres_effectifs(tenant_id: UUID, etablissement_id: UUID) -> list[ParametreEffectif]:
    """Chaque clé du catalogue, résolue à la portée de l'établissement."""

async def poser_parametre(tenant_id: UUID, cle: str, portee: Portee, portee_id: UUID,
                          valeur: bool | int | str | None) -> ParametrePose:
    """Valide contre le catalogue (TEN_PARAMETRE_INCONNU, TEN_PORTEE_INVALIDE, TEN_VALEUR_INVALIDE),
    UPSERT parametre_valeur ET INSERT evenement_outbox dans la même transaction."""

async def valeur_effective(tenant_id: UUID, cle: str, portee: Portee, portee_id: UUID) -> ValeurEffective:
    """Le trait unique de résolution tenant → établissement → site → cycle, surcharge locale."""

async def tenant_de_etablissement(etablissement_id: UUID) -> UUID | None:
    """PROVISOIRE jusqu'à T1a — passe par la fonction SECURITY DEFINER du schéma."""

async def creer_tenant(...) -> UUID
async def creer_etablissement(tenant_id: UUID, ...) -> UUID
    """Pour les seeds et les tests ; aucune route ne les expose en T0a."""
```

Ce que le `__init__.py` **n'exporte pas** : les objets `Table` de `tables.py`, les fonctions de
`acces.py`, le moteur, la connexion. Le même critère s'applique à `protection` — et c'est le test
du troisième verrou qui le vérifie sur lui.

**Fonctions d'accès aux données** (`acces.py`, toutes exercées ou P-12 échoue) :
`lire_catalogue`, `lire_valeurs_posees`, `upsert_valeur`, `lire_etablissement`, `inserer_evenement`,
`prendre_evenements`, `marquer_traite`, `marquer_echec`, `reprendre_pris_orphelins`,
`inserer_tenant`, `inserer_etablissement`, `appeler_tenant_de_etablissement`,
`appeler_tenants_pour_travailleur`.

**Événement émis** : `tenants.parametre.pose`, charge `{cle, portee, portee_id, valeur}`.

## `modules.socle.assistance` — le paquet, six capacités, aucune livrée

```python
# modules/socle/assistance/__init__.py
__all__ = ["Assistance", "Capacite", "EtatCapacite", "CapaciteNonLivree", "AssistanceSuspendue"]

class Capacite(StrEnum):
    C1_REDACTION_ASSISTEE, C2_QUESTION_REPONSE_DOCUMENTAIRE, C3_PLANIFICATION_SOUS_CONTRAINTES,
    C4_ANALYSE_ET_DETECTION_DE_SIGNAUX, C5_EXTRACTION_DOCUMENTAIRE, C6_ASSISTANCE_A_L_APPRENTISSAGE

class EtatCapacite(StrEnum):
    NON_LIVREE, SUSPENDUE, DISPONIBLE

LecteurSuspension = Callable[[UUID, UUID], Awaitable[bool]]   # (tenant_id, etablissement_id) -> suspendue ?

class Assistance:
    def __init__(self, lecteur_suspension: LecteurSuspension, inference: ServiceInference): ...
    async def etat_des_capacites(self, tenant_id: UUID, etablissement_id: UUID) -> dict[Capacite, EtatCapacite]:
        """SUSPENDUE pour les six si assistance.suspendue est vrai à cette portée ; sinon NON_LIVREE en T0a."""
    async def appeler(self, capacite: Capacite, tenant_id: UUID, etablissement_id: UUID, **entree) -> NoReturn:
        """Lève AssistanceSuspendue si suspendue, sinon CapaciteNonLivree. Aucune capacité ne répond en T0a."""
```

Le lecteur injecté est, dans `api/`, une fermeture sur `tenants.valeur_effective("assistance.suspendue",
ETABLISSEMENT, etablissement_id)`. `assistance` n'importe jamais `tenants`.

## Les trois abstractions — dessinées pour le fournisseur réel

Chacune : un `Protocol`, une simulation qui l'implémente, un mode lu de la configuration. L'accusé
**différé est le cas nominal** : la méthode d'envoi rend une référence, l'accusé se collecte à part,
et l'attente est **bornée**.

### `modules.socle.communication.passerelle_sms`

```python
class PasserelleSms(Protocol):
    async def envoyer(self, destinataire_e164: str, texte: str, reference: UUID) -> ReferenceEnvoi:
        """Fournisseur réel : soumission d'un message (ex. POST /messages) → identifiant fournisseur."""
    async def attendre_accuse(self, reference: ReferenceEnvoi, delai_max: timedelta) -> AccuseSms | None:
        """Fournisseur réel : rapport de remise reçu par webhook (DLR). None à l'échéance — jamais de blocage."""

class SimulationPasserelleSms(PasserelleSms):
    def __init__(self, mode: ModeSimulation, delai: timedelta): ...
```

| Mode | Comportement |
|---|---|
| `SUCCES` | accusé `REMIS` immédiat |
| `ACCUSE_EN_RETARD` | accusé après `delai` |
| `ACCUSE_EN_DOUBLE` | deux accusés pour la même référence |
| `JAMAIS_RECU` | aucun accusé ; `attendre_accuse` rend `None` à `delai_max` |
| `INDISPONIBLE` | `envoyer` lève `DependanceIndisponible("PASSERELLE_SMS")` |

### `modules.metier.finance.agregateur_paiement`

```python
class AgregateurPaiement(Protocol):
    async def initier(self, montant_unite_mineure: int, devise: str, reference: UUID,
                      payeur_e164: str) -> ReferencePaiement:
        """Fournisseur réel : initiation d'un paiement mobile → identifiant de transaction. Le montant
        est un entier d'unité mineure, l'exposant appartient à la devise (R2)."""
    async def attendre_confirmation(self, reference: ReferencePaiement, delai_max: timedelta) -> ConfirmationPaiement | None:
        """Fournisseur réel : webhook de confirmation. None à l'échéance — le webhook qui n'arrive jamais
        est le cas nominal (ADR 009)."""
```

Mêmes cinq modes ; `INDISPONIBLE` lève `DependanceIndisponible("AGREGATEUR_PAIEMENT")`.

### `modules.socle.assistance.service_inference`

```python
class ServiceInference(Protocol):
    async def soumettre(self, requete: RequeteInference) -> ReferenceInference:
        """Fournisseur réel : création d'une complétion ou d'un lot → identifiant."""
    async def attendre_resultat(self, reference: ReferenceInference, delai_max: timedelta) -> ResultatInference | None:
        """Fournisseur réel : lecture du résultat. Un fournisseur synchrone est servi en rendant le résultat
        dès le premier appel ; un fournisseur par lot est servi tel quel. None à l'échéance."""
```

Mêmes cinq modes ; `INDISPONIBLE` lève `DependanceIndisponible("SERVICE_INFERENCE")`. Le service
d'inférence **n'est pas dans `compose.yml`** (FR-002) : cette abstraction est sa seule existence en
T0a.

## `modules.metier.protection` — présent, vide, cloisonné

```python
# modules/metier/protection/__init__.py
__all__ = ["ServiceProtection"]

class ServiceProtection(Protocol):
    """L'interface de service, sans opération en T0a. Rien d'autre ne sort de ce module : ni entité,
    ni accès aux données, ni session — c'est le troisième verrou de P-11, et un test le lit."""
```

## `api` — la composition

| Élément | Fichier | Rôle |
|---|---|---|
| application | `api/main.py` | crée l'app, monte les middlewares, les gestionnaires d'erreur, les routes, le `lifespan` (travailleur) |
| configuration | `api/configuration.py` | `pydantic-settings`, préfixe `NELO_` |
| middleware d'idempotence | `api/idempotence.py` | R-06 |
| middleware d'établissement | `api/tenant_provisoire.py` | R-16, **provisoire jusqu'à T1a** |
| point d'insertion | `api/capacites.py` | `exiger_capacite(code)` — vide jusqu'à T1b |
| enveloppe et gestionnaires | `api/erreurs.py` | `RequestValidationError` → `422 VAL_SCHEMA_INVALIDE` ; `ErreurMetier` → son statut ; `DependanceIndisponible` → `503 API_DEPENDANCE_INDISPONIBLE` ; reste → `500 API_ERREUR_INTERNE` |
| routes | `api/routes/parametres.py`, `api/routes/sante.py` | les trois routes, et rien d'autre |
| travailleur | `api/travailleur.py` | la boucle de R-09 |
| écriture du contrat | `api/contrat.py` | `python -m api.contrat` écrit `contrat/openapi.json` avec les en-têtes de middleware ajoutés |

`api/` importe tout ce dont il a besoin et **ne porte aucune règle métier**
([01-stack.md § 2.4](../../../docs/01-stack.md)) : la validation du catalogue, la résolution des
portées et l'écriture de l'événement sont dans `tenants`.
