#!/usr/bin/env bash
# Test négatif de P-04 : le module doré du socle importe un paquet de metier/.
set -euo pipefail
fichier=modules/socle/tenants/service.py
{ echo "from modules.metier.finance import agregateur_paiement  # noqa: F401"; cat "$fichier"; } > "$fichier.mute"
mv "$fichier.mute" "$fichier"
