"""US4 : le noyau des personnes, ce que le contexte lit d'une personne et rien de plus.

Créer, relire une identité, en relire plusieurs d'un coup ; une personne inconnue rend `None`, et
une langue qui n'est pas un code de deux lettres est refusée **avant** l'écriture.
"""

import uuid

import pytest

from modules.shared import ErreurMetier
from modules.socle import personnes


async def test_creation_puis_lecture_de_l_identite(tenants_ab):
    personne_id = await personnes.creer_personne(
        tenants_ab.tenant_a, "Kouassi", "Ama Grâce", "fr", "+2250700000001"
    )
    identite = await personnes.lire_identite(tenants_ab.tenant_a, personne_id)
    assert identite == personnes.Identite(nom="Kouassi", prenoms="Ama Grâce", langue="fr")


async def test_plusieurs_identites_en_une_lecture(tenants_ab):
    premiere = await personnes.creer_personne(tenants_ab.tenant_a, "Diarra", "Ibrahim", "fr")
    seconde = await personnes.creer_personne(tenants_ab.tenant_a, "Koffi", "Adjoua", "en")
    inconnue = uuid.uuid7()

    identites = await personnes.lire_identites(tenants_ab.tenant_a, [premiere, seconde, inconnue])
    assert set(identites) == {premiere, seconde}
    assert identites[premiere].nom == "Diarra"
    assert identites[seconde].langue == "en"
    assert await personnes.lire_identites(tenants_ab.tenant_a, []) == {}


async def test_identite_inconnue_rend_none(tenants_ab):
    assert await personnes.lire_identite(tenants_ab.tenant_a, uuid.uuid7()) is None


async def test_la_personne_d_un_autre_tenant_est_inconnue(tenants_ab):
    personne_id = await personnes.creer_personne(tenants_ab.tenant_a, "Traoré", "Fanta", "fr")
    assert await personnes.lire_identite(tenants_ab.tenant_b, personne_id) is None
    assert await personnes.lire_identites(tenants_ab.tenant_b, [personne_id]) == {}


@pytest.mark.parametrize("langue", ["FR", "fra", "f", "", "fr-CI"])
async def test_langue_hors_motif_refusee(tenants_ab, langue):
    with pytest.raises(ErreurMetier) as refus:
        await personnes.creer_personne(tenants_ab.tenant_a, "Bamba", "Sekou", langue)
    assert refus.value.code == "VAL_SCHEMA_INVALIDE"
    assert refus.value.champ == "langue"
