#!/usr/bin/env bash
# Test négatif de P-07 : une dépendance copyleft réellement installée dans l'environnement de la copie.
set -euo pipefail
site=$(uv run --frozen python -c "import sysconfig; print(sysconfig.get_paths()['purelib'])")
dossier="$site/copyleft_test-0.0.0.dist-info"
mkdir -p "$dossier"
printf 'Metadata-Version: 2.1\nName: copyleft-test\nVersion: 0.0.0\nLicense: GPL-3.0-only\n' > "$dossier/METADATA"
: > "$dossier/RECORD"
