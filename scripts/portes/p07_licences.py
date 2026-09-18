"""PORTE P-07 — aucune dépendance sous licence copyleft fort (docs/01-stack.md § 9).

Deux vérificateurs adossés aux environnements verrouillés : `pip-licenses` pour Python, `pnpm
licenses` pour npm. Toute licence hors de la liste autorisée, **ou inconnue**, échoue en nommant le
paquet. Une expression `A AND B` exige que toutes soient autorisées ; `A OR B`, qu'une le soit.
"""

import json
import re
import subprocess
import sys

AUTORISEES = {
    "MIT",
    # MIT sans obligation d'attribution : strictement plus permissive que MIT.
    # Arrivée en T1a avec cffi, transitive de argon2-cffi.
    "MIT-0",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "BSD",  # classifieur « BSD License », sans précision de clauses : les deux sont autorisées
    "ISC",
    "Zlib",
    "Unicode-3.0",
    "Unicode-DFS-2016",
    "MPL-2.0",
    "OFL-1.1",
    # La licence de la bibliothèque standard Python, et sa forme SPDX historique (argparse).
    "PSF-2.0",
    "Python-2.0",
    # Permissives, arrivées avec Nuxt et son outillage de construction (T0b, research.md R-01) :
    # BlueOak est une licence de type MIT, CC0 une renonciation au droit d'auteur.
    "BlueOak-1.0.0",
    "CC0-1.0",
}
# Une licence permise pour un paquet nommé seulement, avec son motif. caniuse-lite porte les
# données de browserslist : elles servent à la construction et ne voyagent pas jusqu'au client.
EXCEPTIONS_NOMMEES = {
    ("caniuse-lite", "CC-BY-4.0"),
}
SYNONYMES = {
    "mit license": "MIT",
    "mit": "MIT",
    "bsd license": "BSD",
    "apache software license": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "isc license (iscl)": "ISC",
    "isc license": "ISC",
    "mozilla public license 2.0 (mpl 2.0)": "MPL-2.0",
    "python software foundation license": "PSF-2.0",
}
# Les membres de l'espace de travail sont le produit lui-même, pas une dépendance.
PRODUIT = {"nelo"}


def normaliser(licence: str) -> str:
    return SYNONYMES.get(licence.strip().lower(), licence.strip())


def autorisee(expression: str) -> bool:
    expression = expression.strip()
    if expression.startswith("(") and expression.endswith(")"):
        expression = expression[1:-1].strip()
    if not expression or expression.upper() == "UNKNOWN":
        return False
    if " OR " in expression:
        return any(autorisee(e) for e in re.split(r"\s+OR\s+", expression))
    if " AND " in expression:
        return all(autorisee(e) for e in re.split(r"\s+AND\s+", expression))
    if ";" in expression:
        return all(autorisee(e) for e in expression.split(";"))
    return normaliser(expression) in AUTORISEES


def echec(motif: str) -> None:
    print(f"PORTE P-07 ÉCHOUÉE : {motif}", file=sys.stderr)
    sys.exit(1)


def principal() -> None:
    python = json.loads(
        subprocess.run(
            ["pip-licenses", "--format=json", "--with-system", "--from=mixed"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    paquets_python = [p for p in python if p["Name"] not in PRODUIT]
    for paquet in paquets_python:
        if not autorisee(paquet["License"]):
            echec(f"{paquet['Name']} {paquet['Version']} — licence « {paquet['License']} » refusée")

    npm = json.loads(
        subprocess.run(
            ["pnpm", "licenses", "list", "--json", "--long"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        or "{}"
    )
    paquets_npm = 0
    for licence, paquets in npm.items():
        for paquet in paquets:
            paquets_npm += 1
            if not autorisee(licence) and (paquet["name"], licence) not in EXCEPTIONS_NOMMEES:
                echec(f"{paquet['name']} (npm) — licence « {licence} » refusée")

    if not paquets_python:
        echec("aucun paquet Python inspecté")
    print(
        f"PORTE P-07 : {len(paquets_python)} paquets Python, {paquets_npm} paquets npm, "
        "0 licence refusée"
    )


if __name__ == "__main__":
    principal()
