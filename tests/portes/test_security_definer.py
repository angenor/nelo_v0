"""R-07 : les fonctions SECURITY DEFINER sont exactement celles nommées, et pas une de plus.

Chacune répond **avant que le tenant ne soit connu** : un établissement, un numéro, un lien ou
un appareil ne disent pas de quel tenant ils relèvent. Elles ne rendent que des identifiants et
un statut : ni nom, ni numéro, ni empreinte. `tenant_de_etablissement`, celle du tenant
provisoire de T0a, a été retirée avec lui par la migration `tenants` 0003, et
`compte_par_id_sans_tenant` par la migration `habilitations` 0002 : elle n'a jamais eu
d'appelant, et une fonction qui traverse la RLS sans servir est une porte ouverte pour rien.
"""

from sqlalchemy import text

from modules.shared import transaction

ATTENDUES = {
    "tenants_pour_travailleur",
    "comptes_par_identifiant",
    "compte_par_invitation",
}


async def test_les_fonctions_nommees_et_pas_une_de_plus(tenants_ab):
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


async def test_elles_ne_rendent_que_des_identifiants(tenants_ab):
    from modules.shared.bd import sans_tenant
    from modules.socle import tenants
    from modules.socle.habilitations import acces

    parcourus = await tenants.tenants_pour_travailleur()
    assert {tenants_ab.tenant_a, tenants_ab.tenant_b} <= set(parcourus)

    async with sans_tenant() as connexion:
        comptes = await acces.appeler_comptes_par_identifiant(connexion, tenants_ab.numero_a)
    assert [c["id"] for c in comptes] == [tenants_ab.compte_a]
    # Un identifiant, un tenant, une personne, un statut, et rien d'autre : ni nom, ni numéro.
    assert set(comptes[0]) == {"id", "tenant_id", "personne_id", "statut"}
