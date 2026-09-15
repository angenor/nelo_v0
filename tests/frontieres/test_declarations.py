"""US4 — P-11, déclaration : aucun paquet ne déclare le module cloisonné dans ses dépendances."""

import tomllib
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
NOM = "nelo-metier-protection"


def charger(chemin: Path) -> dict:
    return tomllib.loads(chemin.read_text(encoding="utf-8"))


def noms(dependances: list[str]) -> set[str]:
    return {d.split("==")[0].split(">")[0].split("<")[0].split("~")[0].strip() for d in dependances}


def test_aucune_declaration():
    racine = charger(RACINE / "pyproject.toml")
    membres = racine["tool"]["uv"]["workspace"]["members"]
    # Le module cloisonné est membre de l'espace de travail : c'est la seule place où il est nommé.
    assert ("modules", "metier", "protection") in {Path(m).parts for m in membres}
    assert NOM not in noms(racine["project"].get("dependencies", []))
    for groupe in racine.get("dependency-groups", {}).values():
        assert NOM not in noms(groupe)

    inspectes = 0
    for membre in membres:
        projet = charger(RACINE / membre / "pyproject.toml")
        inspectes += 1
        declarees = noms(projet["project"].get("dependencies", []))
        sources = set(projet.get("tool", {}).get("uv", {}).get("sources", {}))
        if projet["project"]["name"] == NOM:
            continue
        assert NOM not in declarees, f"{membre}/pyproject.toml déclare {NOM}"
        assert NOM not in sources, f"{membre}/pyproject.toml source {NOM}"
    assert inspectes == len(membres) > 0
