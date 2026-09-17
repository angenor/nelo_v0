#!/usr/bin/env bash
# Test négatif de P-05 : une page qui lève au montage.
set -euo pipefail
fichier=web/app/pages/a-propos.vue
grep -q '^const { t } = useLibelles()$' "$fichier"
perl -0pi -e "s/^const \{ t \} = useLibelles\(\)\$/throw new Error('cassé')\nconst { t } = useLibelles()/m" "$fichier"
grep -q "throw new Error('cassé')" "$fichier"
