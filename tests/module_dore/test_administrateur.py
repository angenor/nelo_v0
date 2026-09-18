"""FR-049 : l'écran « aucun domaine » nomme quelqu'un, et ce quelqu'un est une donnée du tenant."""

import uuid

import pytest

from modules.shared import ErreurMetier
from modules.socle import tenants


async def test_un_etablissement_naît_sans_administrateur(tenants_ab):
    """L'établissement est semé ici : celui de la fixture reçoit un administrateur à sa création,
    pour que le compte de test soit rattaché quelque part. Un établissement neuf n'en a aucun."""
    neuf = await tenants.creer_etablissement(tenants_ab.tenant_a, "École neuve", "Africa/Abidjan")
    etablissements = await tenants.lire_etablissements(tenants_ab.tenant_a, [neuf])
    assert len(etablissements) == 1
    assert etablissements[0].administrateur_compte_id is None
    assert etablissements[0].nom
    assert etablissements[0].fuseau_horaire


async def test_designer_puis_retirer_l_administrateur(tenants_ab):
    compte_id = uuid.uuid7()
    await tenants.designer_administrateur(tenants_ab.tenant_a, tenants_ab.etab_a, compte_id)
    lu = await tenants.lire_etablissements(tenants_ab.tenant_a, [tenants_ab.etab_a])
    assert lu[0].administrateur_compte_id == compte_id

    await tenants.designer_administrateur(tenants_ab.tenant_a, tenants_ab.etab_a, None)
    lu = await tenants.lire_etablissements(tenants_ab.tenant_a, [tenants_ab.etab_a])
    assert lu[0].administrateur_compte_id is None


async def test_un_etablissement_d_un_autre_tenant_est_introuvable(tenants_ab):
    """Ni « interdit », ni silencieux : introuvable, comme toute ressource hors périmètre."""
    with pytest.raises(ErreurMetier) as refus:
        await tenants.designer_administrateur(tenants_ab.tenant_a, tenants_ab.etab_b, uuid.uuid7())
    assert refus.value.code == "TEN_RESSOURCE_INTROUVABLE"
    assert refus.value.statut == 404


async def test_lire_les_etablissements_d_un_autre_tenant_ne_rend_rien(tenants_ab):
    assert await tenants.lire_etablissements(tenants_ab.tenant_a, [tenants_ab.etab_b]) == []
    assert await tenants.lire_etablissements(tenants_ab.tenant_a, []) == []
