"""Remplace un texte exact dans un fichier, ou échoue en le disant.

    python3 scripts/portes/negatifs/muter.py <fichier> <avant> <apres>

Les tests négatifs s'en servent pour casser **une** chose à la fois, dans une copie de travail
jetable. Un motif absent est une erreur : une mutation qui ne mute rien ferait croire qu'une porte
tient alors qu'elle n'a rien vu.
"""

import sys
from pathlib import Path


def principal() -> None:
    chemin, avant, apres = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    texte = chemin.read_text(encoding="utf-8")
    if avant not in texte:
        print(f"mutation impossible : le motif est absent de {chemin}", file=sys.stderr)
        sys.exit(2)
    chemin.write_text(texte.replace(avant, apres, 1), encoding="utf-8")


if __name__ == "__main__":
    principal()
