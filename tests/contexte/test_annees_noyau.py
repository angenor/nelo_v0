"""US4 : le noyau des années, et l'invariant que T2a trouvera déjà posé.

Au plus une année `active` et une en `preparation` par établissement : les deux index partiels le
tiennent en base, le service traduit le refus en `409 ANN_ANNEE_ACTIVE_UNIQUE`. Aucune transition
n'existe en T1a : le cycle de vie appartient à T2a.
"""

import uuid
from datetime import date

import pytest
import pytest_asyncio

from modules.shared import ErreurMetier
from modules.socle import annees, tenants

DEBUT = date(2026, 9, 1)
FIN = date(2027, 7, 15)


@pytest_asyncio.fixture
async def etablissement_vierge(tenants_ab) -> uuid.UUID:
    """Un établissement sans année : celui de la fixture en porte déjà deux, semées.

    L'invariant s'étudie sur un établissement neuf ; le vérifier sur celui du jeu d'essai ne
    dirait que ce que la fixture a semé.
    """
    return await tenants.creer_etablissement(
        tenants_ab.tenant_a, "École sans année", "Africa/Abidjan"
    )


async def creer(tenants_ab, etablissement_id, libelle, etat, decalage_annees=0):
    return await annees.creer_annee(
        tenants_ab.tenant_a,
        etablissement_id,
        libelle,
        DEBUT.replace(year=DEBUT.year + decalage_annees),
        FIN.replace(year=FIN.year + decalage_annees),
        etat,
    )


async def test_creation_puis_lecture_des_annees(tenants_ab, etablissement_vierge):
    active = await creer(tenants_ab, etablissement_vierge, "2026-2027", "active")
    preparation = await creer(tenants_ab, etablissement_vierge, "2027-2028", "preparation", 1)

    lues = await annees.lire_annees(tenants_ab.tenant_a, etablissement_vierge)
    assert [(a.id, a.libelle, a.etat) for a in lues] == [
        (preparation, "2027-2028", "preparation"),
        (active, "2026-2027", "active"),
    ]
    assert lues[0] == annees.Annee(id=preparation, libelle="2027-2028", etat="preparation")


@pytest.mark.parametrize("etat", ["active", "preparation"])
async def test_deux_annees_du_meme_etat_refusees(tenants_ab, etablissement_vierge, etat):
    await creer(tenants_ab, etablissement_vierge, "2026-2027", etat)
    with pytest.raises(ErreurMetier) as refus:
        await creer(tenants_ab, etablissement_vierge, "2027-2028", etat, 1)
    assert refus.value.code == "ANN_ANNEE_ACTIVE_UNIQUE"
    assert refus.value.statut == 409
    assert refus.value.details["etat"] == etat
    # Le refus n'a rien laissé derrière lui : une seule année, celle du premier appel.
    lues = await annees.lire_annees(tenants_ab.tenant_a, etablissement_vierge)
    assert [a.libelle for a in lues] == ["2026-2027"]


async def test_un_autre_etablissement_a_droit_a_son_annee_active(tenants_ab, etablissement_vierge):
    second = await tenants.creer_etablissement(tenants_ab.tenant_a, "École A2", "Africa/Abidjan")
    premiere = await creer(tenants_ab, etablissement_vierge, "2026-2027", "active")
    seconde = await creer(tenants_ab, second, "2026-2027", "active")
    assert premiere != seconde
    assert [a.id for a in await annees.lire_annees(tenants_ab.tenant_a, second)] == [seconde]


async def test_etablissement_de_annee(tenants_ab, etablissement_vierge):
    annee_id = await creer(tenants_ab, etablissement_vierge, "2026-2027", "active")
    assert (
        await annees.etablissement_de_annee(tenants_ab.tenant_a, annee_id) == etablissement_vierge
    )
    assert await annees.etablissement_de_annee(tenants_ab.tenant_a, uuid.uuid7()) is None
    # L'année d'un autre tenant est introuvable, jamais empruntée.
    assert await annees.etablissement_de_annee(tenants_ab.tenant_b, annee_id) is None


def test_aucune_transition_disponible():
    """T1a pose l'état, jamais son changement : le cycle de vie est livré par T2a."""
    assert set(annees.__all__) == {"Annee", "lire_annees", "etablissement_de_annee", "creer_annee"}
    interdits = ("activer", "cloturer", "ouvrir", "archiver", "changer_etat", "dupliquer")
    assert not [nom for nom in dir(annees) if nom.startswith(interdits)]
