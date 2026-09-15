"""US1-7 — la sonde répond sans en-tête, et ne touche ni la base ni Valkey."""

from modules.shared import bd


class MoteurArrete:
    def begin(self):
        raise AssertionError("la sonde a touché la base")


async def test_sante_sans_en_tete_ni_base(client, monkeypatch):
    monkeypatch.setattr(bd, "_moteur", MoteurArrete())
    reponse = await client.get("/api/v1/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"etat": "OK"}
