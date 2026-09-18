"""Le noyau des personnes : la personne, son outbox, leurs politiques.

Révision : 0001
Précédente : aucune

Les seules colonnes de docs/02-domaine.md § 2.2 que le contexte lit (research.md R-02). T3a pose
les autres, sans renommer ni retirer celles-ci.

Aucune clé étrangère ne sort du schéma : `tenant_id` est un identifiant, son intégrité est tenue
par l'application et testée. Le `downgrade` retire tout ce que l'`upgrade` a créé, sauf le schéma,
qui porte la table de version du module.
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
        "personne",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("nom", sa.Text, nullable=False),
        sa.Column("prenoms", sa.Text, nullable=False),
        sa.Column("langue_preferee", sa.Text, nullable=False),
        sa.Column("telephone_principal", sa.Text),
        sa.Column(
            "cree_le", TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("langue_preferee ~ '^[a-z]{2}$'", name="ck_personne_langue"),
        schema="personnes",
    )
    op.create_index("ix_personne_tenant", "personne", ["tenant_id"], schema="personnes")

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
        schema="personnes",
    )
    op.create_index(
        "ix_evenement_file",
        "evenement_outbox",
        ["tenant_id", "etat", "ecrit_le", "id"],
        schema="personnes",
    )

    for table in ("personne", "evenement_outbox"):
        op.execute(f"ALTER TABLE personnes.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE personnes.{table} FORCE ROW LEVEL SECURITY")

    op.execute(
        f"CREATE POLICY isolation_tenant ON personnes.personne FOR ALL "
        f"USING (tenant_id = {TENANT_COURANT}) WITH CHECK (tenant_id = {TENANT_COURANT})"
    )
    # L'outbox : lire, écrire, marquer, jamais effacer.
    op.execute(
        f"CREATE POLICY lecture_tenant ON personnes.evenement_outbox FOR SELECT "
        f"USING (tenant_id = {TENANT_COURANT})"
    )
    op.execute(
        f"CREATE POLICY ecriture_tenant ON personnes.evenement_outbox FOR INSERT "
        f"WITH CHECK (tenant_id = {TENANT_COURANT})"
    )
    op.execute(
        f"CREATE POLICY marquage_tenant ON personnes.evenement_outbox FOR UPDATE "
        f"USING (tenant_id = {TENANT_COURANT}) WITH CHECK (tenant_id = {TENANT_COURANT})"
    )

    op.execute("GRANT USAGE ON SCHEMA personnes TO nelo_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON personnes.personne, personnes.evenement_outbox TO nelo_app"
    )


def downgrade() -> None:
    op.drop_table("evenement_outbox", schema="personnes")
    op.drop_table("personne", schema="personnes")
    op.execute("REVOKE USAGE ON SCHEMA personnes FROM nelo_app")
