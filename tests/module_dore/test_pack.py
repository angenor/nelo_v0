"""FR-050, principe V : le pays vit dans le pack, en données semées, jamais dans le code.

Deux packs sont semés par la migration : celui du pays du pilote, et un pack **fictif** dont
aucune valeur ne coïncide avec le premier. Le second est le test d'agnosticité : si une valeur du
premier était écrite dans le code, elle apparaîtrait ici.
"""

import pytest

from modules.socle import tenants
from modules.socle.tenants.packs_seed import CODES_NEUTRES, COTE_D_IVOIRE, FICTIF

SEMES = [COTE_D_IVOIRE, FICTIF]


@pytest.mark.parametrize("seme", SEMES, ids=[p["pays_code"] for p in SEMES])
async def test_chaque_pack_seme_se_lit(tenants_ab, seme):
    pack = await tenants.lire_pack(tenants_ab.tenant_a, seme["pays_code"], seme["version"])
    assert pack is not None
    contenu = seme["contenu"]
    assert pack.devise.model_dump() == contenu["devise"]
    assert pack.langues == contenu["langues"]
    assert pack.decoupage == contenu["decoupage"]
    assert pack.indicatif == contenu["telephone"]["indicatif"]
    assert set(pack.vocabulaire) == set(CODES_NEUTRES)


async def test_les_dix_sept_codes_neutres_sont_traduits_dans_chaque_langue(tenants_ab):
    for seme in SEMES:
        pack = await tenants.lire_pack(tenants_ab.tenant_a, seme["pays_code"], seme["version"])
        assert pack is not None
        for code in CODES_NEUTRES:
            for langue in pack.langues:
                assert pack.vocabulaire[code][langue], f"{seme['pays_code']}/{code}/{langue}"


async def test_aucune_valeur_du_pack_fictif_ne_coincide_avec_l_autre(tenants_ab):
    """Le test d'agnosticité : deux packs qui se ressembleraient ne prouveraient rien."""
    un = await tenants.lire_pack(tenants_ab.tenant_a, "CI", 1)
    autre = await tenants.lire_pack(tenants_ab.tenant_a, "ZZ", 1)
    assert un is not None and autre is not None
    assert un.devise.code != autre.devise.code
    assert un.devise.exposant != autre.devise.exposant
    assert un.decoupage != autre.decoupage
    assert un.indicatif != autre.indicatif
    assert un.vocabulaire["CLASSE"]["fr"] != autre.vocabulaire["CLASSE"]["fr"]


async def test_un_pack_inconnu_rend_none(tenants_ab):
    assert await tenants.lire_pack(tenants_ab.tenant_a, "XX", 1) is None
    assert await tenants.lire_pack(tenants_ab.tenant_a, "CI", 99) is None
