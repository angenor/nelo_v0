"""R-07 — l'application est nelo_app, qui ne contourne jamais la RLS ; les tables sont forcées."""

from sqlalchemy import text

from modules.shared import transaction
from tests.isolation.schema import SCHEMA, tables_du_schema


async def test_role_et_tables(tenants_ab):
    async with transaction(tenants_ab.tenant_a) as connexion:
        assert await connexion.scalar(text("SELECT current_user")) == "nelo_app"
        assert (
            await connexion.scalar(
                text("SELECT rolbypassrls OR rolsuper FROM pg_roles WHERE rolname = 'nelo_app'")
            )
            is False
        )
        noms = await tables_du_schema(connexion)
        resultat = await connexion.execute(
            text(
                "SELECT c.relname, pg_get_userbyid(c.relowner), c.relrowsecurity, c.relforcerowsecurity "
                "FROM pg_class c WHERE c.relnamespace = CAST(:schema AS regnamespace) AND c.relkind = 'r'"
            ),
            {"schema": SCHEMA},
        )
        lignes = {r[0]: r[1:] for r in resultat}
    for nom in noms:
        proprietaire, active, forcee = lignes[nom]
        assert proprietaire == "nelo_proprietaire", nom
        assert active and forcee, f"tenants.{nom} : RLS non activée ou non forcée"
