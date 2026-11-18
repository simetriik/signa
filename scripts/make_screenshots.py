# SPDX-License-Identifier: GPL-3.0-or-later
"""Génère les captures d'écran du README en mode offscreen, avec un PDF et une configuration factices.

Usage : uv run python scripts/make_screenshots.py
"""

import os
import tempfile
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pymupdf
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"


def make_demo_pdf(path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 90), "Contrat de démonstration", fontsize=20)
    for i, line in enumerate(("Article 1 - Objet du document.", "Article 2 - Durée et conditions.", "Article 3 - Signatures.")):
        page.insert_text((72, 140 + i * 30), line, fontsize=12)
    doc.save(path)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_CONFIG_HOME"] = tmp  # préférences isolées : rien de personnel dans les images
        from signa import app as app_module
        from signa.settings import Settings

        qt_app = QApplication.instance() or QApplication([])
        OUT.mkdir(parents=True, exist_ok=True)
        window = app_module.MainWindow(Settings())
        window.resize(900, 760)
        window.show()
        qt_app.processEvents()
        window.grab().save(str(OUT / "01-empty.png"))

        pdf = Path(tmp) / "contrat.pdf"
        make_demo_pdf(pdf)
        window.settings.certificate_path = "certificat.p12"  # nom générique affiché
        window.cert_edit.setText("certificat.p12")
        window.open_pdf(pdf)
        window.view.set_rect_points((72.0, 330.0, 300.0, 400.0))
        qt_app.processEvents()
        window.grab().save(str(OUT / "02-zone.png"))
        window.settings = Settings()  # rien n'est écrit dans le vrai dossier utilisateur
        window.close()


if __name__ == "__main__":
    main()
