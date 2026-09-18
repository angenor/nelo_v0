"""Les country packs semés : ce que le pays dit, en **données**, jamais en code (principe V).

Deux packs. Celui de la Côte d'Ivoire, pays du pilote, et un pack **fictif** dont aucune valeur ne
coïncide avec le premier : devise à deux décimales, deux périodes au lieu de trois, un autre
indicatif, et un vocabulaire où « classe » ne se dit pas « Classe ». Le test d'agnosticité fait
tourner le contexte sur ce second pack : si une valeur du premier se retrouvait écrite dans le
code, elle apparaîtrait ici et le test tomberait.

`contenu` porte ce que docs/02-domaine.md § 1.3 énumère ; T1a n'en lit que le sous-ensemble du
contexte et le format de numéro. Un pack publié ne se modifie jamais en place : on en publie une
version de plus.
"""

from typing import Any, TypedDict

# Les dix-sept codes neutres de docs/02-domaine.md § 15, dans l'ordre du glossaire.
CODES_NEUTRES = (
    "ANNEE",
    "PERIODE",
    "CLASSE",
    "PROFESSEUR_PRINCIPAL",
    "BULLETIN",
    "NOTE",
    "MENTION",
    "RANG",
    "RESPONSABLE",
    "CHEF_ETABLISSEMENT",
    "CENSEUR",
    "ECONOME",
    "INSTANCE_PARENTS",
    "FRAIS_SCOLARITE",
    "EXAMEN_NATIONAL",
    "CONSEIL_ELEVES",
    "CONSEIL_CLASSE",
)


class EntreePack(TypedDict):
    pays_code: str
    version: int
    contenu: dict[str, Any]


def _vocabulaire(libelles: dict[str, tuple[str, str]]) -> dict[str, dict[str, str]]:
    manquants = set(CODES_NEUTRES) - set(libelles)
    if manquants:
        raise ValueError(f"vocabulaire incomplet : {sorted(manquants)}")
    return {code: {"fr": libelles[code][0], "en": libelles[code][1]} for code in CODES_NEUTRES}


COTE_D_IVOIRE: EntreePack = {
    "pays_code": "CI",
    "version": 1,
    "contenu": {
        "devise": {"code": "XOF", "exposant": 0, "symbole": "F"},
        "langues": ["fr", "en"],
        "decoupage": "TRIMESTRES",
        "telephone": {"indicatif": "225"},
        "vocabulaire": _vocabulaire(
            {
                "ANNEE": ("Année scolaire", "School year"),
                "PERIODE": ("Trimestre", "Term"),
                "CLASSE": ("Classe", "Class"),
                "PROFESSEUR_PRINCIPAL": ("Maître titulaire", "Class teacher"),
                "BULLETIN": ("Bulletin", "Report card"),
                "NOTE": ("Note", "Mark"),
                "MENTION": ("Mention", "Grade"),
                "RANG": ("Rang", "Position in class"),
                "RESPONSABLE": ("Responsable légal", "Guardian"),
                "CHEF_ETABLISSEMENT": ("Directeur", "Head teacher"),
                "CENSEUR": ("Éducateur", "Assistant head"),
                "ECONOME": ("Économe", "Bursar"),
                "INSTANCE_PARENTS": ("Association des parents", "Parent association"),
                "FRAIS_SCOLARITE": ("Frais de scolarité", "School fees"),
                "EXAMEN_NATIONAL": ("Examen national", "National examination"),
                "CONSEIL_ELEVES": ("Conseil des élèves", "Pupil council"),
                "CONSEIL_CLASSE": ("Conseil des maîtres", "Class committee"),
            }
        ),
    },
}

# Le pack du test d'agnosticité : aucune de ses valeurs n'est celle du premier.
FICTIF: EntreePack = {
    "pays_code": "ZZ",
    "version": 1,
    "contenu": {
        "devise": {"code": "XFT", "exposant": 2, "symbole": "¤"},
        "langues": ["fr", "en"],
        "decoupage": "SEMESTRES",
        "telephone": {"indicatif": "999"},
        # En réserve : l'échelle des notes vient du référentiel et non du code. Rien ne la lit
        # en T1a ; elle est ici pour que T2a la trouve semée, et sur dix, pas sur vingt.
        "echelle": {"maximum": "10", "minimum": "0"},
        "vocabulaire": _vocabulaire(
            {
                "ANNEE": ("Année d'études", "Study year"),
                "PERIODE": ("Semestre", "Semester"),
                "CLASSE": ("Cohorte", "Stream"),
                "PROFESSEUR_PRINCIPAL": ("Tuteur de cohorte", "Form master"),
                "BULLETIN": ("Relevé", "Terminal report"),
                "NOTE": ("Score", "Score"),
                "MENTION": ("Appréciation", "Band"),
                "RANG": ("Position", "Position"),
                "RESPONSABLE": ("Tuteur légal", "Parent"),
                "CHEF_ETABLISSEMENT": ("Proviseur", "Principal"),
                "CENSEUR": ("Surveillant général", "Assistant head (discipline)"),
                "ECONOME": ("Intendant", "Treasurer"),
                "INSTANCE_PARENTS": ("Comité des familles", "Families committee"),
                "FRAIS_SCOLARITE": ("Écolage", "Levies"),
                "EXAMEN_NATIONAL": ("Épreuve nationale", "National assessment"),
                "CONSEIL_ELEVES": ("Assemblée des délégués", "Student council"),
                "CONSEIL_CLASSE": ("Commission de cohorte", "Stream committee"),
            }
        ),
    },
}

PACKS: list[EntreePack] = [COTE_D_IVOIRE, FICTIF]
