#!/usr/bin/env bash
# Test négatif de P-11 : un import du module cloisonné, différé au fond d'une fonction de route.
set -euo pipefail
fichier=api/routes/parametres.py
grep -q '^async def lire_parametres(' "$fichier"
awk '{print} /^async def lire_parametres\(/ {print "    from modules.metier import protection  # noqa: F401"}' "$fichier" > "$fichier.mute"
mv "$fichier.mute" "$fichier"
