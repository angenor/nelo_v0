"""La sonde publique — sans en-tête, sans donnée, sans accès à la base ni à Valkey."""

from fastapi import APIRouter

from modules.socle.tenants import ReponseSante

routeur = APIRouter()


@routeur.get(
    "/sante",
    operation_id="sante",
    summary="Sonde publique — sans authentification, sans donnée",
    response_model=ReponseSante,
    responses={200: {"description": "Le serveur est levé"}},
)
async def sante() -> ReponseSante:
    return ReponseSante(etat="OK")
