"""L'enveloppe d'erreur sur toutes les sorties — docs/03-api.md § 1.6 et § 1.8.

Quatre gestionnaires : le refus de schéma (`422 VAL_SCHEMA_INVALIDE`, tous les champs fautifs), le
refus métier (son statut, son code), la dépendance indisponible (`503`), et tout le reste
(`500 API_ERREUR_INTERNE`, sans aucun détail technique — la trace va au journal seulement).
"""

import json
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import Send

from modules.shared import DependanceIndisponible, EnveloppeErreur, ErreurMetier

journal = logging.getLogger("nelo.api")


def enveloppe(
    code: str,
    message: str,
    requete_id: str | None,
    *,
    champ: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return EnveloppeErreur(
        code=code, message=message, champ=champ, details=details or {}, requete_id=requete_id
    ).model_dump(mode="json")


async def envoyer_erreur_asgi(
    send: Send,
    statut: int,
    code: str,
    message: str,
    requete_id: str | None,
    *,
    details: dict[str, Any] | None = None,
) -> None:
    """Pour les middlewares ASGI purs, qui refusent avant que FastAPI ne voie la requête."""
    corps = json.dumps(
        enveloppe(code, message, requete_id, details=details), ensure_ascii=False
    ).encode()
    await send(
        {
            "type": "http.response.start",
            "status": statut,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(corps)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": corps})


def _requete_id(request: Request) -> str | None:
    return request.scope.get("state", {}).get("requete_id")


def _chemin(loc: tuple[Any, ...]) -> str:
    morceaux = list(loc[1:]) if loc and loc[0] in ("body", "path", "query") else list(loc)
    return ".".join(str(m) for m in morceaux)


async def _refus_de_schema(request: Request, exc: RequestValidationError) -> JSONResponse:
    champs = [{"chemin": _chemin(tuple(e["loc"])), "motif": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        status_code=422,
        content=enveloppe(
            "VAL_SCHEMA_INVALIDE",
            "le corps de la requête ne respecte pas le schéma",
            _requete_id(request),
            champ=champs[0]["chemin"] if champs else None,
            details={"champs": champs},
        ),
    )


async def _refus_metier(request: Request, exc: ErreurMetier) -> JSONResponse:
    return JSONResponse(
        status_code=exc.statut,
        content=enveloppe(
            exc.code, exc.message, _requete_id(request), champ=exc.champ, details=exc.details
        ),
    )


async def _dependance_indisponible(request: Request, exc: DependanceIndisponible) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content=enveloppe(
            "API_DEPENDANCE_INDISPONIBLE",
            "une dépendance externe est indisponible",
            _requete_id(request),
            details={"dependance": exc.dependance},
        ),
    )


async def _erreur_interne(request: Request, exc: Exception) -> JSONResponse:
    journal.error("erreur interne (requete_id=%s)", _requete_id(request), exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=enveloppe("API_ERREUR_INTERNE", "erreur interne du serveur", _requete_id(request)),
    )


def installer(application: FastAPI) -> None:
    application.add_exception_handler(RequestValidationError, _refus_de_schema)
    application.add_exception_handler(ErreurMetier, _refus_metier)
    application.add_exception_handler(DependanceIndisponible, _dependance_indisponible)
    application.add_exception_handler(Exception, _erreur_interne)
