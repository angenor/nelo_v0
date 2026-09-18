"""La normalisation du numéro de téléphone : une seule forme entre en base, E.164.

Tout ce que le module reçoit d'un client (demande de code, création de compte, changement de
numéro) passe par ici. `+2250708123456` et `07 08 12 34 56` sont le même compte : sans
normalisation, ils seraient deux identifiants, et le partage familial de US8 deviendrait
indétectable.

L'indicatif par défaut est une **donnée de déploiement** (`NELO_INDICATIF_DEFAUT`), pas une règle
du code : aucun pays n'est nommé ici (principe VII). Le format lui-même vient de `phonenumbers`
(research.md R-14), qui connaît les plans de numérotation mieux qu'une expression régulière.
"""

import phonenumbers

from modules.shared import ErreurMetier


def _refus() -> ErreurMetier:
    return ErreurMetier(
        "AUT_NUMERO_INVALIDE",
        "le numéro de téléphone n'est pas un numéro valide",
        statut=422,
        champ="identifiant",
    )


def normaliser(brut: str, indicatif_defaut: str) -> str:
    """Le numéro en E.164, ou `AUT_NUMERO_INVALIDE`.

    Un numéro écrit sans indicatif est lu dans le plan de numérotation du déploiement ; un numéro
    qui commence par `+` porte le sien, et peut donc venir de n'importe quel pays.
    """
    try:
        region = phonenumbers.region_code_for_country_code(int(indicatif_defaut))
    except (TypeError, ValueError) as erreur:
        raise RuntimeError(
            f"NELO_INDICATIF_DEFAUT « {indicatif_defaut} » n'est pas un indicatif téléphonique"
        ) from erreur
    try:
        numero = phonenumbers.parse(brut, region)
    except phonenumbers.NumberParseException:
        raise _refus() from None
    if not phonenumbers.is_valid_number(numero):
        raise _refus()
    return phonenumbers.format_number(numero, phonenumbers.PhoneNumberFormat.E164)
