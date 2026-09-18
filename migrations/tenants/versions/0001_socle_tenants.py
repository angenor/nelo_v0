"""Le socle tenants : cinq tables, leurs politiques, deux fonctions, le catalogue.

Révision : 0001
Précédente : aucune

Chaque table porte `ENABLE` **et** `FORCE ROW LEVEL SECURITY`. L'expression de tenant est
`NULLIF(current_setting('app.current_tenant', true), '')::uuid` : absente, elle vaut `NULL` et
aucune ligne ne passe — jamais « toutes ». Le `NULLIF` couvre la connexion réutilisée, où la
variable, une fois connue de la session, revient à la chaîne vide après la transaction.

Le rôle propriétaire exécute les migrations et possède les fonctions `SECURITY DEFINER` ; il doit
contourner la RLS (superutilisateur en développement, `BYPASSRLS` ailleurs). L'application n'accède
que par `nelo_app`, qui ne la contourne jamais.

Le `downgrade` retire tout ce que l'`upgrade` a créé, sauf le schéma lui-même : il porte la table
de version du module (`tenants.alembic_version`), qu'Alembic doit pouvoir mettre à jour.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

from modules.socle.tenants.catalogue_seed import entrees_de

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TENANT_COURANT = "NULLIF(current_setting('app.current_tenant', true), '')::uuid"
PORTEES = "portee IN ('TENANT', 'ETABLISSEMENT', 'SITE', 'CYCLE')"


def upgrade() -> None:
    op.create_table(
        "tenant",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("nom", sa.Text, nullable=False),
        sa.Column("raison_sociale", sa.Text),
        sa.Column("pays_code", sa.Text, nullable=False),
        sa.Column("country_pack_version", sa.Integer, nullable=False),
        sa.Column("statut_abonnement", sa.Text, nullable=False, server_default=sa.text("'ACTIF'")),
        sa.Column("branding", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "cree_le", TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        schema="tenants",
    )
    op.create_table(
        "etablissement",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.tenant.id"), nullable=False
        ),
        sa.Column("nom", sa.Text, nullable=False),
        sa.Column("code_officiel", sa.Text),
        sa.Column("agrement", sa.Text),
        sa.Column("fuseau_horaire", sa.Text, nullable=False),
        sa.Column("telephone", sa.Text),
        sa.Column("direction_regionale", sa.Text),
        sa.Column(
            "cree_le", TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        schema="tenants",
    )
    op.create_index("ix_etablissement_tenant", "etablissement", ["tenant_id"], schema="tenants")
    catalogue = op.create_table(
        "parametre_catalogue",
        sa.Column("cle", sa.Text, primary_key=True),
        sa.Column("portee_la_plus_basse", sa.Text, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("valeur_defaut", JSONB(none_as_null=True)),
        sa.Column("origine_defaut", sa.Text, nullable=False),
        sa.Column("description_cle", sa.Text, nullable=False),
        sa.CheckConstraint(
            "portee_la_plus_basse IN ('TENANT', 'ETABLISSEMENT', 'SITE', 'CYCLE')",
            name="ck_catalogue_portee",
        ),
        sa.CheckConstraint(
            "type IN ('ENTIER', 'DECIMAL', 'BOOLEEN', 'CHAINE', 'PLAGE_HORAIRE')",
            name="ck_catalogue_type",
        ),
        sa.CheckConstraint(
            "origine_defaut IN ('LITTERALE', 'COUNTRY_PACK', 'OBLIGATOIRE')",
            name="ck_catalogue_origine",
        ),
        schema="tenants",
    )
    op.create_table(
        "parametre_valeur",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.tenant.id"), nullable=False
        ),
        sa.Column("cle", sa.Text, sa.ForeignKey("tenants.parametre_catalogue.cle"), nullable=False),
        sa.Column("portee", sa.Text, nullable=False),
        sa.Column("portee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("valeur", JSONB, nullable=False),
        sa.Column(
            "pose_le", TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(PORTEES, name="ck_valeur_portee"),
        sa.UniqueConstraint(
            "tenant_id", "cle", "portee", "portee_id", name="uq_valeur_cle_naturelle"
        ),
        schema="tenants",
    )
    op.create_index(
        "ix_valeur_tenant_cle", "parametre_valeur", ["tenant_id", "cle"], schema="tenants"
    )
    op.create_table(
        "evenement_outbox",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.tenant.id"), nullable=False
        ),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("charge", JSONB, nullable=False),
        sa.Column(
            "ecrit_le", TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("etat", sa.Text, nullable=False, server_default=sa.text("'en_attente'")),
        sa.Column("tentatives", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("pris_le", TIMESTAMP(timezone=True)),
        sa.Column("traite_le", TIMESTAMP(timezone=True)),
        sa.Column("derniere_erreur", sa.Text),
        sa.CheckConstraint(
            "etat IN ('en_attente', 'pris', 'traite', 'en_echec')", name="ck_evenement_etat"
        ),
        schema="tenants",
    )
    op.create_index(
        "ix_evenement_file",
        "evenement_outbox",
        ["tenant_id", "etat", "ecrit_le", "id"],
        schema="tenants",
    )

    # Le catalogue de docs/02-domaine.md § 17, alimenté sous le rôle propriétaire. Les clés
    # qu'une révision ultérieure ajoute ne sont pas de cette migration.
    op.bulk_insert(catalogue, list(entrees_de("0001")))

    # L'isolation : ENABLE et FORCE, une ligne par table.
    op.execute("ALTER TABLE tenants.tenant ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants.tenant FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants.etablissement ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants.etablissement FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants.parametre_catalogue ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants.parametre_catalogue FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants.parametre_valeur ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants.parametre_valeur FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants.evenement_outbox ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants.evenement_outbox FORCE ROW LEVEL SECURITY")

    op.execute(
        f"CREATE POLICY isolation_tenant ON tenants.tenant FOR ALL "
        f"USING (id = {TENANT_COURANT}) WITH CHECK (id = {TENANT_COURANT})"
    )
    op.execute(
        f"CREATE POLICY isolation_tenant ON tenants.etablissement FOR ALL "
        f"USING (tenant_id = {TENANT_COURANT}) WITH CHECK (tenant_id = {TENANT_COURANT})"
    )
    op.execute(
        "CREATE POLICY lecture_tenantee ON tenants.parametre_catalogue FOR SELECT "
        "USING (NULLIF(current_setting('app.current_tenant', true), '') IS NOT NULL)"
    )
    op.execute(
        f"CREATE POLICY isolation_tenant ON tenants.parametre_valeur FOR ALL "
        f"USING (tenant_id = {TENANT_COURANT}) WITH CHECK (tenant_id = {TENANT_COURANT})"
    )
    # L'outbox : lire, écrire, marquer — jamais effacer.
    op.execute(
        f"CREATE POLICY lecture_tenant ON tenants.evenement_outbox FOR SELECT "
        f"USING (tenant_id = {TENANT_COURANT})"
    )
    op.execute(
        f"CREATE POLICY ecriture_tenant ON tenants.evenement_outbox FOR INSERT "
        f"WITH CHECK (tenant_id = {TENANT_COURANT})"
    )
    op.execute(
        f"CREATE POLICY marquage_tenant ON tenants.evenement_outbox FOR UPDATE "
        f"USING (tenant_id = {TENANT_COURANT}) WITH CHECK (tenant_id = {TENANT_COURANT})"
    )

    op.execute("GRANT USAGE ON SCHEMA tenants TO nelo_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON tenants.tenant, tenants.etablissement, "
        "tenants.parametre_valeur, tenants.evenement_outbox TO nelo_app"
    )
    op.execute("GRANT SELECT ON tenants.parametre_catalogue TO nelo_app")

    # Les deux seules fonctions SECURITY DEFINER : elles ne renvoient que des identifiants.
    op.execute(
        """
        CREATE FUNCTION tenants.tenant_de_etablissement(p_etablissement uuid) RETURNS uuid
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
        AS $$ SELECT tenant_id FROM tenants.etablissement WHERE id = p_etablissement $$
        """
    )
    op.execute(
        """
        CREATE FUNCTION tenants.tenants_pour_travailleur() RETURNS SETOF uuid
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
        AS $$ SELECT id FROM tenants.tenant ORDER BY id $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION tenants.tenant_de_etablissement(uuid) FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION tenants.tenants_pour_travailleur() FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION tenants.tenant_de_etablissement(uuid) TO nelo_app")
    op.execute("GRANT EXECUTE ON FUNCTION tenants.tenants_pour_travailleur() TO nelo_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION tenants.tenants_pour_travailleur()")
    op.execute("DROP FUNCTION tenants.tenant_de_etablissement(uuid)")
    op.drop_table("evenement_outbox", schema="tenants")
    op.drop_table("parametre_valeur", schema="tenants")
    op.drop_table("parametre_catalogue", schema="tenants")
    op.drop_table("etablissement", schema="tenants")
    op.drop_table("tenant", schema="tenants")
    op.execute("REVOKE USAGE ON SCHEMA tenants FROM nelo_app")
