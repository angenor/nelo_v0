"""Le service du module doré : tenants, établissements, catalogue de paramètres.

Aucune classe de base, aucun dépôt générique (FR-010) : des fonctions, une transaction par
opération, des accès nommés. Les règles s'appliquent **après** le schéma Pydantic et **avant**
toute écriture ; l'événement s'écrit dans la transaction du changement d'état.
"""

import re
import uuid
from collections.abc import Awaitable, Callable, Mapping
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from modules.shared import ErreurMetier, Evenement, transaction
from modules.shared.bd import sans_tenant
from modules.socle.tenants import acces
from modules.socle.tenants.schemas import (
    ParametreEffectif,
    ParametrePose,
    Portee,
    TypeParametre,
    ValeurParametre,
)

# De la plus large à la plus fine : la résolution remonte cet ordre à l'envers.
ORDRE_DES_PORTEES = (Portee.TENANT, Portee.ETABLISSEMENT, Portee.SITE, Portee.CYCLE)
# Les portées dont l'entité existe ; SITE et CYCLE arrivent avec les tranches qui créent leurs tables.
PORTEES_DISPONIBLES = (Portee.TENANT, Portee.ETABLISSEMENT)

EVENEMENT_PARAMETRE_POSE = "tenants.parametre.pose"

_PLAGE_HORAIRE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$")

type Chaine = list[tuple[Portee, UUID]]


async def creer_tenant(
    nom: str,
    pays_code: str,
    *,
    country_pack_version: int = 1,
    raison_sociale: str | None = None,
) -> UUID:
    """Pour les seeds et les tests ; aucune route ne l'expose en T0a. `pays_code` est une donnée."""
    tenant_id = uuid.uuid7()
    async with transaction(tenant_id) as connexion:
        await acces.inserer_tenant(
            connexion, tenant_id, nom, pays_code, country_pack_version, raison_sociale
        )
    return tenant_id


async def creer_etablissement(tenant_id: UUID, nom: str, fuseau_horaire: str) -> UUID:
    """Pour les seeds et les tests ; aucune route ne l'expose en T0a."""
    etablissement_id = uuid.uuid7()
    async with transaction(tenant_id) as connexion:
        await acces.inserer_etablissement(
            connexion, etablissement_id, tenant_id, nom, fuseau_horaire
        )
    return etablissement_id


async def tenant_de_etablissement(etablissement_id: UUID) -> UUID | None:
    """PROVISOIRE jusqu'à T1a — passe par la fonction SECURITY DEFINER du schéma."""
    async with sans_tenant() as connexion:
        return await acces.appeler_tenant_de_etablissement(connexion, etablissement_id)


async def tenants_pour_travailleur() -> list[UUID]:
    """Les tenants que le travailleur d'événements parcourt — fonction SECURITY DEFINER."""
    async with sans_tenant() as connexion:
        return await acces.appeler_tenants_pour_travailleur(connexion)


# --- La résolution : un seul trait, quatre portées -------------------------------------------


def resoudre(
    entree: Mapping[str, Any],
    posees: dict[tuple[str, UUID], Any],
    chaine: Chaine,
) -> ParametreEffectif:
    """Le trait unique de résolution : la valeur posée à la portée la plus fine de la chaîne gagne.

    La chaîne est remontée `CYCLE → SITE → ÉTABLISSEMENT → TENANT`, puis vient le défaut du
    catalogue, puis `NON_DEFINIE`. La réponse dit toujours à quelle portée la valeur a été trouvée.
    """
    for portee, portee_id in sorted(
        chaine, key=lambda m: ORDRE_DES_PORTEES.index(m[0]), reverse=True
    ):
        if (portee, portee_id) in posees:
            return ParametreEffectif(
                cle=entree["cle"],
                type=entree["type"],
                valeur=posees[(portee, portee_id)],
                portee_resolue=portee,
                portee_id=portee_id,
                source="VALEUR",
            )
    defaut = entree["valeur_defaut"]
    return ParametreEffectif(
        cle=entree["cle"],
        type=entree["type"],
        valeur=defaut,
        portee_resolue=None,
        portee_id=None,
        source="DEFAUT" if defaut is not None else "NON_DEFINIE",
    )


def _chaine(tenant_id: UUID, portee: Portee, portee_id: UUID) -> Chaine:
    """Les maillons de la portée demandée jusqu'au tenant."""
    if portee == Portee.TENANT:
        return [(Portee.TENANT, tenant_id)]
    if portee == Portee.ETABLISSEMENT:
        return [(Portee.ETABLISSEMENT, portee_id), (Portee.TENANT, tenant_id)]
    raise _portee_invalide(portee, None)


def _posees(lignes) -> dict[str, dict[tuple[str, UUID], Any]]:
    par_cle: dict[str, dict[tuple[str, UUID], Any]] = {}
    for ligne in lignes:
        par_cle.setdefault(ligne["cle"], {})[(Portee(ligne["portee"]), ligne["portee_id"])] = ligne[
            "valeur"
        ]
    return par_cle


async def lire_parametres_effectifs(
    tenant_id: UUID, etablissement_id: UUID
) -> list[ParametreEffectif]:
    """Chaque clé du catalogue, résolue à la portée de l'établissement."""
    chaine = _chaine(tenant_id, Portee.ETABLISSEMENT, etablissement_id)
    async with transaction(tenant_id) as connexion:
        catalogue = await acces.lire_catalogue(connexion)
        posees = _posees(
            await acces.lire_valeurs_posees(connexion, tenant_id, [e["cle"] for e in catalogue])
        )
    return [resoudre(entree, posees.get(entree["cle"], {}), chaine) for entree in catalogue]


async def valeur_effective(
    tenant_id: UUID, cle: str, portee: Portee, portee_id: UUID
) -> ParametreEffectif:
    """Le trait unique de résolution tenant → établissement → site → cycle, surcharge locale."""
    chaine = _chaine(tenant_id, portee, portee_id)
    async with transaction(tenant_id) as connexion:
        catalogue = {e["cle"]: e for e in await acces.lire_catalogue(connexion)}
        if cle not in catalogue:
            raise _parametre_inconnu(list(catalogue))
        posees = _posees(await acces.lire_valeurs_posees(connexion, tenant_id, [cle]))
    return resoudre(catalogue[cle], posees.get(cle, {}), chaine)


# --- L'écriture : cinq règles, puis la valeur et l'événement dans la même transaction ----------


async def poser_parametre(
    tenant_id: UUID,
    cle: str,
    portee: Portee,
    portee_id: UUID,
    valeur: ValeurParametre,
) -> ParametrePose:
    """Valide contre le catalogue (TEN_PARAMETRE_INCONNU, TEN_PORTEE_INVALIDE, TEN_VALEUR_INVALIDE),
    UPSERT parametre_valeur ET INSERT evenement_outbox dans la même transaction."""
    async with transaction(tenant_id) as connexion:
        # 1. La clé est au catalogue.
        catalogue = {e["cle"]: e for e in await acces.lire_catalogue(connexion)}
        entree = catalogue.get(cle)
        if entree is None:
            raise _parametre_inconnu(list(catalogue))

        # 2 et 3. La portée n'est pas plus fine que permise, et son entité existe.
        la_plus_basse = Portee(entree["portee_la_plus_basse"])
        if portee not in _portees_permises(la_plus_basse):
            raise _portee_invalide(portee, la_plus_basse)

        # 4. La portée désigne le tenant courant, ou un établissement visible de lui.
        if portee == Portee.TENANT and portee_id != tenant_id:
            raise ErreurMetier(
                "TEN_PORTEE_INVALIDE",
                "la portée TENANT désigne un autre tenant que le tenant courant",
                champ="portee_id",
                details={"motif": "HORS_TENANT"},
            )
        if (
            portee == Portee.ETABLISSEMENT
            and await acces.lire_etablissement(connexion, portee_id) is None
        ):
            raise ErreurMetier("TEN_RESSOURCE_INTROUVABLE", "établissement introuvable", statut=404)

        # 5. La valeur a le type du catalogue.
        type_attendu = TypeParametre(entree["type"])
        if not valeur_conforme(type_attendu, valeur):
            raise ErreurMetier(
                "TEN_VALEUR_INVALIDE",
                f"la valeur ne correspond pas au type {type_attendu} de la clé",
                champ="valeur",
                details={"type_attendu": type_attendu.value},
            )

        ligne = await acces.upsert_valeur(connexion, tenant_id, cle, portee, portee_id, valeur)
        await acces.inserer_evenement(
            connexion,
            tenant_id,
            Evenement(
                EVENEMENT_PARAMETRE_POSE,
                {"cle": cle, "portee": portee.value, "portee_id": str(portee_id), "valeur": valeur},
            ),
        )
    return ParametrePose(
        cle=ligne["cle"],
        portee=ligne["portee"],
        portee_id=ligne["portee_id"],
        valeur=ligne["valeur"],
        pose_le=ligne["pose_le"],
    )


def valeur_conforme(type_attendu: TypeParametre, valeur: ValeurParametre) -> bool:
    match type_attendu:
        case TypeParametre.BOOLEEN:
            return isinstance(valeur, bool)
        case TypeParametre.ENTIER:
            return isinstance(valeur, int) and not isinstance(valeur, bool)
        case TypeParametre.DECIMAL:
            if not isinstance(valeur, str):
                return False
            try:
                return Decimal(valeur).is_finite()
            except InvalidOperation:
                return False
        case TypeParametre.CHAINE:
            return isinstance(valeur, str)
        case TypeParametre.PLAGE_HORAIRE:
            return isinstance(valeur, str) and _PLAGE_HORAIRE.match(valeur) is not None


def _portees_permises(la_plus_basse: Portee) -> list[Portee]:
    rang = ORDRE_DES_PORTEES.index(la_plus_basse)
    return [p for p in PORTEES_DISPONIBLES if ORDRE_DES_PORTEES.index(p) <= rang]


def _parametre_inconnu(cles_connues: list[str]) -> ErreurMetier:
    return ErreurMetier(
        "TEN_PARAMETRE_INCONNU",
        "la clé n'est pas au catalogue des paramètres",
        details={"cles_connues": sorted(cles_connues)},
    )


def _portee_invalide(portee: Portee, la_plus_basse: Portee | None) -> ErreurMetier:
    details: dict[str, Any] = {
        "portees_disponibles": [
            p.value
            for p in (_portees_permises(la_plus_basse) if la_plus_basse else PORTEES_DISPONIBLES)
        ]
    }
    if la_plus_basse is not None:
        details["portee_la_plus_basse"] = la_plus_basse.value
    return ErreurMetier(
        "TEN_PORTEE_INVALIDE",
        f"la portée {portee} n'est pas permise pour cette clé",
        champ="portee",
        details=details,
    )


# --- L'outbox : consommée par tenant, dans l'ordre d'écriture, au moins une fois ---------------

type Consommateur = Callable[[UUID, UUID, Evenement], Awaitable[None]]


async def reprendre_evenements(tenant_id: UUID, delai_orphelin: timedelta) -> None:
    """Les `pris` orphelins et les `en_echec` repassent `en_attente` : ils seront livrés à nouveau."""
    async with transaction(tenant_id) as connexion:
        await acces.reprendre_pris_orphelins(connexion, tenant_id, delai_orphelin)
        await acces.reprendre_en_echec(connexion, tenant_id)


async def consommer_lot(tenant_id: UUID, consommateur: Consommateur, n: int) -> int:
    """Jusqu'à `n` événements du tenant, un par un, dans l'ordre d'écriture.

    Chaque événement est pris dans sa transaction, passé au consommateur hors transaction, puis
    marqué dans une autre. Au premier échec, le lot s'arrête : l'événement suivant ne passe pas
    devant celui qui a échoué, qui sera repris au tour suivant. Rend le nombre d'événements traités.
    """
    traites = 0
    for _ in range(n):
        async with transaction(tenant_id) as connexion:
            pris = await acces.prendre_evenements(connexion, tenant_id, 1)
        if not pris:
            break
        ligne = pris[0]
        try:
            await consommateur(tenant_id, ligne["id"], Evenement(ligne["type"], ligne["charge"]))
        except Exception as erreur:
            async with transaction(tenant_id) as connexion:
                await acces.marquer_echec(
                    connexion, ligne["id"], f"{type(erreur).__name__} : {erreur}"[:500]
                )
            break
        async with transaction(tenant_id) as connexion:
            await acces.marquer_traite(connexion, ligne["id"])
        traites += 1
    return traites
