"""Le pack de pays a sa table, l'établissement son administrateur, le catalogue trois clés.

Révision : 0002
Précédente : 0001

Trois ajouts que T1a demande au module doré :

- `etablissement.administrateur_compte_id` : qui attribue ses domaines à une personne sans
  capacité. L'écran « aucun domaine » le nomme (docs/02-domaine.md § 1.2) ;
- `country_pack` : la provision nommée par T0a prend corps. Deux packs sont semés, dont un
  fictif dont aucune valeur ne coïncide avec l'autre : c'est le test d'agnosticité ;
- trois clés de sécurité au catalogue, réglables par établissement là où le produit l'admet.

Le retrait de `tenants.tenant_de_etablissement` n'est **pas** ici : la fonction sert encore au
tenant provisoire de T0a jusqu'à ce que les middlewares de session la remplacent (migration 0003).
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP

from modules.socle.tenants.catalogue_seed import entrees_de
from modules.socle.tenants.packs_seed import PACKS

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

CLES_NEUVES = (
    "securite.pin_tentatives_max",
    "securite.appareil_connu_jours",
    "securite.invitation_validite_jours",
)


def upgrade() -> None:
    # Identifiant vers `habilitations.compte`, sans clé étrangère : aucune ne traverse un schéma.
    op.add_column(
        "etablissement",
        sa.Column("administrateur_compte_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        schema="tenants",
    )

    pack = op.create_table(
        "country_pack",
        sa.Column("pays_code", sa.Text, primary_key=True),
        sa.Column("version", sa.Integer, primary_key=True),
        sa.Column("contenu", JSONB, nullable=False),
        sa.Column(
            "publie_le", TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        schema="tenants",
    )
    op.execute("ALTER TABLE tenants.country_pack ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants.country_pack FORCE ROW LEVEL SECURITY")
    # Un pack n'appartient à aucun tenant : comme le catalogue, il se lit depuis toute
    # transaction tenantée, et de nulle part ailleurs.
    op.execute(
        "CREATE POLICY lecture_tenantee ON tenants.country_pack FOR SELECT "
        "USING (NULLIF(current_setting('app.current_tenant', true), '') IS NOT NULL)"
    )
    op.execute("GRANT SELECT ON tenants.country_pack TO nelo_app")
    op.bulk_insert(pack, [dict(entree) for entree in PACKS])

    catalogue = sa.table(
        "parametre_catalogue",
        sa.column("cle", sa.Text),
        sa.column("portee_la_plus_basse", sa.Text),
        sa.column("type", sa.Text),
        sa.column("valeur_defaut", JSONB(none_as_null=True)),
        sa.column("origine_defaut", sa.Text),
        sa.column("description_cle", sa.Text),
        schema="tenants",
    )
    op.bulk_insert(catalogue, list(entrees_de("0002")))


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM tenants.parametre_catalogue WHERE cle = ANY(:cles)").bindparams(
            sa.bindparam("cles", value=list(CLES_NEUVES))
        )
    )
    op.drop_table("country_pack", schema="tenants")
    op.drop_column("etablissement", "administrateur_compte_id", schema="tenants")
