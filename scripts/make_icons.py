# SPDX-License-Identifier: GPL-3.0-or-later
"""Génère les icônes PNG / ICO / ICNS à partir de l'icône SVG (usage : uv run --with pillow python scripts/make_icons.py)."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "src" / "signa" / "resources" / "signa.svg"
OUT = ROOT / "packaging" / "icons"


def render(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    QSvgRenderer(str(SVG)).render(painter)
    painter.end()
    return image


def main() -> None:
    _app = QGuiApplication([])
    OUT.mkdir(exist_ok=True)
    big = OUT / "signa.png"
    render(1024).save(str(big))
    image = Image.open(big)
    image.save(OUT / "signa.ico", sizes=[(s, s) for s in (16, 32, 48, 64, 128, 256)])
    image.save(OUT / "signa.icns")


if __name__ == "__main__":
    main()
