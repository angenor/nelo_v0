"""Le jeu d'essai : deux tenants complets, de quoi ouvrir une session à la main et en e2e.

    uv run python -m scripts.jeu_essai

Imprime les identifiants en forme `export`, à évaluer dans le shell. Le code pays, le fuseau
horaire et les numéros sont des **données** du tenant et de l'établissement, jamais des constantes
du code : le tenant B porte le pack fictif, et c'est lui qui prouve que rien n'est figé.

Ce que le jeu d'essai sème, et pourquoi :

- deux tenants, avec chacun un établissement, une personne, une année active et une en
  préparation, un compte actif affecté aux deux années, et l'administrateur désigné ;
- un **second établissement** dans le tenant A, auquel le compte A est aussi rattaché : sans lui,
  le choix d'établissement de US4 n'aurait rien à proposer ;
- une personne **sans compte** dans le tenant A : la création de compte de US6 a besoin d'une
  personne à inviter.
"""

import asyncio
from datetime import date

from api.configuration import Configuration
from modules.shared import bd
from modules.socle import annees, habilitations, personnes, tenants

# Les numéros du jeu d'essai. Ils sont **en E.164 valide**, y compris celui du tenant qui porte
# le pack fictif : l'indicatif du pack (999) sert à lire un numéro écrit sans indicatif, il n'est
# pas un plan de numérotation, et aucun compte ne peut porter un numéro qui n'existe pas.
NUMERO_A = "+2250700000001"
NUMERO_B = "+2250700000002"
NUMERO_FICTIF = "+2250700000003"
# Un compte par suite de bout en bout qui **ferme** sa session : fermer celle d'une autre suite
# la ferait tomber, et les suites tournent en parallèle.
NUMERO_FERMETURE = "+2250700000004"


def bornes(decalage: int = 0) -> tuple[date, date]:
    """Une année scolaire qui commence en septembre et finit en juillet."""
    debut = date(date.today().year + decalage, 9, 1)
    return debut, date(debut.year + 1, 7, 31)


async def semer_tenant(nom: str, pays: str, numero: str, langue: str) -> dict:
    tenant_id = await tenants.creer_tenant(f"Établissement d'essai {nom}", pays)
    etablissement = await tenants.creer_etablissement(tenant_id, f"École {nom}", "Africa/Abidjan")
    personne = await personnes.creer_personne(tenant_id, f"Koné {nom}", "Awa", langue, numero)
    debut, fin = bornes()
    annee = await annees.creer_annee(
        tenant_id, etablissement, f"{debut.year}-{fin.year}", debut, fin, "active"
    )
    debut_prep, fin_prep = bornes(1)
    preparation = await annees.creer_annee(
        tenant_id,
        etablissement,
        f"{debut_prep.year}-{fin_prep.year}",
        debut_prep,
        fin_prep,
        "preparation",
    )
    compte = await habilitations.semer_compte(tenant_id, personne, numero)
    for annee_id in (annee, preparation):
        await habilitations.creer_affectation(
            tenant_id, compte, annee_id, etablissement, date.today(), None
        )
    await tenants.designer_administrateur(tenant_id, etablissement, compte)
    return {
        "tenant": tenant_id,
        "etablissement": etablissement,
        "personne": personne,
        "compte": compte,
        "annee": annee,
    }


async def principal() -> None:
    configuration = Configuration()
    bd.configurer(configuration.bd_url_application, taille_pool=1)
    try:
        a = await semer_tenant("A", "CI", NUMERO_A, "fr")
        b = await semer_tenant("B", "ZZ", NUMERO_B, "en")

        # Un second établissement du tenant A, pour que le choix de US4 ait deux entrées.
        etab_a2 = await tenants.creer_etablissement(
            a["tenant"], "École A, annexe", "Africa/Abidjan"
        )
        debut, fin = bornes()
        annee_a2 = await annees.creer_annee(
            a["tenant"], etab_a2, f"{debut.year}-{fin.year}", debut, fin, "active"
        )
        await habilitations.creer_affectation(
            a["tenant"], a["compte"], annee_a2, etab_a2, date.today(), None
        )
        await tenants.designer_administrateur(a["tenant"], etab_a2, a["compte"])

        # Des personnes **sans compte**, une par usage : les tests de bout en bout tournent en
        # parallèle, et deux d'entre eux qui créeraient un compte pour la même personne se
        # gêneraient (une personne n'a qu'un compte par tenant).
        personne_nouvelle = await personnes.creer_personne(
            a["tenant"], "Yao", "Kouadio", "fr", None
        )
        personne_partage = await personnes.creer_personne(
            a["tenant"], "Bamba", "Fatoumata", "fr", None
        )

        # Le compte de la suite qui ferme sa session.
        personne_fermeture = await personnes.creer_personne(
            a["tenant"], "Diarra", "Sekou", "fr", NUMERO_FERMETURE
        )
        compte_fermeture = await habilitations.semer_compte(
            a["tenant"], personne_fermeture, NUMERO_FERMETURE
        )
        await habilitations.creer_affectation(
            a["tenant"], compte_fermeture, a["annee"], a["etablissement"], date.today(), None
        )

        # Un second compte dans le tenant qui porte le pack fictif : de quoi vérifier à la main
        # qu'aucune valeur de pays n'est écrite dans le code. Il lui faut sa propre personne :
        # une personne n'a qu'un compte par tenant.
        personne_fictive = await personnes.creer_personne(
            b["tenant"], "Traoré", "Salif", "en", NUMERO_FICTIF
        )
        compte_fictif = await habilitations.semer_compte(
            b["tenant"], personne_fictive, NUMERO_FICTIF
        )
        await habilitations.creer_affectation(
            b["tenant"], compte_fictif, b["annee"], b["etablissement"], date.today(), None
        )
    finally:
        await bd.fermer()

    print(
        f"export ETAB_A={a['etablissement']} ETAB_A2={etab_a2} ETAB_B={b['etablissement']} "
        f"NUMERO_A={NUMERO_A} NUMERO_B={NUMERO_B} NUMERO_FICTIF={NUMERO_FICTIF} "
        f"NUMERO_FERMETURE={NUMERO_FERMETURE} "
        f"COMPTE_A={a['compte']} COMPTE_FICTIF={compte_fictif} "
        f"PERSONNE_NOUVELLE={personne_nouvelle} PERSONNE_PARTAGE={personne_partage} "
        f"ANNEE_A={a['annee']}"
    )


if __name__ == "__main__":
    asyncio.run(principal())
