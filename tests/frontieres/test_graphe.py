"""US4 — la hiérarchie des paquets est un test (docs/01-stack.md § 2.4), et chaque arête est déclarée."""

import tomllib
from pathlib import Path

import grimp
import pytest

import modules.metier.protection as protection

RACINE = Path(__file__).resolve().parents[2]
PROTECTION = protection.__name__

# De la plus haute à la plus basse ; une couche n'importe que les couches plus basses.
COUCHES = [
    {"api"},
    {"modules.segments"},
    {"modules.metier"},
    {"modules.socle"},
    {"modules.shared", "modules.domaine"},
]


@pytest.fixture(scope="module")
def graphe() -> grimp.ImportGraph:
    graphe = grimp.build_graph("api", "modules")
    print(f"nombre de modules inspectés : {len(graphe.modules)}")
    assert len(graphe.modules) > 0, "aucun module inspecté : la porte n'a rien prouvé"
    return graphe


def couche(module: str) -> int | None:
    for rang, familles in enumerate(COUCHES):
        if any(module == f or module.startswith(f + ".") for f in familles):
            return rang
    return None


def aretes(graphe: grimp.ImportGraph):
    for importeur in graphe.modules:
        for importe in graphe.find_modules_directly_imported_by(importeur):
            if importe in graphe.modules:
                yield importeur, importe


def test_le_graphe_n_est_pas_vide(graphe):
    assert any(m.startswith("modules.socle.tenants") for m in graphe.modules)


def test_hierarchie(graphe):
    interdites = []
    for importeur, importe in aretes(graphe):
        haut, bas = couche(importeur), couche(importe)
        if haut is None or bas is None:
            continue
        if bas < haut:
            interdites.append(f"{importeur} → {importe}")
        elif bas == haut == len(COUCHES) - 1 and importeur.split(".")[1] != importe.split(".")[1]:
            interdites.append(f"{importeur} → {importe} (shared et domaine sont indépendants)")
    assert not interdites, "arêtes interdites :\n" + "\n".join(interdites)


def test_aucune_arete_vers_protection(graphe):
    interdites = [
        f"{importeur} → {importe}"
        for importeur, importe in aretes(graphe)
        if (importe == PROTECTION or importe.startswith(PROTECTION + "."))
        and not (importeur == PROTECTION or importeur.startswith(PROTECTION + "."))
    ]
    assert not interdites, "arêtes vers le module cloisonné :\n" + "\n".join(interdites)


def paquet(module: str) -> str | None:
    """Le membre de l'espace de travail qui contient le module : son dossier et son nom."""
    morceaux = module.split(".")
    if morceaux[0] == "api":
        return "api"
    if morceaux[0] != "modules" or len(morceaux) < 2:
        return None
    if morceaux[1] in ("shared", "domaine"):
        return "/".join(morceaux[:2])
    if len(morceaux) >= 3:
        return "/".join(morceaux[:3])
    return None


def nom_declare(dossier: str) -> str:
    return tomllib.loads((RACINE / dossier / "pyproject.toml").read_text())["project"]["name"]


def dependances(dossier: str) -> set[str]:
    projet = tomllib.loads((RACINE / dossier / "pyproject.toml").read_text())["project"]
    return set(projet.get("dependencies", []))


def test_chaque_arete_est_declaree(graphe):
    non_declarees = set()
    for importeur, importe in aretes(graphe):
        a, b = paquet(importeur), paquet(importe)
        if a is None or b is None or a == b:
            continue
        if not (RACINE / b / "pyproject.toml").exists():
            continue
        if nom_declare(b) not in dependances(a):
            non_declarees.add(
                f"{a}/pyproject.toml ne déclare pas {nom_declare(b)} ({importeur} → {importe})"
            )
    assert not non_declarees, "\n".join(sorted(non_declarees))
