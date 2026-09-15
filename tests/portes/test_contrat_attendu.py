"""SC-007 — le contrat généré porte ce que le contrat attendu déclare."""

import json
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parents[2]
ATTENDU = yaml.safe_load(
    (RACINE / "specs/001-socle-serveur/contracts/openapi-attendu.yaml").read_text()
)
GENERE = json.loads((RACINE / "contrat/openapi.json").read_text())


def resoudre(document: dict, objet: dict) -> dict:
    while "$ref" in objet:
        chemin = objet["$ref"].removeprefix("#/").split("/")
        objet = document
        for morceau in chemin:
            objet = objet[morceau]
    return objet


def test_chemins_methodes_et_codes():
    for chemin, methodes in ATTENDU["paths"].items():
        assert chemin in GENERE["paths"], chemin
        for methode, operation in methodes.items():
            genere = GENERE["paths"][chemin].get(methode)
            assert genere is not None, f"{methode.upper()} {chemin}"
            assert set(operation["responses"]) <= set(genere["responses"]), (
                f"{methode.upper()} {chemin} : {set(operation['responses']) - set(genere['responses'])}"
            )


def test_en_tetes_requis():
    for chemin, methodes in ATTENDU["paths"].items():
        for methode, operation in methodes.items():
            attendus = {
                resoudre(ATTENDU, p)["name"]
                for p in operation.get("parameters", [])
                if resoudre(ATTENDU, p)["in"] == "header"
            }
            generes = {
                resoudre(GENERE, p)["name"]: resoudre(GENERE, p)
                for p in GENERE["paths"][chemin][methode].get("parameters", [])
                if resoudre(GENERE, p)["in"] == "header"
            }
            for nom in attendus:
                assert nom in generes, f"{methode.upper()} {chemin} : {nom}"
                assert generes[nom]["required"] is True, nom
    assert not [
        p for p in GENERE["paths"]["/sante"]["get"].get("parameters", []) if p["in"] == "header"
    ]


def test_schemas_et_champs_requis():
    for nom in ("EnveloppeErreur", "ReponseParametres", "CorpsPoserParametre", "ParametrePose"):
        schema = GENERE["components"]["schemas"].get(nom)
        assert schema is not None, nom
        assert set(ATTENDU["components"]["schemas"][nom]["required"]) <= set(
            schema.get("required", [])
        ), nom
    assert "ReponseSante" in GENERE["components"]["schemas"]


def test_le_422_du_put_reference_l_enveloppe():
    reponse = GENERE["paths"]["/parametres/{cle}"]["put"]["responses"]["422"]
    schema = reponse["content"]["application/json"]["schema"]
    assert schema["$ref"] == "#/components/schemas/EnveloppeErreur"
