"""P-12 — aucune requête construite par concaténation : S608 active, et `text()` ne prend qu'une constante."""

import ast
import tomllib
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]


def test_s608_est_active():
    ruff = tomllib.loads((RACINE / "pyproject.toml").read_text())["tool"]["ruff"]["lint"]
    assert "S608" in ruff["select"] or "S" in ruff["select"]
    assert "S608" not in ruff.get("ignore", [])


def test_text_ne_prend_qu_une_constante():
    inspectes = 0
    fautifs = []
    for dossier in ("modules", "api"):
        for chemin in sorted((RACINE / dossier).rglob("*.py")):
            for noeud in ast.walk(ast.parse(chemin.read_text(encoding="utf-8"))):
                if not isinstance(noeud, ast.Call):
                    continue
                nom = getattr(noeud.func, "id", None) or getattr(noeud.func, "attr", None)
                if nom != "text":
                    continue
                inspectes += 1
                argument = noeud.args[0] if noeud.args else None
                if not (isinstance(argument, ast.Constant) and isinstance(argument.value, str)):
                    fautifs.append(f"{chemin.relative_to(RACINE)}:{noeud.lineno}")
    assert inspectes > 0, "aucun appel à text() inspecté"
    assert not fautifs, "text() avec un argument non constant :\n" + "\n".join(fautifs)
