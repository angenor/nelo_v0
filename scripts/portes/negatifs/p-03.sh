#!/usr/bin/env bash
# Test négatif de P-03 : le client typé est modifié à la main et la retouche est indexée.
# La régénération l'efface — la porte doit échouer sur l'écart.
set -euo pipefail
echo "// modifié à la main" >> contrat/client.d.ts
git add contrat/client.d.ts
