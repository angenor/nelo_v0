"""US7-4 — l'assistance est un paquet du socle, pas un service : ni projet, ni point d'entrée."""

import tomllib
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]


def test_aucun_projet_de_service():
    membres = tomllib.loads((RACINE / "pyproject.toml").read_text())["tool"]["uv"]["workspace"][
        "members"
    ]
    for membre in membres:
        nom = tomllib.loads((RACINE / membre / "pyproject.toml").read_text())["project"]["name"]
        if nom == "nelo-api":
            continue
        assert "service" not in nom and "serveur" not in nom, nom


def test_aucun_point_d_entree_dans_l_assistance():
    dossier = RACINE / "modules" / "socle" / "assistance"
    assert not (dossier / "Dockerfile").exists()
    assert not (dossier / "main.py").exists()
    assert not list(dossier.rglob("Dockerfile*"))
