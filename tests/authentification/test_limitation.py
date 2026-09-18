"""FR-007 : compter les usages dans une fenêtre, et savoir de quel client vient la requête."""

from datetime import timedelta

import pytest

from api.asgi import est_libre
from api.limitation import adresse_client, compter

FENETRE = timedelta(seconds=60)


async def test_sous_le_plafond_rien_n_est_refuse(valkey):
    for _ in range(3):
        assert await compter(valkey, "essai:debit", 3, FENETRE) is None


async def test_au_dela_du_plafond_la_reprise_est_annoncee(valkey):
    for _ in range(3):
        await compter(valkey, "essai:debit", 3, FENETRE)
    reprise = await compter(valkey, "essai:debit", 3, FENETRE)
    assert reprise is not None
    assert 0 < reprise <= 60


async def test_la_fenetre_part_du_premier_usage(valkey):
    """Sinon un client qui frappe sans arrêt repousserait sa propre fenêtre indéfiniment."""
    await compter(valkey, "essai:fenetre", 5, FENETRE)
    await valkey.expire("essai:fenetre", 10)
    await compter(valkey, "essai:fenetre", 5, FENETRE)
    assert int(await valkey.ttl("essai:fenetre")) <= 10


async def test_un_plafond_de_un_est_un_delai_avant_renvoi(valkey):
    assert await compter(valkey, "essai:renvoi", 1, FENETRE) is None
    assert await compter(valkey, "essai:renvoi", 1, FENETRE) is not None


async def test_deux_cles_ne_se_melangent_pas(valkey):
    assert await compter(valkey, "essai:a", 1, FENETRE) is None
    assert await compter(valkey, "essai:b", 1, FENETRE) is None


def _scope(client: str, en_tetes: dict[bytes, bytes] | None = None):
    return {
        "type": "http",
        "client": (client, 51234),
        "headers": [(nom, valeur) for nom, valeur in (en_tetes or {}).items()],
    }


def test_sans_relais_declare_l_adresse_est_celle_de_la_connexion():
    scope = _scope("203.0.113.7", {b"x-forwarded-for": b"198.51.100.9"})
    assert adresse_client(scope, None) == "203.0.113.7"


def test_l_en_tete_transmis_ne_vaut_que_depuis_le_relais_declare():
    en_tetes = {b"x-forwarded-for": b"198.51.100.9, 10.0.0.2"}
    assert adresse_client(_scope("127.0.0.1", en_tetes), "127.0.0.1") == "198.51.100.9"
    # La même requête, venue d'ailleurs : l'en-tête est ignoré. N'importe qui peut l'écrire.
    assert adresse_client(_scope("203.0.113.7", en_tetes), "127.0.0.1") == "203.0.113.7"


def test_un_relais_sans_en_tete_reste_le_client():
    assert adresse_client(_scope("127.0.0.1"), "127.0.0.1") == "127.0.0.1"


def test_une_connexion_sans_client_ne_fait_pas_tomber_la_limitation():
    assert adresse_client({"type": "http", "headers": []}, None) == "inconnu"


@pytest.mark.parametrize(
    ("chemin", "libre"),
    [
        ("/sante", True),
        ("/openapi.json", True),
        ("/auth/otp", True),
        ("/auth/otp/verification", True),
        ("/auth/pin", True),
        ("/auth/rafraichissement", True),
        ("/auth/invitation/abc", True),
        ("/auth/appareil", True),
        # Changer son code personnel exige d'être déjà connecté.
        ("/auth/pin/definition", False),
        ("/auth/session", False),
        ("/parametres", False),
        ("/moi/capacites", False),
    ],
)
def test_les_chemins_libres_sont_ceux_qui_ouvrent_une_session(chemin, libre):
    assert est_libre(chemin) is libre
