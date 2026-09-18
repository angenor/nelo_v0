"""SC-007 : le contrat généré porte ce que les contrats attendus déclarent.

Un fichier par tranche livrée, lus l'un après l'autre : ce que T0a a promis reste vrai quand T1a
ajoute ses routes. Le contrat attendu dit les chemins, les méthodes, les codes de réponse et les
en-têtes requis ; la génération dit le reste.
"""

import json
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parents[2]
CONTRATS_ATTENDUS = [
    "specs/001-socle-serveur/contracts/openapi-attendu.yaml",
    "specs/003-connexion-contexte/contracts/openapi-attendu.yaml",
]
ATTENDUS = [yaml.safe_load((RACINE / chemin).read_text()) for chemin in CONTRATS_ATTENDUS]
# Le premier reste nommé : les assertions de T0a le désignent directement.
ATTENDU = ATTENDUS[0]
GENERE = json.loads((RACINE / "contrat/openapi.json").read_text())

# Les routes que la tranche en cours doit encore livrer. Une story qui livre la sienne la retire
# de cette liste ; **elle doit être vide quand la tranche se termine**, et un test le dit. Elle
# n'est pas une permission de ne pas livrer : elle rend l'attente visible au lieu de laisser la
# porte rouge sans qu'on sache pourquoi.
ROUTES_A_VENIR: set[str] = set()


def paires():
    """Chaque (document attendu, chemin, méthode, opération), pour un cas de test par route."""
    for document in ATTENDUS:
        for chemin, methodes in document["paths"].items():
            for methode, operation in methodes.items():
                yield pytest.param(document, chemin, methode, operation, id=f"{methode} {chemin}")


def resoudre(document: dict, objet: dict) -> dict:
    while "$ref" in objet:
        chemin = objet["$ref"].removeprefix("#/").split("/")
        objet = document
        for morceau in chemin:
            objet = objet[morceau]
    return objet


def _attendre_la_story(chemin: str) -> None:
    if chemin in ROUTES_A_VENIR and chemin not in GENERE["paths"]:
        pytest.skip(f"{chemin} : livrée par une story suivante de la tranche")


@pytest.mark.parametrize(("document", "chemin", "methode", "operation"), list(paires()))
def test_chemins_methodes_et_codes(document, chemin, methode, operation):
    _attendre_la_story(chemin)
    assert chemin in GENERE["paths"], chemin
    genere = GENERE["paths"][chemin].get(methode)
    assert genere is not None, f"{methode.upper()} {chemin}"
    assert set(operation["responses"]) <= set(genere["responses"]), (
        f"{methode.upper()} {chemin} : {set(operation['responses']) - set(genere['responses'])}"
    )


@pytest.mark.parametrize(("document", "chemin", "methode", "operation"), list(paires()))
def test_en_tetes_requis(document, chemin, methode, operation):
    _attendre_la_story(chemin)
    attendus = {
        resoudre(document, p)["name"]
        for p in operation.get("parameters", [])
        if resoudre(document, p)["in"] == "header"
    }
    generes = {
        resoudre(GENERE, p)["name"]: resoudre(GENERE, p)
        for p in GENERE["paths"][chemin][methode].get("parameters", [])
        if resoudre(GENERE, p)["in"] == "header"
    }
    for nom in attendus:
        assert nom in generes, f"{methode.upper()} {chemin} : {nom}"
        assert generes[nom]["required"] is True, nom


def test_la_sonde_ne_demande_aucun_en_tete():
    assert not [
        p for p in GENERE["paths"]["/sante"]["get"].get("parameters", []) if p["in"] == "header"
    ]


def test_les_schemas_des_routes_livrees_sont_publies():
    """Chaque schéma référencé par une route livrée existe, sous ce nom, dans la génération."""
    publies = GENERE["components"]["schemas"]
    references = set()
    for document in ATTENDUS:
        for chemin, methodes in document["paths"].items():
            if chemin not in GENERE["paths"]:
                continue
            references |= _schemas_references(json.dumps(methodes))
    assert references, "aucun schéma référencé : le parcours ne prouverait rien"
    for nom in sorted(references):
        assert nom in publies, nom


def _schemas_references(texte: str) -> set[str]:
    import re

    return set(re.findall(r"#/components/schemas/(\w+)", texte))


def test_la_liste_d_attente_ne_retient_aucune_route_deja_livree():
    """Une route livrée doit sortir de la liste, sinon elle cesserait d'être vérifiée."""
    livrees = [chemin for chemin in ROUTES_A_VENIR if chemin in GENERE["paths"]]
    assert not livrees, f"à retirer de ROUTES_A_VENIR : {sorted(livrees)}"


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
