"""Le contrat OpenAPI généré, avec ce que les middlewares exigent.

Les en-têtes `Authorization`, `X-Nelo-Etablissement` et `X-Nelo-Requete` sont lus par des
middlewares, pas par des dépendances de route (research.md R-04) : FastAPI ne les voit pas. Ce crochet les ajoute à la
spécification, **requis**, pour que le client typé les porte ; il déclare aussi le refus
`422 VAL_SCHEMA_INVALIDE` sur toute route avec corps.

Il enregistre enfin les schémas d'échange qu'aucune route ne sert **encore**, pour que le client
en dérive ses types au lieu de les écrire. La liste est vide depuis T1a : le contexte de
composition, qui l'occupait, est servi par `GET /moi/capacites`.

    uv run python -m api.contrat      # écrit contrat/openapi.json, stable octet pour octet
"""

import json
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

from api.asgi import est_libre, exige_un_etablissement
from api.configuration import RACINE

EN_TETE_ETABLISSEMENT = {
    "name": "X-Nelo-Etablissement",
    "in": "header",
    "required": True,
    "description": "UUID de l'établissement actif. Lu par un middleware : absent ou malformé, `400 TEN_ETABLISSEMENT_REQUIS` (avec `details.etablissements`, les rattachements du compte) ; sans affectation vivante du compte, `403 TEN_ETABLISSEMENT_NON_AUTORISE`, que l'établissement soit d'un autre tenant, inexistant ou non rattaché.",
    "schema": {"type": "string", "format": "uuid"},
}
EN_TETE_REQUETE = {
    "name": "X-Nelo-Requete",
    "in": "header",
    "required": True,
    "description": "UUID v7 généré par le client. Lu par un middleware : absent, `400 REQUETE_CLE_MANQUANTE` ; pas un UUID v7, `400 REQUETE_CLE_INVALIDE`. La réponse est mémorisée 24 h, bornée au tenant, ou à l'authentification sur un chemin libre.",
    "schema": {"type": "string", "format": "uuid"},
}
METHODES_ECRITURE = {"post", "put", "patch", "delete"}
EN_TETE_AUTHORIZATION = {
    "name": "Authorization",
    "in": "header",
    "required": True,
    "description": "`Bearer {jwt}`, lu par le middleware de session. Absent ou sans `Bearer`, `401 AUT_JETON_MANQUANT` ; signature ou expiration, `401 AUT_JETON_INVALIDE` ; session révoquée, `401 AUT_SESSION_REVOQUEE`.",
    "schema": {"type": "string"},
}

REFUS_DE_SCHEMA = {
    "description": "`VAL_SCHEMA_INVALIDE` : le corps ne respecte pas le schéma ; `details.champs` liste chaque champ fautif",
    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/EnveloppeErreur"}}},
}

# Vide depuis T1a : `GET /moi/capacites` sert le contexte, et FastAPI le publie lui-même.
# Une tranche qui pose un schéma d'échange avant sa route l'ajoute ici, et l'en retire en
# livrant la route, sinon la fusion lèverait sur la collision de nom.
SCHEMAS_SANS_ROUTE: list[type[BaseModel]] = []


def schemas_sans_route() -> dict[str, Any]:
    """Les schémas d'échange sans route et leurs sous-modèles, tels qu'une réponse les sérialise."""
    if not SCHEMAS_SANS_ROUTE:
        return {}
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
            if exige_un_etablissement(chemin):
                en_tetes.append(EN_TETE_ETABLISSEMENT)
            if not est_libre(chemin):
                en_tetes.append(EN_TETE_AUTHORIZATION)
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
