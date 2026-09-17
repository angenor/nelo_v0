# Nelo

Plateforme de gestion pour établissements scolaires.
Pilote : établissements privés d'Abidjan, Côte d'Ivoire — par le cycle **primaire**, seul segment du
MVP ([ADR 018](docs/adr/018-le-mvp-commence-par-le-primaire.md)).

Backend FastAPI/Pydantic · application Nuxt 4 mobile-first · assistance IA intégrée au socle,
désactivable par réglage · PostgreSQL · Valkey · Garage.

---

**Toute la documentation est dans [`docs/`](docs/).**

| Pour… | Ouvrir |
|---|---|
| Comprendre le produit et son périmètre | [docs/00-brief.md](docs/00-brief.md) |
| Savoir où on en est | [docs/progress.md](docs/progress.md) |
| Construire une tranche | [docs/04-roadmap.md](docs/04-roadmap.md) |
| Le modèle et le contrat, qui font foi | [docs/02-domaine.md](docs/02-domaine.md) · [docs/03-api.md](docs/03-api.md) |

## Démarrer

```bash
cp .env.exemple .env                       # changer les NELO_PORT_* si un autre projet occupe les ports
docker compose up -d                       # postgres, valkey, garage
uv sync && pnpm install --frozen-lockfile  # Python 3.14 et openapi-typescript, épinglés
scripts/bd-vierge.sh --avec-jeu-d-essai    # la base, ses deux rôles, les migrations, deux tenants de test
uv run fastapi dev api/main.py             # l'API sur :8000 — /api/v1/sante, /api/v1/parametres
```

## L'interface

```bash
pnpm --filter nelo-web exec playwright install chromium webkit   # une fois, avec réseau
pnpm --filter nelo-web dev       # l'application ; ?persona=un-domaine|cinq-domaines|sept-domaines|aucune-capacite
                                 # la page de style sur /style, le pack fictif avec ?pack=fictif
pnpm --filter nelo-web build     # la construction, dans web/.output
pnpm --filter nelo-web preview   # la construction servie, installable
```

## Vérifier

```bash
scripts/verifier.sh          # ruff, les dix portes, le reparcours sous suspension, typecheck, Vitest,
                             #   la construction, et les tests de l'interface dans un vrai navigateur
scripts/tests-negatifs.sh    # chaque porte cassée dans une copie git, et chacune doit échouer
```

Les guides pas à pas sont [specs/001-socle-serveur/quickstart.md](specs/001-socle-serveur/quickstart.md)
et [specs/002-socle-interface/quickstart.md](specs/002-socle-interface/quickstart.md).

Les instructions destinées aux agents sont dans [CLAUDE.md](CLAUDE.md), lu automatiquement.
