"""PORTE P-02 — aucune dépendance en intervalle : chaque déclaration est épinglée par `==` exact.

Inspecte le `pyproject.toml` racine (dépendances, groupes, système de build), celui de chaque membre
de l'espace de travail, et le `package.json` de chaque espace de travail pnpm présent. Les membres
de l'espace de travail `uv` (`nelo-*`, sources `workspace`) sont figés par `uv.lock` et ne portent
pas de version. Échoue en **nommant la dépendance**.
"""

import json
import re
import sys
import tomllib
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
EXACTE_PYTHON = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-\[\],]*\s*==\s*[0-9][A-Za-z0-9.+!\-]*$")
EXACTE_NPM = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.\-]+)?$")


def echec(motif: str) -> None:
    print(f"PORTE P-02 ÉCHOUÉE : {motif}", file=sys.stderr)
    sys.exit(1)


def verifier_python(chemin: Path, sources_espace: set[str]) -> int:
    document = tomllib.loads(chemin.read_text(encoding="utf-8"))
    declarations = list(document.get("project", {}).get("dependencies", []))
    for groupe in document.get("dependency-groups", {}).values():
        declarations += [d for d in groupe if isinstance(d, str)]
    declarations += document.get("build-system", {}).get("requires", [])
    sources = set(document.get("tool", {}).get("uv", {}).get("sources", {}))
    compte = 0
    for declaration in declarations:
        nom = re.split(r"[\s=<>~!\[;]", declaration, maxsplit=1)[0]
        if nom in sources and nom in sources_espace:
            continue
        if not EXACTE_PYTHON.match(declaration.strip()):
            echec(
                f"{chemin.relative_to(RACINE)} : « {declaration} » n'est pas épinglée par == exact"
            )
        compte += 1
    return compte


def verifier_npm(chemin: Path) -> int:
    document = json.loads(chemin.read_text(encoding="utf-8"))
    compte = 0
    for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        for nom, version in document.get(section, {}).items():
            if not EXACTE_NPM.match(version):
                echec(
                    f"{chemin.relative_to(RACINE)} : « {nom}@{version} » n'est pas épinglée exactement"
                )
            compte += 1
    if not (chemin.parent / "pnpm-lock.yaml").exists() and not (RACINE / "pnpm-lock.yaml").exists():
        echec(f"{chemin.relative_to(RACINE)} : aucun pnpm-lock.yaml")
    return compte


def principal() -> None:
    racine = tomllib.loads((RACINE / "pyproject.toml").read_text(encoding="utf-8"))
    membres = racine["tool"]["uv"]["workspace"]["members"]
    noms_espace = {
        tomllib.loads((RACINE / m / "pyproject.toml").read_text(encoding="utf-8"))["project"][
            "name"
        ]
        for m in membres
    }
    if not (RACINE / "uv.lock").exists():
        echec("uv.lock est absent")
    compte = verifier_python(RACINE / "pyproject.toml", noms_espace)
    for membre in membres:
        compte += verifier_python(RACINE / membre / "pyproject.toml", noms_espace)

    lockfiles = 1
    paquets_npm = [RACINE / "package.json"] + [
        p for p in [RACINE / "web" / "package.json"] if p.exists()
    ]
    for paquet in paquets_npm:
        if paquet.exists():
            compte += verifier_npm(paquet)
    if (RACINE / "package.json").exists():
        if not (RACINE / "pnpm-lock.yaml").exists():
            echec("pnpm-lock.yaml est absent")
        lockfiles += 1
    if compte == 0:
        echec("aucune dépendance inspectée")
    print(f"{compte} {lockfiles}")


if __name__ == "__main__":
    principal()
