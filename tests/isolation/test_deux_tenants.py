"""US2-1, A ne voit jamais B : ni par l'API, ni sur aucune table d'aucun schéma du produit.

Depuis T1a, le produit porte quatre schémas et non plus un seul. Le parcours est le même pour
tous : on énumère les tables depuis le catalogue de PostgreSQL, et chacune doit ne montrer que le
tenant de la transaction courante. Une table neuve entre donc dans ce test le jour de sa migration,
sans qu'on ait à y penser (FR-045).
"""

from modules.shared import Evenement, outbox, transaction
from modules.socle.annees import tables as tables_annees
from modules.socle.personnes import tables as tables_personnes
from tests.isolation.schema import SCHEMAS, colonne, compter, tables_du_schema
from tests.module_dore.outils import lire, poser

CLE = "absence.delai_notification_minutes"
# Les tables sans `tenant_id`, semées par les migrations : le catalogue et les packs de pays.
REFERENTIELS = {("tenants", "parametre_catalogue"): 20, ("tenants", "country_pack"): 2}
# La table qui porte le tenant dans sa clé primaire : `tenants.tenant` **est** le tenant.
COLONNE_DE_TENANT = {("tenants", "tenant"): "id"}


async def test_a_ne_voit_aucune_valeur_de_b(client, sessions_ab, tenants_ab):
    reponse = await poser(
        client, sessions_ab.b, tenants_ab.etab_b, CLE, "ETABLISSEMENT", tenants_ab.etab_b, 99
    )
    assert reponse.status_code == 200, reponse.text
    reponse = await poser(
        client, sessions_ab.b, tenants_ab.etab_b, CLE, "TENANT", tenants_ab.tenant_b, 98
    )
    assert reponse.status_code == 200, reponse.text

    parametre = (await lire(client, sessions_ab.a, tenants_ab.etab_a))[CLE]
    assert (parametre["source"], parametre["portee_resolue"], parametre["valeur"]) == (
        "DEFAUT",
        None,
        15,
    )


async def test_une_ressource_de_b_est_introuvable_jamais_interdite(client, sessions_ab, tenants_ab):
    """La session et l'en-tête sont ceux de A : c'est la **portée visée** qui est hors périmètre.

    Le refus vient donc du service, et il est introuvable. Le cas où c'est l'en-tête lui-même qui
    désigne un établissement hors périmètre est le `403` nommé du principe XII, et il se mesure
    dans `tests/en_tetes/test_etablissement.py`.
    """
    reponse = await poser(
        client, sessions_ab.a, tenants_ab.etab_a, CLE, "ETABLISSEMENT", tenants_ab.etab_b, 1
    )
    assert reponse.status_code == 404
    assert reponse.json()["code"] == "TEN_RESSOURCE_INTROUVABLE"


async def _semer_les_outbox_sans_ecrivain(tenant_id) -> None:
    """Les deux outbox qu'aucune opération de T1a n'alimente encore.

    Elles existent, elles sont sous politique de sécurité au niveau ligne, et un zéro ne prouverait
    rien : une table vide passe n'importe quel test d'isolation. On y écrit donc une ligne par
    tenant, pour que « aucune ligne étrangère » soit une vraie absence et non un vide.
    """
    for module in (tables_personnes, tables_annees):
        async with transaction(tenant_id) as connexion:
            await outbox.inserer(
                connexion,
                module.evenement_outbox,
                tenant_id,
                Evenement("isolation.temoin", {"pourquoi": "une table vide ne prouve rien"}),
            )


async def test_chaque_table_de_chaque_schema_ne_montre_que_le_tenant_courant(
    client, sessions_ab, tenants_ab
):
    # Chaque tenant porte des lignes dans chaque table : un zéro ne peut pas être un vide.
    for session, etab, tenant_id in (
        (sessions_ab.a, tenants_ab.etab_a, tenants_ab.tenant_a),
        (sessions_ab.b, tenants_ab.etab_b, tenants_ab.tenant_b),
    ):
        reponse = await poser(client, session, etab, CLE, "ETABLISSEMENT", etab, 7)
        assert reponse.status_code == 200, reponse.text
        await _semer_les_outbox_sans_ecrivain(tenant_id)

    for tenant_id in (tenants_ab.tenant_a, tenants_ab.tenant_b):
        async with transaction(tenant_id) as connexion:
            for schema in SCHEMAS:
                for nom in await tables_du_schema(connexion, schema):
                    attendu = REFERENTIELS.get((schema, nom))
                    if attendu is not None:
                        # Référentiels communs : visibles dans toute transaction tenantée.
                        assert await connexion.scalar(compter(nom, schema=schema)) == attendu
                        continue
                    cle_tenant = colonne(COLONNE_DE_TENANT.get((schema, nom), "tenant_id"))
                    etrangeres = await connexion.scalar(
                        compter(nom, cle_tenant != tenant_id, schema=schema)
                    )
                    assert etrangeres == 0, f"{schema}.{nom} montre des lignes d'un autre tenant"
                    assert await connexion.scalar(compter(nom, schema=schema)) >= 1, (
                        f"{schema}.{nom} : rien à inspecter"
                    )
