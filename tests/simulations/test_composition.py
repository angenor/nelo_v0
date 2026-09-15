"""US6-5 — trois services dans la composition, et aucun service d'inférence."""

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parents[2]
INTERDITS = ("inference", "ia", "assistance", "llm")


def test_trois_services_et_pas_un_de_plus():
    composition = yaml.safe_load((RACINE / "compose.yml").read_text())
    services = composition["services"]
    assert set(services) == {"postgres", "valkey", "garage"}
    for nom, service in services.items():
        image = service.get("image", "").split("/")[-1].split(":")[0]
        for mot in INTERDITS:
            assert mot not in nom.split("-"), nom
            assert mot not in image.split("-"), image
    assert "inference" not in (RACINE / "compose.yml").read_text().lower()
