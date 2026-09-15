"""PORTE P-12 — toute requête SQL du produit s'exécute contre une base fraîchement migrée.

Deux contrôles, qui remplacent la vérification à la compilation (docs/01-stack.md § 7.5) :

1. **Chaque fonction d'accès aux données** — toute fonction d'un fichier `acces.py` sous
   `modules/` — a au moins une ligne de son corps exécutée par la suite de tests. Une fonction non
   exercée fait échouer la porte **en la nommant** ; ce n'est pas un seuil de couverture.
2. **Le schéma migré est comparé au schéma déclaré** (`tables.py`) : colonne absente, type
   divergent, contrainte manquante — le premier écart est nommé.

    python -m scripts.portes.p12_acces_exerces <code de sortie de la suite de tests>
"""

import ast
import asyncio
import json
import os
import sys
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

RACINE = Path(__file__).resolve().parents[2]
# Chaque module déclare ses tables dans `modules/**/tables.py`, sous le schéma de son nom.
DECLARATIONS = {"tenants": "modules.socle.tenants.tables"}


def fonctions_d_acces() -> list[tuple[Path, str, set[int]]]:
    trouvees = []
    for chemin in sorted((RACINE / "modules").rglob("acces.py")):
        arbre = ast.parse(chemin.read_text(encoding="utf-8"))
        for noeud in arbre.body:
            if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)):
                corps = noeud.body
                if (
                    corps
                    and isinstance(corps[0], ast.Expr)
                    and isinstance(corps[0].value, ast.Constant)
                ):
                    corps = corps[1:] or corps
                lignes = set()
                for instruction in corps:
                    lignes.update(
                        range(
                            instruction.lineno, (instruction.end_lineno or instruction.lineno) + 1
                        )
                    )
                trouvees.append((chemin, noeud.name, lignes))
    return trouvees


def non_exercees() -> tuple[int, list[str]]:
    rapport = json.loads((RACINE / "coverage.json").read_text(encoding="utf-8"))
    executees = {
        (RACINE / fichier).resolve(): set(donnees["executed_lines"])
        for fichier, donnees in rapport["files"].items()
    }
    fonctions = fonctions_d_acces()
    manquantes = [
        f"{chemin.relative_to(RACINE)}::{nom}"
        for chemin, nom, lignes in fonctions
        if not lignes & executees.get(chemin.resolve(), set())
    ]
    return len(fonctions), manquantes


def decrire(ecart) -> str:
    if isinstance(ecart, list):
        return "; ".join(decrire(e) for e in ecart)
    operation = ecart[0]
    match operation:
        case "add_column":
            return f"colonne absente de la base : {ecart[1]}.{ecart[2]}.{ecart[3].name}"
        case "remove_column":
            return f"colonne en base non déclarée : {ecart[1]}.{ecart[2]}.{ecart[3].name}"
        case "add_table":
            return f"table absente de la base : {ecart[1].fullname}"
        case "remove_table":
            return f"table en base non déclarée : {ecart[1].fullname}"
        case "modify_type":
            return f"type divergent : {ecart[1]}.{ecart[2]}.{ecart[3]} ({ecart[5]} en base, {ecart[6]} déclaré)"
        case "modify_nullable":
            return f"nullabilité divergente : {ecart[1]}.{ecart[2]}.{ecart[3]}"
        case _:
            return f"{operation} : {ecart[1:]}"


async def ecarts_de_schema() -> list[str]:
    import importlib

    url = make_url(os.environ["NELO_BD_URL_PROPRIETAIRE"]).set(
        database=os.environ.get("NELO_BD_NOM_TEST", "nelo_test")
    )
    moteur = create_async_engine(url)
    ecarts: list[str] = []
    try:
        async with moteur.connect() as connexion:
            for schema, module in DECLARATIONS.items():
                metadata = importlib.import_module(module).metadata

                def comparer(connexion_sync, schema=schema, metadata=metadata):
                    contexte = MigrationContext.configure(
                        connexion_sync,
                        opts={
                            "include_schemas": True,
                            "include_name": lambda nom, type_, parents: (
                                nom == schema if type_ == "schema" else True
                            ),
                            "include_object": lambda objet, nom, type_, reflechi, compare: (
                                not (type_ == "table" and nom == "alembic_version")
                            ),
                            "compare_type": True,
                        },
                    )
                    return compare_metadata(contexte, metadata)

                ecarts += [decrire(e) for e in await connexion.run_sync(comparer)]
    finally:
        await moteur.dispose()
    return ecarts


def principal() -> None:
    code_tests = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    motifs = []
    ecarts = asyncio.run(ecarts_de_schema())
    if ecarts:
        motifs.append("schéma migré ≠ schéma déclaré — " + ecarts[0])
    if code_tests != 0:
        motifs.append("la suite de tests échoue contre la base fraîchement migrée")
    inspectees, manquantes = non_exercees()
    if inspectees == 0:
        motifs.append("aucune fonction d'accès inspectée")
    for nom in manquantes:
        motifs.append(f"fonction d'accès non exercée : {nom}")
    for motif in motifs:
        print(f"PORTE P-12 ÉCHOUÉE : {motif}", file=sys.stderr)
    if motifs:
        sys.exit(1)
    print(f"PORTE P-12 : {inspectees} fonctions d'accès inspectées et exercées, 0 écart de schéma")


if __name__ == "__main__":
    principal()
