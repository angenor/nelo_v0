"""FR-018, A puis B sur la même connexion du pool : rien ne traverse."""

from sqlalchemy import text

from modules.shared import bd, transaction
from tests.isolation.schema import colonne, compter
from tests.module_dore.outils import poser


async def test_meme_connexion_rien_ne_traverse(
    client, sessions_ab, tenants_ab, moteur_pool_un, monkeypatch
):
    reponse = await poser(
        client,
        sessions_ab.a,
        tenants_ab.etab_a,
        "assistance.suspendue",
        "ETABLISSEMENT",
        tenants_ab.etab_a,
        True,
    )
    assert reponse.status_code == 200, reponse.text

    monkeypatch.setattr(bd, "_moteur", moteur_pool_un)
    requete_pid = text("SELECT pg_backend_pid()")
    requete_variable = text("SELECT current_setting('app.current_tenant', true)")

    async with transaction(tenants_ab.tenant_a) as connexion:
        pid_a = await connexion.scalar(requete_pid)
        assert await connexion.scalar(compter("parametre_valeur")) >= 1

    async with moteur_pool_un.connect() as connexion:
        assert await connexion.scalar(requete_pid) == pid_a
        assert (await connexion.scalar(requete_variable) or "") == ""

    async with transaction(tenants_ab.tenant_b) as connexion:
        assert await connexion.scalar(requete_pid) == pid_a
        assert (
            await connexion.scalar(compter("etablissement", colonne("id") == tenants_ab.etab_a))
            == 0
        )
        assert (
            await connexion.scalar(
                compter("parametre_valeur", colonne("tenant_id") == tenants_ab.tenant_a)
            )
            == 0
        )
        assert await connexion.scalar(compter("tenant")) == 1
