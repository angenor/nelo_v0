"""R-07 : l'application est nelo_app, qui ne contourne jamais la RLS ; chaque table est forcée.

FR-045 : « chaque table neuve porte la politique de sécurité au niveau ligne activée et forcée ».
Le parcours va chercher les tables **dans les quatre schémas**, depuis le catalogue de PostgreSQL :
une table ajoutée demain par une migration sans politique apparaît ici d'office, et fait tomber ce
test sans que personne ait pensé à l'y inscrire.
"""

import pytest
from sqlalchemy import text

from modules.shared import transaction
from tests.isolation.schema import SCHEMAS, tables_du_schema


async def test_le_role_applicatif_ne_contourne_jamais_la_rls(tenants_ab):
    async with transaction(tenants_ab.tenant_a) as connexion:
        assert await connexion.scalar(text("SELECT current_user")) == "nelo_app"
        assert (
            await connexion.scalar(
                text("SELECT rolbypassrls OR rolsuper FROM pg_roles WHERE rolname = 'nelo_app'")
            )
            is False
        )


@pytest.mark.parametrize("schema", SCHEMAS)
async def test_chaque_table_est_possedee_et_forcee(tenants_ab, schema):
    async with transaction(tenants_ab.tenant_a) as connexion:
        noms = await tables_du_schema(connexion, schema)
        resultat = await connexion.execute(
            text(
                "SELECT c.relname, pg_get_userbyid(c.relowner), c.relrowsecurity, c.relforcerowsecurity "
                "FROM pg_class c WHERE c.relnamespace = CAST(:schema AS regnamespace) AND c.relkind = 'r'"
            ),
            {"schema": schema},
        )
        lignes = {r[0]: r[1:] for r in resultat}
    for nom in noms:
        proprietaire, active, forcee = lignes[nom]
        assert proprietaire == "nelo_proprietaire", f"{schema}.{nom}"
        assert active and forcee, f"{schema}.{nom} : RLS non activée ou non forcée"


@pytest.mark.parametrize("schema", SCHEMAS)
async def test_chaque_table_porte_au_moins_une_politique(tenants_ab, schema):
    """Forcer la RLS sans politique ferme la table à tout le monde, y compris à l'application."""
    async with transaction(tenants_ab.tenant_a) as connexion:
        noms = await tables_du_schema(connexion, schema)
        resultat = await connexion.execute(
            text(
                "SELECT tablename, count(*) FROM pg_policies WHERE schemaname = :schema "
                "GROUP BY tablename"
            ),
            {"schema": schema},
        )
        politiques = dict(resultat.all())
    for nom in noms:
        assert politiques.get(nom, 0) >= 1, f"{schema}.{nom} : aucune politique"
