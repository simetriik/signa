# SPDX-License-Identifier: GPL-3.0-or-later
"""Garde-fous du dépôt : licence, pas de donnée personnelle ni de secret."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / line for line in out.splitlines() if (ROOT / line).is_file()]


def test_python_files_have_spdx_header():
    missing = [
        f for f in tracked_files()
        if f.suffix == ".py" and "SPDX-License-Identifier: GPL-3.0-or-later" not in f.read_text()[:300]
    ]
    assert not missing


def test_no_secret_files_tracked():
    assert not [f for f in tracked_files() if f.suffix in {".p12", ".pfx", ".pem", ".key"}]


def test_no_personal_home_paths():
    pattern = re.compile(r"/home/(?!user\b)[a-z_][\w-]*/")
    offenders = []
    for f in tracked_files():
        if f.name == "test_repository.py" or f.suffix in {".lock", ".svg"}:
            continue
        try:
            text = f.read_text()
        except UnicodeDecodeError:
            continue
        if pattern.search(text):
            offenders.append(f.name)
    assert not offenders


def test_version_is_consistent():
    import tomllib

    import signa

    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert signa.__version__ == data["project"]["version"] == data["tool"]["briefcase"]["version"]
