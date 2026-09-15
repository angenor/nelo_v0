#!/usr/bin/env bash
# Test négatif de P-02 : une dépendance déclarée en intervalle.
set -euo pipefail
grep -q '"fastapi==0.141.1"' pyproject.toml
sed -i.bak 's/"fastapi==0.141.1"/"fastapi>=0.141"/' pyproject.toml && rm -f pyproject.toml.bak
