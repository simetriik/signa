# Contribuer à Signa / Contributing

Merci de votre intérêt ! / Thanks for your interest!

## Mise en place

```sh
git clone https://github.com/simetriik/signa.git && cd signa
uv sync
uv run pytest
QT_QPA_PLATFORM=offscreen uv run signa --smoke-test   # test de démarrage sans écran
```

## Règles

- Code en **anglais** (noms), commentaires, docstrings et interface en **français**.
- Chaque fichier source commence par `# SPDX-License-Identifier: GPL-3.0-or-later`.
- Messages de commit en anglais, format [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- Toute nouvelle fonctionnalité ou correction s'accompagne d'un test. Les tests ne doivent **jamais** utiliser un vrai certificat : ils génèrent un certificat factice (`tests/conftest.py`).
- Ne versionnez aucun certificat, mot de passe, chemin personnel ni donnée personnelle (le test `tests/test_repository.py` vérifie une partie de ces règles).
- Le mot de passe du certificat ne doit jamais être écrit sur disque ni journalisé.

## Installateurs

Les installateurs sont construits par `.github/workflows/release.yml` à chaque tag `v*` (tests sur Linux, Windows et macOS, puis `.deb`, `.msi`, `.dmg` joints à la release).

- **Linux (.deb)** : les dépendances absentes de Debian sont listées dans `packaging/requirements-vendor.txt` (versions de `uv.lock`). Après une mise à jour de pyHanko, mettez ce fichier à jour, puis `dpkg-buildpackage -us -uc -b && lintian ../signa_*_amd64.deb`.
- **Windows / macOS** : [Briefcase](https://briefcase.readthedocs.io/), configuré dans `pyproject.toml` (`[tool.briefcase]`) : `uv tool install briefcase`, puis `briefcase create`, `build` et `package --adhoc-sign` sur le système concerné.
- Icônes : `uv run --with pillow python scripts/make_icons.py` (à partir de `src/signa/resources/signa.svg`).

## Proposer un changement

Une branche par sujet (`feat/...`, `fix/...`), des commits petits et atomiques, puis une pull request décrivant le besoin et la façon de tester.
