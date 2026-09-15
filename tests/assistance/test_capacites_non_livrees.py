"""US7-1 — six capacités connues, aucune livrée : l'appel est un refus explicite, jamais un silence."""

import pytest

from modules.socle.assistance import Capacite, CapaciteNonLivree, EtatCapacite


async def test_six_capacites_non_livrees(application, tenants_ab):
    assistance = application.state.assistance
    etats = await assistance.etat_des_capacites(tenants_ab.tenant_b, tenants_ab.etab_b)
    assert len(Capacite) == 6
    attendu = EtatCapacite.SUSPENDUE if _suspendue() else EtatCapacite.NON_LIVREE
    assert etats == dict.fromkeys(Capacite, attendu)


@pytest.mark.parametrize("capacite", list(Capacite))
async def test_appeler_leve_capacite_non_livree(application, tenants_ab, capacite):
    from modules.socle.assistance import AssistanceSuspendue, service

    assistance = service.Assistance(_jamais_suspendue, application.state.service_inference)
    with pytest.raises(CapaciteNonLivree) as refus:
        await assistance.appeler(capacite, tenants_ab.tenant_a, tenants_ab.etab_a, texte="essai")
    assert refus.value.capacite == capacite
    assert capacite.value in str(refus.value)
    assert not isinstance(refus.value, AssistanceSuspendue)


async def _jamais_suspendue(tenant_id, etablissement_id) -> bool:
    return False


def _suspendue() -> bool:
    import os

    return os.environ.get("NELO_TEST_SUSPENSION") == "1"
