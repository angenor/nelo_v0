"""US4 : une seule requête au démarrage, et l'interface sait exactement ce qui existe.

Le contexte est la **seule** source de ce que l'écran a le droit de rendre : une action absente du
contexte est absente de l'écran, jamais grisée. Cette suite garde quatre choses.

La **forme** d'abord : exactement celle du contrat, sans un champ de plus ni de moins, parce que
le client en dérive son type et qu'un champ surnuméraire deviendrait une dépendance non écrite.
Le **périmètre** ensuite : les établissements sont ceux du compte, et d'aucun autre. La
**suppléance** : un écran qui dit « demandez à quelqu'un » sans dire à qui ne sert à rien, donc
l'administrateur n'est jamais absent, même quand personne n'est désigné. L'**agnosticité** enfin :
le tenant B tourne sur un pack fictif dont aucune valeur ne coïncide avec celle du pays du pilote,
et son contexte doit le refléter ligne pour ligne. Une devise écrite dans le code tomberait ici.
"""

import json
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import update

from modules.shared import transaction
from modules.shared.contexte import ContexteCapacites
from modules.socle import annees, habilitations, personnes, tenants
from modules.socle.tenants.packs_seed import COTE_D_IVOIRE, FICTIF
from modules.socle.tenants.tables import etablissement as table_etablissement
from tests.authentification.outils import en_tetes, semer_compte_neuf
from tests.module_dore.outils import poser

CHEMIN = "/api/v1/moi/capacites"


def charge_en_texte(charge: dict) -> str:
    return json.dumps(charge, ensure_ascii=False)


async def lire_contexte(client, session, etablissement_id) -> dict:
    reponse = await client.get(CHEMIN, headers=en_tetes(session, etablissement_id))
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


async def poser_telephone(tenant_id: UUID, etablissement_id: UUID, telephone: str) -> None:
    """Aucun service de T1a ne pose le téléphone d'une école ; le repli de FR-049 en vit."""
    async with transaction(tenant_id) as connexion:
        await connexion.execute(
            update(table_etablissement)
            .where(table_etablissement.c.id == etablissement_id)
            .values(telephone=telephone)
        )


async def rattacher_une_seconde_ecole(tenant, nom: str, telephone: str = "+2252000000009") -> UUID:
    """Une seconde école du même tenant, à laquelle le compte est rattaché pour l'année en cours.

    Elle porte toujours un téléphone : le contexte exige que l'administrateur soit joignable, et
    sans désignation c'est celui de l'école qui répond (FR-049).
    """
    etablissement_id = await tenants.creer_etablissement(tenant.tenant, nom, "Africa/Abidjan")
    annee_id = await annees.creer_annee(
        tenant.tenant,
        etablissement_id,
        "2026-2027",
        date.today() - timedelta(days=30),
        date.today() + timedelta(days=300),
        "active",
    )
    await habilitations.creer_affectation(
        tenant.tenant, tenant.compte, annee_id, etablissement_id, date.today(), None
    )
    await poser_telephone(tenant.tenant, etablissement_id, telephone)
    return etablissement_id


# --- La forme, et rien qu'elle ------------------------------------------------------------------


async def test_le_contexte_a_exactement_la_forme_du_contrat(client, sessions_ab, tenants_ab):
    charge = await lire_contexte(client, sessions_ab.a, tenants_ab.etab_a)

    # `ContexteCapacites` interdit les champs surnuméraires : la validation dit les deux sens.
    contexte = ContexteCapacites.model_validate(charge)
    assert set(charge) == set(ContexteCapacites.model_fields)
    assert contexte.etablissement_actif == tenants_ab.etab_a


async def test_rien_de_ce_que_t1b_livrera_n_est_invente_ici(client, sessions_ab, tenants_ab):
    """Capacités, accès nominatifs et alertes sont vides, et c'est ce que la coquille attend."""
    charge = await lire_contexte(client, sessions_ab.a, tenants_ab.etab_a)

    assert charge["capacites"] == []
    assert charge["acces_nominatifs"] == []
    assert charge["alertes"] == []
    assert charge["etablissements"][0]["sites"] == []
    assert charge["etablissements"][0]["cycles_actifs"] == []
    assert charge["etablissements"][0]["modules_actifs"] == []


async def test_la_langue_du_compte_est_celle_de_la_personne(client, sessions_ab, tenants_ab):
    """L'interface se rend dans la langue du compte, pas dans celle du navigateur (US4-7)."""
    charge_a = await lire_contexte(client, sessions_ab.a, tenants_ab.etab_a)
    charge_b = await lire_contexte(client, sessions_ab.b, tenants_ab.etab_b)

    assert charge_a["compte"]["langue"] == "fr"
    assert charge_b["compte"]["langue"] == "en"
    assert charge_a["compte"]["id"] == str(tenants_ab.compte_a)
    assert charge_a["compte"]["nom"] and charge_a["compte"]["prenoms"]


# --- Le périmètre : ce qui est à ce compte, et rien d'autre --------------------------------------


async def test_les_etablissements_sont_ceux_du_compte_et_d_aucun_autre(
    client, sessions_ab, tenants_ab
):
    non_rattachee = await tenants.creer_etablissement(
        tenants_ab.tenant_a, "École A2", "Africa/Abidjan"
    )

    charge = await lire_contexte(client, sessions_ab.a, tenants_ab.etab_a)

    vus = {e["id"] for e in charge["etablissements"]}
    assert vus == {str(tenants_ab.etab_a)}
    assert str(non_rattachee) not in vus
    assert str(tenants_ab.etab_b) not in vus


async def test_l_etablissement_actif_est_celui_de_l_en_tete(client, sessions_ab, tenants_ab):
    """Rattaché à deux écoles, la personne choisit : le serveur ne se replie sur aucune (FR-051)."""
    seconde = await rattacher_une_seconde_ecole(tenants_ab.a, "École A bis")

    charge = await lire_contexte(client, sessions_ab.a, seconde)

    assert charge["etablissement_actif"] == str(seconde)
    assert {e["id"] for e in charge["etablissements"]} == {
        str(tenants_ab.etab_a),
        str(seconde),
    }


async def test_les_annees_sont_celles_de_l_etablissement_actif_avec_leur_etat(
    client, sessions_ab, tenants_ab
):
    charge = await lire_contexte(client, sessions_ab.a, tenants_ab.etab_a)

    par_id = {a["id"]: a for a in charge["annees"]}
    assert set(par_id) == {str(tenants_ab.annee_a), str(tenants_ab.annee_prep_a)}
    assert par_id[str(tenants_ab.annee_a)]["etat"] == "ACTIVE"
    assert par_id[str(tenants_ab.annee_a)]["libelle"] == "2026-2027"
    assert par_id[str(tenants_ab.annee_prep_a)]["etat"] == "PREPARATION"
    assert charge["annee_active"] == str(tenants_ab.annee_a)


async def test_les_annees_d_une_autre_ecole_n_entrent_pas_dans_le_contexte(
    client, sessions_ab, tenants_ab
):
    seconde = await rattacher_une_seconde_ecole(tenants_ab.a, "École A ter")

    charge = await lire_contexte(client, sessions_ab.a, seconde)

    assert str(tenants_ab.annee_a) not in {a["id"] for a in charge["annees"]}
    assert len(charge["annees"]) == 1


# --- L'administrateur : jamais un champ absent ---------------------------------------------------


async def test_l_administrateur_designe_est_nomme_avec_son_telephone(
    client, sessions_ab, tenants_ab
):
    charge = await lire_contexte(client, sessions_ab.a, tenants_ab.etab_a)

    administrateur = charge["etablissements"][0]["administrateur"]
    assert administrateur["prenoms"]
    assert administrateur["telephone"] == tenants_ab.numero_a


async def test_sans_designation_c_est_l_ecole_qu_on_appelle(client, sessions_ab, tenants_ab):
    """FR-049 : une institution n'a pas de prénoms, et le champ n'est jamais absent."""
    seconde = await rattacher_une_seconde_ecole(tenants_ab.a, "École sans chef", "+2252000000001")

    charge = await lire_contexte(client, sessions_ab.a, seconde)

    administrateur = next(
        e["administrateur"] for e in charge["etablissements"] if e["id"] == str(seconde)
    )
    assert administrateur["nom"] == "École sans chef"
    assert administrateur["prenoms"] == ""
    assert administrateur["telephone"] == "+2252000000001"


async def test_un_administrateur_suspendu_ne_nomme_plus_personne(
    client, application, sessions_ab, tenants_ab
):
    """L'écran « aucun domaine » ne renvoie jamais vers quelqu'un qui n'a plus accès."""
    await poser_telephone(tenants_ab.tenant_a, tenants_ab.etab_a, "+2252000000002")
    _, remplacant = await semer_compte_neuf(tenants_ab.a)
    await tenants.designer_administrateur(tenants_ab.tenant_a, tenants_ab.etab_a, remplacant)
    await habilitations.suspendre(
        tenants_ab.tenant_a,
        remplacant,
        tenants_ab.compte_a,
        valkey=application.state.valkey,
    )

    charge = await lire_contexte(client, sessions_ab.a, tenants_ab.etab_a)

    administrateur = charge["etablissements"][0]["administrateur"]
    assert administrateur["nom"] == "École A"
    assert administrateur["prenoms"] == ""
    assert administrateur["telephone"] == "+2252000000002"


# --- Le pays est une donnée, jamais une littérale ------------------------------------------------


async def test_le_pack_du_tenant_fictif_ne_doit_rien_au_pays_du_pilote(
    client, sessions_ab, tenants_ab
):
    """Une seule valeur du pilote écrite dans le code apparaîtrait ici, et le test tomberait."""
    charge = await lire_contexte(client, sessions_ab.b, tenants_ab.etab_b)

    pack = charge["country_pack"]
    attendu = FICTIF["contenu"]
    assert pack["pays"] == "ZZ"
    assert pack["version"] == FICTIF["version"]
    assert pack["devise"] == attendu["devise"]
    assert pack["langues"] == attendu["langues"]
    assert pack["decoupage"] == attendu["decoupage"]
    assert pack["vocabulaire"] == attendu["vocabulaire"]
    # Aucune valeur du pays du pilote ne s'est glissée dans la réponse du tenant fictif.
    assert COTE_D_IVOIRE["contenu"]["devise"]["code"] not in charge_en_texte(charge)
    assert COTE_D_IVOIRE["contenu"]["decoupage"] not in charge_en_texte(charge)


async def test_le_pack_du_pays_du_pilote_est_celui_qui_est_seme(client, sessions_ab, tenants_ab):
    charge = await lire_contexte(client, sessions_ab.a, tenants_ab.etab_a)

    pack = charge["country_pack"]
    assert pack["pays"] == "CI"
    assert pack["devise"] == COTE_D_IVOIRE["contenu"]["devise"]
    assert pack["vocabulaire"] == COTE_D_IVOIRE["contenu"]["vocabulaire"]


# --- Les paramètres effectifs : une clé, une valeur ----------------------------------------------


async def test_les_parametres_effectifs_sont_une_valeur_par_cle(client, sessions_ab, tenants_ab):
    charge = await lire_contexte(client, sessions_ab.a, tenants_ab.etab_a)

    parametres = charge["parametres_effectifs"]
    assert isinstance(parametres, dict)
    assert parametres["securite.duree_session_minutes"] == 480
    assert all(isinstance(cle, str) for cle in parametres)
    # Une projection, pas la forme complète de `GET /parametres` : ni source, ni portée résolue.
    assert not any(
        isinstance(valeur, dict) and "source" in valeur for valeur in parametres.values()
    )


async def test_une_valeur_posee_se_lit_dans_le_contexte(client, sessions_ab, tenants_ab):
    reponse = await poser(
        client,
        sessions_ab.a,
        tenants_ab.etab_a,
        "absence.delai_notification_minutes",
        "ETABLISSEMENT",
        tenants_ab.etab_a,
        42,
    )
    assert reponse.status_code == 200, reponse.text

    charge = await lire_contexte(client, sessions_ab.a, tenants_ab.etab_a)

    assert charge["parametres_effectifs"]["absence.delai_notification_minutes"] == 42


async def test_l_identite_du_compte_vient_du_module_des_personnes(client, sessions_ab, tenants_ab):
    identite = await personnes.lire_identite(tenants_ab.tenant_a, tenants_ab.personne_a)

    charge = await lire_contexte(client, sessions_ab.a, tenants_ab.etab_a)

    assert charge["compte"]["nom"] == identite.nom
    assert charge["compte"]["prenoms"] == identite.prenoms


async def test_un_etablissement_sans_administrateur_ni_telephone_ne_fait_pas_tomber_le_contexte(
    client, sessions_ab, tenants_ab
):
    """Un écran privé de numéro reste un écran ; un `500` ferme la porte à tout le monde.

    `creer_etablissement` ne pose aucun téléphone, et personne n'est désigné tant que le
    secrétariat ne l'a pas fait : le cas est atteignable dès le premier jour d'un établissement.
    Le contexte nomme alors l'école, sans numéro, plutôt que de refuser de se charger.
    """
    from datetime import date

    from modules.socle import annees, habilitations
    from modules.socle import tenants as module_tenants
    from tests.authentification.outils import en_tetes

    nu = await module_tenants.creer_etablissement(
        tenants_ab.tenant_a, "École nue", "Africa/Abidjan"
    )
    annee = await annees.creer_annee(
        tenants_ab.tenant_a, nu, "2026-2027", date(2026, 9, 1), date(2027, 7, 31), "active"
    )
    await habilitations.creer_affectation(
        tenants_ab.tenant_a, tenants_ab.compte_a, annee, nu, date.today(), None
    )

    reponse = await client.get("/api/v1/moi/capacites", headers=en_tetes(sessions_ab.a, nu))

    assert reponse.status_code == 200, reponse.text
    administrateur = next(
        e["administrateur"] for e in reponse.json()["etablissements"] if e["id"] == str(nu)
    )
    assert administrateur["nom"] == "École nue"
    assert administrateur["prenoms"] == ""
    assert administrateur["telephone"] == ""
