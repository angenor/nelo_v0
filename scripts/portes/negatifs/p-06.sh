#!/usr/bin/env bash
# Test négatif de P-06 : une chaîne visible écrite en dur dans la coquille.
set -euo pipefail
fichier=web/app/components/canon/Coquille.vue
grep -q '<CanonCoquilleSansCapacite' "$fichier"
perl -0pi -e 's|(\s*)<CanonCoquilleSansCapacite|$1<p>Bonjour</p>$1<CanonCoquilleSansCapacite|' "$fichier"
grep -q '<p>Bonjour</p>' "$fichier"
