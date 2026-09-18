"""La fonction qui cherchait un compte sans son tenant n'a jamais eu d'appelant.

Révision : 0002
Précédente : 0001

`habilitations.compte_par_id_sans_tenant` devait servir à `/auth/pin` : retrouver le tenant d'un
compte quand on ne connaît que son identifiant. L'implémentation n'en a pas eu besoin, parce que
le **secret d'appareil** porte déjà le tenant : c'est lui qui prouve la possession, et lui qu'on
lit avant tout le reste (research.md R-13).

Une fonction `SECURITY DEFINER` traverse la politique de sécurité au niveau ligne. En garder une
qu'aucun code n'appelle, c'est laisser ouverte une porte dont personne ne se sert : la porte P-12
l'a signalée, et la voici retirée. Le `downgrade` la recrée telle qu'elle était.
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

DEFINITION = """
CREATE FUNCTION habilitations.compte_par_id_sans_tenant(p_compte uuid)
RETURNS TABLE (id uuid, tenant_id uuid, statut text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp
AS $$ SELECT c.id, c.tenant_id, c.statut FROM habilitations.compte c WHERE c.id = p_compte $$
"""


def upgrade() -> None:
    op.execute("DROP FUNCTION habilitations.compte_par_id_sans_tenant(uuid)")


def downgrade() -> None:
    op.execute(DEFINITION)
    op.execute("REVOKE ALL ON FUNCTION habilitations.compte_par_id_sans_tenant(uuid) FROM PUBLIC")
    op.execute(
        "GRANT EXECUTE ON FUNCTION habilitations.compte_par_id_sans_tenant(uuid) TO nelo_app"
    )
