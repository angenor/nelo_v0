"""T0b — le type du contexte vient du contrat : le schéma est publié, le client en dérive le sien."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from modules.shared.contexte import ContexteCapacites

RACINE = Path(__file__).resolve().parents[2]
GENERE = json.loads((RACINE / "contrat/openapi.json").read_text())
CLIENT = (RACINE / "contrat/client.d.ts").read_text()
PERSONAS = sorted((RACINE / "web/app/core/demonstration/personas").glob("*.json"))
SOUS_MODELES = [
    "Compte",
    "EtablissementContexte",
    "Administrateur",
    "AnneeContexte",
    "CapaciteContexte",
    "AccesNominatif",
    "CountryPackContexte",
    "Devise",
    "AlerteContexte",
]


def test_le_contrat_publie_le_contexte_et_ses_sous_modeles():
    schemas = GENERE["components"]["schemas"]
    for nom in ["ContexteCapacites", *SOUS_MODELES]:
        assert nom in schemas, nom
    assert schemas["ContexteCapacites"]["additionalProperties"] is False
    assert "vocabulaire" in schemas["CountryPackContexte"]["properties"]
    assert "administrateur" in schemas["EtablissementContexte"]["required"]


def test_aucune_route_ne_le_sert_encore():
    assert not any("capacites" in chemin for chemin in GENERE["paths"])


def test_le_client_type_en_derive():
    assert "ContexteCapacites: {" in CLIENT
    assert 'administrateur: components["schemas"]["Administrateur"]' in CLIENT


def test_aucun_role_dans_le_schema():
    texte = json.dumps(GENERE["components"]["schemas"]["ContexteCapacites"])
    assert "role" not in texte.lower()


def _contexte() -> dict:
    return json.loads(PERSONAS[0].read_text()) if PERSONAS else {}


@pytest.mark.skipif(not PERSONAS, reason="les personas arrivent avec US3")
def test_les_personas_sont_des_contextes_valides():
    for chemin in PERSONAS:
        ContexteCapacites.model_validate_json(chemin.read_text())


@pytest.mark.skipif(not PERSONAS, reason="les personas arrivent avec US3")
@pytest.mark.parametrize(
    ("chemin", "valeur", "motif"),
    [
        (("capacites", 0, "code"), "vie_scolaire.appel", "pattern"),
        (("etablissement_actif",), "00000000-0000-7000-8000-000000000000", "etablissement_actif"),
        (("country_pack", "langues"), [], "at least 1"),
        (("role",), "DIRECTEUR", "Extra inputs"),
    ],
)
def test_le_schema_refuse(chemin, valeur, motif):
    contexte = json.loads(
        (RACINE / "web/app/core/demonstration/personas/sept-domaines.json").read_text()
    )
    cible = contexte
    for cle in chemin[:-1]:
        cible = cible[cle]
    cible[chemin[-1]] = valeur
    with pytest.raises(ValidationError, match=motif):
        ContexteCapacites.model_validate(contexte)
