"""Le contrat OpenAPI généré, avec ce que les middlewares exigent.

Les en-têtes `X-Nelo-Etablissement` et `X-Nelo-Requete` sont lus par des middlewares, pas par des
dépendances de route (research.md R-05) : FastAPI ne les voit pas. Ce crochet les ajoute à la
spécification, **requis**, pour que le client typé les porte ; il déclare aussi le refus
`422 VAL_SCHEMA_INVALIDE` sur toute route avec corps.

Il enregistre enfin les schémas d'échange qu'aucune route ne sert encore, pour que le client en
dérive ses types au lieu de les écrire : le contexte de composition de l'interface (T0b, servi par
`GET /moi/capacites` à partir de T1a).

    uv run python -m api.contrat      # écrit contrat/openapi.json, stable octet pour octet
"""

import json
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic.json_schema import models_json_schema

from api.configuration import RACINE
from modules.shared import ContexteCapacites

EN_TETE_ETABLISSEMENT = {
    "name": "X-Nelo-Etablissement",
    "in": "header",
    "required": True,
    "description": "UUID de l'établissement actif. Lu par un middleware — absent ou malformé, `400 TEN_ETABLISSEMENT_REQUIS` ; inconnu, `404 TEN_RESSOURCE_INTROUVABLE`. Résolution provisoire du tenant jusqu'à T1a.",
    "schema": {"type": "string", "format": "uuid"},
}
EN_TETE_REQUETE = {
    "name": "X-Nelo-Requete",
    "in": "header",
    "required": True,
    "description": "UUID v7 généré par le client. Lu par un middleware — absent, `400 REQUETE_CLE_MANQUANTE` ; pas un UUID v7, `400 REQUETE_CLE_INVALIDE`. La réponse est mémorisée 24 h, bornée au tenant.",
    "schema": {"type": "string", "format": "uuid"},
}
METHODES_ECRITURE = {"post", "put", "patch", "delete"}
CHEMINS_SANS_ETABLISSEMENT = {"/sante"}
REFUS_DE_SCHEMA = {
    "description": "`VAL_SCHEMA_INVALIDE` — le corps ne respecte pas le schéma ; `details.champs` liste chaque champ fautif",
    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/EnveloppeErreur"}}},
}

SCHEMAS_SANS_ROUTE = [ContexteCapacites]


def schemas_sans_route() -> dict[str, Any]:
    """Les schémas d'échange sans route et leurs sous-modèles, tels qu'une réponse les sérialise."""
    _, definitions = models_json_schema(
        [(modele, "serialization") for modele in SCHEMAS_SANS_ROUTE],
        ref_template="#/components/schemas/{model}",
    )
    return definitions["$defs"]


def specification(application: FastAPI) -> dict[str, Any]:
    if application.openapi_schema:
        return application.openapi_schema
    document = get_openapi(
        title=application.title,
        version=application.version,
        routes=application.routes,
        servers=application.servers,
    )
    for chemin, operations in document.get("paths", {}).items():
        for methode, operation in operations.items():
            en_tetes = []
            if chemin not in CHEMINS_SANS_ETABLISSEMENT:
                en_tetes.append(EN_TETE_ETABLISSEMENT)
            if methode in METHODES_ECRITURE:
                en_tetes.append(EN_TETE_REQUETE)
            operation["parameters"] = en_tetes + operation.get("parameters", [])
            if "requestBody" in operation:
                operation["responses"].setdefault("422", REFUS_DE_SCHEMA)
    schemas = document.setdefault("components", {}).setdefault("schemas", {})
    for nom, schema in schemas_sans_route().items():
        if nom in schemas:
            raise RuntimeError(f"le schéma sans route « {nom} » porte le nom d'un schéma existant")
        schemas[nom] = schema
    application.openapi_schema = document
    return document


def installer(application: FastAPI) -> None:
    application.openapi = lambda: specification(application)


def ecrire() -> None:
    from api.main import app

    texte = json.dumps(app.openapi(), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    (RACINE / "contrat").mkdir(exist_ok=True)
    (RACINE / "contrat" / "openapi.json").write_text(texte, encoding="utf-8")


if __name__ == "__main__":
    ecrire()
