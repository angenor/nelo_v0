#!/usr/bin/env bash
# Test négatif de P-12 : une colonne renommée dans la migration, sans toucher tables.py ni acces.py.
set -euo pipefail
fichier=migrations/tenants/versions/0001_socle_tenants.py
grep -q 'sa.Column("valeur", JSONB, nullable=False)' "$fichier"
sed -i.bak 's/sa.Column("valeur", JSONB, nullable=False)/sa.Column("valeur_json", JSONB, nullable=False)/' "$fichier"
rm -f "$fichier.bak"
