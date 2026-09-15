#!/usr/bin/env bash
# Test négatif de P-01 : la ligne FORCE ROW LEVEL SECURITY de parametre_valeur est commentée.
# La porte doit échouer en nommant tenants.parametre_valeur.
set -euo pipefail
fichier=migrations/tenants/versions/0001_socle_tenants.py
grep -q 'ALTER TABLE tenants.parametre_valeur FORCE ROW LEVEL SECURITY' "$fichier"
sed -i.bak 's|^\(    op.execute("ALTER TABLE tenants.parametre_valeur FORCE ROW LEVEL SECURITY")\)|    # \1|' "$fichier"
rm -f "$fichier.bak"
