"""US4 — P-11, graphe : un chemin vers le module cloisonné écrit en chaîne est arrêté.

`importlib.import_module("…")`, `__import__("…")`, un chemin de fichier : le graphe d'imports ne
les voit pas, ce parcours si. Seuls le module cloisonné lui-même et ce test sont exemptés.
"""

import ast
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
DOSSIERS = ["api", "modules", "migrations", "scripts", "tests"]
MOTIFS = ("modules." + "metier.protection", "metier/" + "protection")
EXEMPTES = {RACINE / "modules" / "metier" / "protection", Path(__file__).resolve()}


def fichiers():
    for dossier in DOSSIERS:
        for chemin in sorted((RACINE / dossier).rglob("*.py")):
            chemin = chemin.resolve()
            if any(chemin == e or e in chemin.parents for e in EXEMPTES):
                continue
            yield chemin


def test_aucune_chaine_vers_protection():
    inspectes = 0
    suspectes = []
    for chemin in fichiers():
        inspectes += 1
        arbre = ast.parse(chemin.read_text(encoding="utf-8"), filename=str(chemin))
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Constant) and isinstance(noeud.value, str):
                if any(motif in noeud.value for motif in MOTIFS):
                    suspectes.append(f"{chemin.relative_to(RACINE)}:{noeud.lineno}")
    print(f"fichiers inspectés : {inspectes}")
    assert inspectes > 0, "aucun fichier inspecté"
    assert not suspectes, "chaînes suspectes :\n" + "\n".join(suspectes)
