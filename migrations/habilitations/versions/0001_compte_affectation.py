"""Le compte et l'affectation : la première frontière de sécurité.

Révision : 0001
Précédente : aucune

Le compte porte le numéro normalisé, le statut, l'empreinte du code personnel et celle du lien
d'invitation. **Aucune unicité sur `identifiant`** : deux parents partagent un téléphone (US8), et
la déclaration de partage est un événement, pas une colonne.

Trois fonctions `SECURITY DEFINER` : elles répondent **avant que le tenant ne soit connu**, parce
qu'un numéro, un lien ou un appareil ne disent pas de quel tenant ils relèvent. Chacune ne renvoie
que des identifiants et un statut, jamais une donnée de personne.
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
        "compte",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("personne_id", UUID(as_uuid=True), nullable=False),
        sa.Column("identifiant", sa.Text, nullable=False),
        sa.Column("statut", sa.Text, nullable=False, server_default=sa.text("'invite'")),
        sa.Column("pin_empreinte", sa.Text),
        sa.Column("pin_verrouille_le", TIMESTAMP(timezone=True)),
        sa.Column("invitation_empreinte", sa.Text),
        sa.Column("invitation_expire_le", TIMESTAMP(timezone=True)),
        sa.Column("invite_le", TIMESTAMP(timezone=True)),
        sa.Column("derniere_connexion", TIMESTAMP(timezone=True)),
        sa.Column(
            "cree_le", TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("statut IN ('invite', 'actif', 'suspendu')", name="ck_compte_statut"),
        sa.UniqueConstraint("tenant_id", "personne_id", name="uq_compte_personne"),
        schema="habilitations",
    )
    op.create_index(
        "ix_compte_tenant_identifiant",
        "compte",
        ["tenant_id", "identifiant"],
        schema="habilitations",
    )
    op.create_index("ix_compte_identifiant", "compte", ["identifiant"], schema="habilitations")

    op.create_table(
        "affectation",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "compte_id",
            UUID(as_uuid=True),
            sa.ForeignKey("habilitations.compte.id"),
            nullable=False,
        ),
        sa.Column("annee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("etablissement_id", UUID(as_uuid=True), nullable=False),
        sa.Column("debut", sa.Date, nullable=False),
        sa.Column("fin", sa.Date),
        sa.Column(
            "cree_le", TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        schema="habilitations",
    )
    op.create_index(
        "ix_affectation_rattachement",
        "affectation",
        ["tenant_id", "compte_id", "etablissement_id", "annee_id"],
        schema="habilitations",
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
        schema="habilitations",
    )
    op.create_index(
        "ix_evenement_file",
        "evenement_outbox",
        ["tenant_id", "etat", "ecrit_le", "id"],
        schema="habilitations",
    )

    for table in ("compte", "affectation", "evenement_outbox"):
        op.execute(f"ALTER TABLE habilitations.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE habilitations.{table} FORCE ROW LEVEL SECURITY")

    op.execute(
        f"CREATE POLICY isolation_tenant ON habilitations.compte FOR ALL "
        f"USING (tenant_id = {TENANT_COURANT}) WITH CHECK (tenant_id = {TENANT_COURANT})"
    )
    op.execute(
        f"CREATE POLICY isolation_tenant ON habilitations.affectation FOR ALL "
        f"USING (tenant_id = {TENANT_COURANT}) WITH CHECK (tenant_id = {TENANT_COURANT})"
    )
    op.execute(
        f"CREATE POLICY lecture_tenant ON habilitations.evenement_outbox FOR SELECT "
        f"USING (tenant_id = {TENANT_COURANT})"
    )
    op.execute(
        f"CREATE POLICY ecriture_tenant ON habilitations.evenement_outbox FOR INSERT "
        f"WITH CHECK (tenant_id = {TENANT_COURANT})"
    )
    op.execute(
        f"CREATE POLICY marquage_tenant ON habilitations.evenement_outbox FOR UPDATE "
        f"USING (tenant_id = {TENANT_COURANT}) WITH CHECK (tenant_id = {TENANT_COURANT})"
    )

    op.execute("GRANT USAGE ON SCHEMA habilitations TO nelo_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON habilitations.compte, habilitations.affectation, "
        "habilitations.evenement_outbox TO nelo_app"
    )

    # Les trois fonctions qui répondent avant tout tenant. Elles ne rendent que des identifiants
    # et un statut : ni nom, ni numéro, ni empreinte.
    op.execute(
        """
        CREATE FUNCTION habilitations.comptes_par_identifiant(p_identifiant text)
        RETURNS TABLE (id uuid, tenant_id uuid, personne_id uuid, statut text)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
        AS $$ SELECT c.id, c.tenant_id, c.personne_id, c.statut FROM habilitations.compte c
              WHERE c.identifiant = p_identifiant ORDER BY c.cree_le, c.id $$
        """
    )
    op.execute(
        """
        CREATE FUNCTION habilitations.compte_par_invitation(p_empreinte text)
        RETURNS TABLE (id uuid, tenant_id uuid, statut text, invitation_expire_le timestamptz)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
        AS $$ SELECT c.id, c.tenant_id, c.statut, c.invitation_expire_le
              FROM habilitations.compte c WHERE c.invitation_empreinte = p_empreinte $$
        """
    )
    op.execute(
        """
        CREATE FUNCTION habilitations.compte_par_id_sans_tenant(p_compte uuid)
        RETURNS TABLE (id uuid, tenant_id uuid, statut text)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
        AS $$ SELECT c.id, c.tenant_id, c.statut FROM habilitations.compte c WHERE c.id = p_compte $$
        """
    )
    for signature in (
        "habilitations.comptes_par_identifiant(text)",
        "habilitations.compte_par_invitation(text)",
        "habilitations.compte_par_id_sans_tenant(uuid)",
    ):
        op.execute(f"REVOKE ALL ON FUNCTION {signature} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {signature} TO nelo_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION habilitations.compte_par_id_sans_tenant(uuid)")
    op.execute("DROP FUNCTION habilitations.compte_par_invitation(text)")
    op.execute("DROP FUNCTION habilitations.comptes_par_identifiant(text)")
    op.drop_table("evenement_outbox", schema="habilitations")
    op.drop_table("affectation", schema="habilitations")
    op.drop_table("compte", schema="habilitations")
    op.execute("REVOKE USAGE ON SCHEMA habilitations FROM nelo_app")
