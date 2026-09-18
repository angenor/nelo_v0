"""FR-009, ADR 013 : un message court tient dans un message court, et le prouve au dépôt.

La vérification se fait ici, une fois pour toutes, avec les **valeurs les plus longues** que le
produit admet. La vérifier à l'envoi serait la faire trop tard : la personne aurait déjà reçu un
texte coupé en deux, facturé deux fois, et parfois recomposé à l'envers par la passerelle.

Les valeurs les plus longues :

- `produit` : trente caractères, le plafond que le déploiement s'impose ;
- `etablissement` : quarante caractères, un nom d'école long et sans abréviation ;
- `lien` : soixante caractères, l'origine publique suivie du jeton d'activation ;
- `nouveau` : seize caractères, un E.164 au plus long ;
- `code` : la longueur de la politique ; `minutes` et `jours` : deux chiffres.
"""

import json
from pathlib import Path

import pytest

from modules.socle.habilitations.gabarits import DOSSIER, LONGUEUR_MAXIMALE, langues, rendre
from modules.socle.habilitations.politique import POLITIQUE

PRODUIT = "N" * 30
ETABLISSEMENT = "É" * 40
LIEN = "https://" + "l" * 52
NOUVEAU = "+" + "9" * 15

VALEURS = {
    "produit": PRODUIT,
    "etablissement": ETABLISSEMENT,
    "lien": LIEN,
    "nouveau": NOUVEAU,
    "code": "9" * POLITIQUE.OTP_LONGUEUR,
    "minutes": 99,
    "jours": 99,
}

CLES = ("otp", "invitation", "changement_ancien_numero")

# Les abréviations qu'un texte tronqué appelle, et que le produit refuse : un message court se
# raccourcit en écrivant moins, jamais en écrivant mal.
ABREVIATIONS = ("svp", "rdv", "ets", "etab.", "qqn", "pr ", "ds ", "vs ", "ns ", "tel.", "cf.")


@pytest.mark.parametrize("langue", ["fr", "en"])
@pytest.mark.parametrize("cle", CLES)
def test_chaque_gabarit_tient_sous_cent_soixante_caracteres(cle, langue):
    texte = rendre(cle, langue, **VALEURS)
    assert len(texte) <= LONGUEUR_MAXIMALE, f"{cle}/{langue} : {len(texte)} caractères\n{texte}"


@pytest.mark.parametrize("langue", ["fr", "en"])
@pytest.mark.parametrize("cle", CLES)
def test_aucun_gabarit_n_abrege(cle, langue):
    texte = rendre(cle, langue, **VALEURS).lower()
    for abreviation in ABREVIATIONS:
        assert abreviation not in texte, f"{cle}/{langue} abrège : « {abreviation} »"


def test_les_deux_langues_portent_les_memes_cles():
    fichiers = {
        langue: json.loads((DOSSIER / f"{langue}.json").read_text(encoding="utf-8"))
        for langue in langues()
    }
    assert set(fichiers) == {"fr", "en"}
    assert set(fichiers["fr"]) == set(fichiers["en"]) == set(CLES)


def test_les_deux_langues_portent_les_memes_parametres():
    """Un paramètre oublié dans une langue est un `KeyError` au moment de l'envoi, jamais avant."""
    import re

    fichiers = {
        langue: json.loads((DOSSIER / f"{langue}.json").read_text(encoding="utf-8"))
        for langue in ("fr", "en")
    }
    for cle in CLES:
        params = {
            langue: set(re.findall(r"\{(\w+)\}", fichiers[langue][cle])) for langue in fichiers
        }
        assert params["fr"] == params["en"], f"{cle} : {params}"


def test_une_langue_inconnue_retombe_sur_le_francais():
    assert rendre("otp", "wo", **VALEURS) == rendre("otp", "fr", **VALEURS)


def test_un_gabarit_inconnu_est_une_erreur_de_programme():
    with pytest.raises(KeyError):
        rendre("inexistant", "fr", **VALEURS)


def test_aucun_gabarit_ne_porte_de_tiret_cadratin():
    for chemin in Path(DOSSIER).glob("*.json"):
        assert "—" not in chemin.read_text(encoding="utf-8"), chemin.name
