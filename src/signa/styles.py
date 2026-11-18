# SPDX-License-Identifier: GPL-3.0-or-later
"""Lecture des styles de tampon depuis un fichier de configuration pyHanko."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from pyhanko.config.errors import ConfigurationError
from pyhanko.stamp import BaseStampStyle, QRStampStyle, StaticStampStyle, TextStampStyle

from signa.settings import config_dir

_STYLE_TYPES = {"text": TextStampStyle, "qr": QRStampStyle, "static": StaticStampStyle}


class StyleError(Exception):
    """Fichier de styles illisible ou style invalide (message en français)."""


def default_config_path() -> Path:
    return config_dir() / "pyhanko.yml"


def example_config_path() -> Path | None:
    """Fichier de styles d'exemple embarqué dans le paquet."""
    candidate = Path(__file__).resolve().parent / "resources" / "pyhanko.example.yml"
    return candidate if candidate.is_file() else None


def ensure_default_config() -> Path:
    """Crée la configuration utilisateur à partir de l'exemple si elle manque."""
    target = default_config_path()
    if not target.exists():
        example = example_config_path()
        if example is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(example, target)
    return target


def _load_entries(config_path: Path) -> dict:
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise StyleError(f"Impossible de lire {config_path.name} : {exc.strerror}") from exc
    except yaml.YAMLError as exc:
        raise StyleError(f"Fichier de styles invalide (YAML) : {exc}") from exc
    entries = data.get("stamp-styles") if isinstance(data, dict) else None
    if not isinstance(entries, dict) or not entries:
        raise StyleError("Aucun style de tampon (« stamp-styles ») dans ce fichier.")
    return entries


def list_styles(config_path: Path) -> list[str]:
    return list(_load_entries(config_path))


def load_style(config_path: Path, name: str) -> BaseStampStyle:
    entries = _load_entries(config_path)
    if name not in entries:
        raise StyleError(f"Style « {name} » introuvable.")
    raw = dict(entries[name])
    style_cls = _STYLE_TYPES.get(raw.pop("type", "text"))
    if style_cls is None:
        raise StyleError(f"Type de style non géré pour « {name} ».")
    try:
        return style_cls.from_config(raw)
    except ConfigurationError as exc:
        raise StyleError(f"Style « {name} » invalide : {exc}") from exc
