"""Le noyau des années scolaires : l'année, son outbox, leurs politiques.

Révision : 0001
Précédente : aucune

Ce que T1a en pose (research.md R-02) : de quoi vérifier l'en-tête d'année et composer le
contexte. **Aucune transition d'état** n'est livrée ; les deux index partiels d'unicité de
docs/02-domaine.md § 4.5 sont posés dès maintenant pour que T2a les trouve.

Aucune clé étrangère ne sort du schéma : `etablissement_id` est un identifiant.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TENANT_COURANT = "NULLIF(current_setting('app.current_tenant', true), '')::uuid"


def upgrade() -> None:
    op.create_table(
        "annee_scolaire",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("etablissement_id", UUID(as_uuid=True), nullable=False),
        sa.Column("libelle", sa.Text, nullable=False),
        sa.Column("debut", sa.Date, nullable=False),
        sa.Column("fin", sa.Date, nullable=False),
        sa.Column("etat", sa.Text, nullable=False, server_default=sa.text("'preparation'")),
        sa.Column(
            "cree_le", TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "etat IN ('preparation', 'active', 'cloturee', 'archivee')", name="ck_annee_etat"
        ),
        schema="annees",
    )
    op.create_index(
        "ix_annee_etablissement",
        "annee_scolaire",
        ["tenant_id", "etablissement_id"],
        schema="annees",
    )
    # Au plus une année active, et une en préparation, par établissement : l'invariant de § 4.5.
    op.create_index(
        "uq_annee_active",
        "annee_scolaire",
        ["tenant_id", "etablissement_id"],
        unique=True,
        postgresql_where=sa.text("etat = 'active'"),
        schema="annees",
    )
    op.create_index(
        "uq_annee_preparation",
        "annee_scolaire",
        ["tenant_id", "etablissement_id"],
        unique=True,
        postgresql_where=sa.text("etat = 'preparation'"),
        schema="annees",
    )

    op.create_table(
        "evenement_outbox",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
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
        schema="annees",
    )
    op.create_index(
        "ix_evenement_file",
        "evenement_outbox",
        ["tenant_id", "etat", "ecrit_le", "id"],
        schema="annees",
    )

    for table in ("annee_scolaire", "evenement_outbox"):
        op.execute(f"ALTER TABLE annees.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE annees.{table} FORCE ROW LEVEL SECURITY")

    op.execute(
        f"CREATE POLICY isolation_tenant ON annees.annee_scolaire FOR ALL "
        f"USING (tenant_id = {TENANT_COURANT}) WITH CHECK (tenant_id = {TENANT_COURANT})"
    )
    op.execute(
        f"CREATE POLICY lecture_tenant ON annees.evenement_outbox FOR SELECT "
        f"USING (tenant_id = {TENANT_COURANT})"
    )
    op.execute(
        f"CREATE POLICY ecriture_tenant ON annees.evenement_outbox FOR INSERT "
        f"WITH CHECK (tenant_id = {TENANT_COURANT})"
    )
    op.execute(
        f"CREATE POLICY marquage_tenant ON annees.evenement_outbox FOR UPDATE "
        f"USING (tenant_id = {TENANT_COURANT}) WITH CHECK (tenant_id = {TENANT_COURANT})"
    )

    op.execute("GRANT USAGE ON SCHEMA annees TO nelo_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON annees.annee_scolaire, annees.evenement_outbox TO nelo_app"
    )


def downgrade() -> None:
    op.drop_table("evenement_outbox", schema="annees")
    op.drop_table("annee_scolaire", schema="annees")
    op.execute("REVOKE USAGE ON SCHEMA annees FROM nelo_app")
