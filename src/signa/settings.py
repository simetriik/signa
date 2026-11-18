# SPDX-License-Identifier: GPL-3.0-or-later
"""Mémorisation des préférences (dernier certificat, style, zone).

Le mot de passe du certificat n'est JAMAIS stocké.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from platformdirs import user_config_dir


def config_dir() -> Path:
    """Dossier de configuration propre au système (XDG, AppData, Library)."""
    return Path(user_config_dir("signa", appauthor=False, roaming=True))


@dataclass
class Settings:
    certificate_path: str = ""
    styles_config_path: str = ""
    style_name: str = ""
    invisible: bool = False
    # Zone : page (0-indexée) et rectangle en points de la page affichée.
    zone_page: int | None = None
    zone_rect: list[float] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        path = path or config_dir() / "settings.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        try:
            return cls(**known)
        except TypeError:
            return cls()

    def save(self, path: Path | None = None) -> None:
        path = path or config_dir() / "settings.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
