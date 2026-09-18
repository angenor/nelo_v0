"""US2-7 : le tenant d'une transaction vient du compte de la session, jamais d'un en-tête.

T0a résolvait le tenant depuis `X-Nelo-Etablissement` : le client choisissait donc lui-même son
périmètre, et c'était un provisoire assumé. Depuis T1a, la seule source est le jeton ; l'en-tête
n'est plus qu'une **question**, vérifiée contre les rattachements du compte.

Cette suite ne se contente pas de lire les réponses : elle écoute ce que les transactions posent
réellement dans `app.current_tenant` pendant la requête, parce que c'est cette valeur, et rien
d'autre, que la politique de sécurité au niveau ligne lit. Une session de A qui présente
l'établissement de B ne doit jamais faire naître une transaction de B, pas même une lecture.
"""

import contextlib
import importlib.util
import re
from pathlib import Path
from uuid import UUID

from sqlalchemy import event

from modules.shared import bd
from tests.authentification.outils import en_tetes
from tests.module_dore.outils import poser

CHEMIN = "/api/v1/parametres"
RACINE = Path(__file__).resolve().parents[2]
MOTIF_UUID = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


@contextlib.contextmanager
def tenants_poses():
    """Les tenants réellement posés dans `app.current_tenant` pendant le bloc.

    On écoute le moteur et non `transaction()` : un code qui aurait gardé une autre façon d'ouvrir
    une transaction serait vu tout de même, et c'est bien ce qu'on veut savoir.
    """
    vus: list[UUID] = []

    def ecouteur(connexion, curseur, instruction, parametres, contexte, plusieurs):
        if "app.current_tenant" not in instruction:
            return
        vus.extend(UUID(trouve) for trouve in MOTIF_UUID.findall(str(parametres)))

    moteur = bd.moteur().sync_engine
    event.listen(moteur, "before_cursor_execute", ecouteur)
    try:
        yield vus
    finally:
        event.remove(moteur, "before_cursor_execute", ecouteur)


async def test_la_transaction_porte_le_tenant_du_jeton_et_lui_seul(client, sessions_ab, tenants_ab):
    with tenants_poses() as vus:
        reponse = await client.get(CHEMIN, headers=en_tetes(sessions_ab.a, tenants_ab.etab_a))

    assert reponse.status_code == 200, reponse.text
    assert vus, "aucune transaction tenantée n'a été ouverte : l'écoute ne prouve rien"
    assert set(vus) == {tenants_ab.tenant_a}


async def test_l_etablissement_d_un_autre_tenant_n_ouvre_jamais_sa_transaction(
    client, sessions_ab, tenants_ab
):
    """Le refus tombe **avant** toute lecture : le tenant de B n'est jamais posé."""
    with tenants_poses() as vus:
        reponse = await client.get(CHEMIN, headers=en_tetes(sessions_ab.a, tenants_ab.etab_b))

    assert reponse.status_code == 403
    assert reponse.json()["code"] == "TEN_ETABLISSEMENT_NON_AUTORISE"
    assert tenants_ab.tenant_b not in vus
    assert set(vus) <= {tenants_ab.tenant_a}


async def test_une_session_de_a_avec_l_en_tete_de_b_ne_voit_rien_de_b(
    client, sessions_ab, tenants_ab
):
    """B pose une valeur bien à lui ; A la demande en désignant l'école de B, et n'obtient rien."""
    pose = await poser(
        client,
        sessions_ab.b,
        tenants_ab.etab_b,
        "absence.delai_notification_minutes",
        "ETABLISSEMENT",
        tenants_ab.etab_b,
        77,
    )
    assert pose.status_code == 200, pose.text

    reponse = await client.get(CHEMIN, headers=en_tetes(sessions_ab.a, tenants_ab.etab_b))

    assert reponse.status_code == 403
    assert "77" not in reponse.text
    assert str(tenants_ab.tenant_b) not in reponse.text


def test_le_resolveur_provisoire_de_t0a_n_existe_plus():
    """Le test qui prouvait le provisoire est remplacé par celui-ci (FR-041).

    Tant que le module existe, quelqu'un peut le rebrancher : c'est son absence qui fait foi, pas
    le fait que la chaîne de middlewares ne l'inclue plus aujourd'hui.
    """
    assert importlib.util.find_spec("api.tenant_provisoire") is None
    assert not (RACINE / "api" / "tenant_provisoire.py").exists()
