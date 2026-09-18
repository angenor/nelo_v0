"""Le tenant provisoire disparaît : sa fonction de résolution n'a plus d'appelant.

Révision : 0003
Précédente : 0002

`tenants.tenant_de_etablissement` répondait « de quel tenant relève cet établissement ? » avant
qu'aucun compte ne soit connu (T0a). Les middlewares de session et d'établissement répondent
désormais autrement, et mieux : le tenant vient du **compte de la session**, et l'établissement
n'est accepté que s'il lui est rattaché. Une fonction `SECURITY DEFINER` de moins est une surface
d'attaque de moins ; le test qui les énumère ne l'attend plus.

Le `downgrade` la recrée telle qu'elle était, avec ses droits.
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

DEFINITION = """
CREATE FUNCTION tenants.tenant_de_etablissement(p_etablissement uuid) RETURNS uuid
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
AS $$ SELECT tenant_id FROM tenants.etablissement WHERE id = p_etablissement $$
"""


def upgrade() -> None:
    op.execute("DROP FUNCTION tenants.tenant_de_etablissement(uuid)")


def downgrade() -> None:
    op.execute(DEFINITION)
    op.execute("REVOKE ALL ON FUNCTION tenants.tenant_de_etablissement(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION tenants.tenant_de_etablissement(uuid) TO nelo_app")
