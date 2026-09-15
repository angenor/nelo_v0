"""R-07 — les fonctions SECURITY DEFINER sont exactement les deux nommées, et personne d'autre."""

from sqlalchemy import text

from modules.shared import transaction

ATTENDUES = {"tenant_de_etablissement", "tenants_pour_travailleur"}


async def test_deux_fonctions_et_pas_une_de_plus(tenants_ab):
    async with transaction(tenants_ab.tenant_a) as connexion:
        resultat = await connexion.execute(
            text(
                "SELECT p.proname, pg_get_userbyid(p.proowner), "
                "EXISTS (SELECT 1 FROM aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a "
                "        WHERE a.grantee = 0 AND a.privilege_type = 'EXECUTE') "
                "FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
                "WHERE p.prosecdef AND n.nspname NOT IN ('pg_catalog', 'information_schema') "
                "AND n.nspname NOT LIKE 'pg_%'"
            )
        )
        fonctions = {r[0]: (r[1], r[2]) for r in resultat}
    assert set(fonctions) == ATTENDUES
    for nom, (proprietaire, public_execute) in fonctions.items():
        assert proprietaire == "nelo_proprietaire", nom
        assert public_execute is False, f"PUBLIC peut exécuter {nom}"
