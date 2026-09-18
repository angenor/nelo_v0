"""FR-001 : deux écritures du même numéro donnent le même identifiant, ou rien.

Le test tourne avec l'indicatif du déploiement passé en paramètre : aucun pays n'est nommé dans le
code qu'il exerce, et l'indicatif fictif du second pack prouve que rien n'est figé.
"""

import pytest

from modules.shared import ErreurMetier
from modules.socle.habilitations.normalisation import normaliser

INDICATIF = "225"


@pytest.mark.parametrize(
    "brut",
    ["07 08 12 34 56", "+225 07 08 12 34 56", "+2250708123456", "0708123456", "07-08-12-34-56"],
)
def test_les_ecritures_d_un_meme_numero_donnent_le_meme_identifiant(brut):
    assert normaliser(brut, INDICATIF) == "+2250708123456"


def test_un_numero_etranger_garde_son_indicatif():
    assert normaliser("+33612345678", INDICATIF) == "+33612345678"


@pytest.mark.parametrize("brut", ["12", "0708", "", "pas un numéro", "+999123456"])
def test_un_numero_invalide_est_refuse(brut):
    with pytest.raises(ErreurMetier) as refus:
        normaliser(brut, INDICATIF)
    assert refus.value.code == "AUT_NUMERO_INVALIDE"
    assert refus.value.statut == 422
    assert refus.value.champ == "identifiant"


def test_l_indicatif_du_deploiement_decide_de_la_lecture():
    """Le même numéro local, lu sous deux indicatifs, ne donne pas le même identifiant."""
    assert normaliser("0612345678", "33") == "+33612345678"
    with pytest.raises(ErreurMetier):
        normaliser("0612345678", INDICATIF)


def test_un_indicatif_de_deploiement_absurde_est_une_erreur_de_deploiement():
    """Pas un refus adressé à la personne : une configuration fausse arrête le serveur."""
    with pytest.raises(RuntimeError, match="NELO_INDICATIF_DEFAUT"):
        normaliser("0708123456", "pas-un-indicatif")
