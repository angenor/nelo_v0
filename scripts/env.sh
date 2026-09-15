# Charge `.env` s'il existe, sans écraser une variable déjà posée dans l'environnement.
# À sourcer depuis la racine du dépôt.
if [ -f .env ]; then
  while IFS='=' read -r cle valeur; do
    case "$cle" in ''|\#*) continue ;; esac
    if [ -z "${!cle+x}" ]; then export "$cle=$valeur"; fi
  done < .env
fi
