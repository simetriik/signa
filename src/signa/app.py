# SPDX-License-Identifier: GPL-3.0-or-later
"""Fenêtre principale et point d'entrée de Signa."""

from __future__ import annotations

import sys
from pathlib import Path

import pymupdf
from PySide6.QtCore import QEvent, QUrl, Qt
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent, QFileOpenEvent, QIcon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

from signa import __version__, styles
from signa.coords import PdfBox, pdf_box_to_view_rect, view_rect_to_pdf_box
from signa.pageview import PageView
from signa.settings import Settings
from signa.signer import SigningError, sign_pdf

APP_ID = "signa"
ICON_PATH = Path(__file__).resolve().parent / "resources" / "signa.svg"
ZOOM = 1.4  # facteur d'affichage (points → pixels)


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__()
        self.settings = settings if settings is not None else Settings.load()
        self.doc: pymupdf.Document | None = None
        self.pdf_path: Path | None = None
        self.page_index = 0
        self.setWindowTitle("Signa")
        self.setAcceptDrops(True)
        self.resize(1000, 800)
        self._build_ui()
        self._load_styles()
        self._refresh_state()

    # ---------- construction de l'interface ----------
    def _build_ui(self) -> None:
        self.view = PageView()
        self.view.rect_changed.connect(self._on_rect_changed)
        scroll = QScrollArea()
        scroll.setWidget(self.view)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.open_btn = QPushButton("Ouvrir un PDF…")
        self.open_btn.clicked.connect(self.choose_pdf)
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setAccessibleName("Page précédente")
        self.prev_btn.clicked.connect(lambda: self.goto_page(self.page_index - 1))
        self.next_btn = QPushButton("▶")
        self.next_btn.setAccessibleName("Page suivante")
        self.next_btn.clicked.connect(lambda: self.goto_page(self.page_index + 1))
        self.page_spin = QSpinBox()
        self.page_spin.valueChanged.connect(lambda v: self.goto_page(v - 1))
        self.page_total = QLabel("/ 0")
        nav = QHBoxLayout()
        for w in (self.open_btn, self.prev_btn, self.page_spin, self.page_total, self.next_btn):
            nav.addWidget(w)
        nav.addStretch()

        self.cert_edit = QLineEdit(self.settings.certificate_path)
        self.cert_edit.setReadOnly(True)
        self.cert_edit.setPlaceholderText("Aucun certificat (.p12) choisi")
        cert_btn = QPushButton("Certificat…")
        cert_btn.clicked.connect(self.choose_certificate)
        cert_row = QHBoxLayout()
        cert_row.addWidget(self.cert_edit, 1)
        cert_row.addWidget(cert_btn)

        self.style_combo = QComboBox()
        self.style_combo.currentTextChanged.connect(self._on_style_changed)
        styles_btn = QPushButton("Fichier de styles…")
        styles_btn.clicked.connect(self.choose_styles_file)
        self.invisible_check = QCheckBox("Signature invisible")
        self.invisible_check.setChecked(self.settings.invisible)
        self.invisible_check.toggled.connect(self._on_invisible_toggled)
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style du tampon :"))
        style_row.addWidget(self.style_combo, 1)
        style_row.addWidget(styles_btn)
        style_row.addWidget(self.invisible_check)

        self.hint = QLabel()
        self.hint.setWordWrap(True)
        self.sign_btn = QPushButton("Signer…")
        self.sign_btn.setDefault(True)
        self.sign_btn.clicked.connect(self.sign)

        layout = QVBoxLayout()
        layout.addLayout(nav)
        layout.addWidget(scroll, 1)
        layout.addLayout(cert_row)
        layout.addLayout(style_row)
        layout.addWidget(self.hint)
        layout.addWidget(self.sign_btn)
        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

    def _load_styles(self) -> None:
        """Remplit la liste des styles depuis le fichier mémorisé (ou par défaut)."""
        path = Path(self.settings.styles_config_path) if self.settings.styles_config_path else styles.ensure_default_config()
        self.styles_path = path
        self.style_combo.blockSignals(True)
        self.style_combo.clear()
        try:
            names = styles.list_styles(path) if path.is_file() else []
        except styles.StyleError as exc:
            names = []
            self.hint.setText(str(exc))
        self.style_combo.addItems(names)
        if self.settings.style_name in names:
            self.style_combo.setCurrentText(self.settings.style_name)
        self.style_combo.blockSignals(False)

    # ---------- documents ----------
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls()
        if urls and urls[0].toLocalFile().lower().endswith(".pdf"):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        self.open_pdf(Path(event.mimeData().urls()[0].toLocalFile()))

    def choose_pdf(self) -> None:
        name, _ = QFileDialog.getOpenFileName(self, "Ouvrir un PDF", "", "Documents PDF (*.pdf)")
        if name:
            self.open_pdf(Path(name))

    def open_pdf(self, path: Path) -> bool:
        try:
            doc = pymupdf.open(path)
            if doc.needs_pass or doc.page_count == 0:
                raise ValueError("document protégé ou vide")
        except Exception as exc:  # PyMuPDF lève plusieurs types d'erreurs
            QMessageBox.critical(self, "Signa", f"Impossible d'ouvrir ce PDF.\n\n{exc}")
            return False
        self.doc, self.pdf_path = doc, path
        self.setWindowTitle(f"Signa — {path.name}")
        self.page_spin.blockSignals(True)
        self.page_spin.setRange(1, doc.page_count)
        self.page_spin.blockSignals(False)
        self.page_total.setText(f"/ {doc.page_count}")
        self._restore_zone()
        self._refresh_state()
        return True

    def _restore_zone(self) -> None:
        """Rouvre la dernière page/zone si elle existe dans ce document."""
        zone_page, rect = self.settings.zone_page, self.settings.zone_rect
        if self.doc and zone_page is not None and zone_page < self.doc.page_count and len(rect) == 4:
            self.page_index = zone_page
            self._show_current_page()
            self.view.set_rect_points(tuple(rect))
        else:
            self.page_index = 0
            self._show_current_page()
            self.view.set_rect_points(None)

    def goto_page(self, index: int) -> None:
        if not self.doc or not 0 <= index < self.doc.page_count or index == self.page_index:
            return
        self.page_index = index
        self._show_current_page()
        # La zone mémorisée n'est affichée que sur sa page.
        same = self.settings.zone_page == index and len(self.settings.zone_rect) == 4
        self.view.set_rect_points(tuple(self.settings.zone_rect) if same else None)
        self._refresh_state()

    def _show_current_page(self) -> None:
        page = self.doc[self.page_index] if self.doc else None
        self.view.show_page(page, ZOOM)
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(self.page_index + 1)
        self.page_spin.blockSignals(False)

    # ---------- préférences ----------
    def choose_certificate(self) -> None:
        name, _ = QFileDialog.getOpenFileName(self, "Choisir un certificat", self.settings.certificate_path, "Certificats PKCS#12 (*.p12 *.pfx)")
        if name:
            self.settings.certificate_path = name
            self.cert_edit.setText(name)
            self.settings.save()
            self._refresh_state()

    def choose_styles_file(self) -> None:
        name, _ = QFileDialog.getOpenFileName(self, "Fichier de styles pyHanko", str(self.styles_path), "Configuration YAML (*.yml *.yaml)")
        if name:
            self.settings.styles_config_path = name
            self._load_styles()
            self.settings.style_name = self.style_combo.currentText()
            self.settings.save()
            self._refresh_state()

    def _on_style_changed(self, name: str) -> None:
        self.settings.style_name = name
        self.settings.save()
        self._refresh_state()

    def _on_invisible_toggled(self, checked: bool) -> None:
        self.settings.invisible = checked
        self.view.set_drawing_enabled(not checked)
        self.settings.save()
        self._refresh_state()

    def _on_rect_changed(self) -> None:
        rect = self.view.rect_points()
        if rect:
            self.settings.zone_page = self.page_index
            self.settings.zone_rect = list(rect)
            self.settings.save()
        self._refresh_state()

    def _refresh_state(self) -> None:
        has_doc = self.doc is not None
        self.prev_btn.setEnabled(has_doc and self.page_index > 0)
        self.next_btn.setEnabled(has_doc and self.doc is not None and self.page_index < self.doc.page_count - 1)
        self.page_spin.setEnabled(has_doc)
        self.view.set_drawing_enabled(not self.invisible_check.isChecked())
        self.style_combo.setEnabled(not self.invisible_check.isChecked())
        ready = has_doc and bool(self.settings.certificate_path) and (self.invisible_check.isChecked() or (self.view.rect_points() is not None and bool(self.style_combo.currentText())))
        self.sign_btn.setEnabled(ready)
        if not has_doc:
            self.hint.setText("Ouvrez un PDF (bouton ou glisser-déposer).")
        elif not self.settings.certificate_path:
            self.hint.setText("Choisissez votre certificat .p12.")
        elif self.invisible_check.isChecked():
            self.hint.setText("La signature sera invisible (aucun tampon sur la page).")
        elif self.view.rect_points() is None:
            self.hint.setText("Tracez à la souris le rectangle de signature sur la page.")
        else:
            self.hint.setText(self._box_text())

    def _box_text(self) -> str:
        box = self.current_box()
        return f"Zone : page {self.page_index + 1}, ({box.x1}, {box.y1}) → ({box.x2}, {box.y2}) en points PDF." if box else ""

    def current_box(self) -> PdfBox | None:
        rect = self.view.rect_points()
        if not rect or not self.doc:
            return None
        return view_rect_to_pdf_box(self.doc[self.page_index], rect)

    # ---------- signature ----------
    def ask_password(self) -> str | None:
        """Le mot de passe est demandé à chaque signature et jamais stocké."""
        password, ok = QInputDialog.getText(self, "Mot de passe", "Mot de passe du certificat :", QLineEdit.EchoMode.Password)
        return password if ok else None

    def sign(self) -> None:
        if not self.pdf_path:
            return
        invisible = self.invisible_check.isChecked()
        box = None if invisible else self.current_box()
        style = None
        if not invisible:
            try:
                style = styles.load_style(self.styles_path, self.style_combo.currentText())
            except styles.StyleError as exc:
                QMessageBox.critical(self, "Signa", str(exc))
                return
        password = self.ask_password()
        if password is None:
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            output = sign_pdf(self.pdf_path, Path(self.settings.certificate_path), password, page=self.page_index, box=box, style=style)
        except SigningError as exc:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Échec de la signature", str(exc))
            return
        finally:
            password = ""  # nosec B105 (effacement)
        QApplication.restoreOverrideCursor()
        self._show_success(output)

    def _show_success(self, output: Path) -> None:
        box = QMessageBox(QMessageBox.Icon.Information, "Signature réussie", f"Document signé enregistré :\n{output}", parent=self)
        open_btn = box.addButton("Ouvrir le résultat", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Fermer", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is open_btn:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(output)))


class SignaApplication(QApplication):
    """Application Qt qui relaie l'ouverture de fichiers demandée par macOS (Finder, « Ouvrir avec »)."""

    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.window: MainWindow | None = None
        self.pending_file: Path | None = None

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.FileOpen and isinstance(event, QFileOpenEvent):
            path = Path(event.file())
            if self.window is None:  # l'événement peut arriver avant la création de la fenêtre
                self.pending_file = path
            else:
                self.window.open_pdf(path)
            return True
        return super().event(event)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    if "--version" in argv[1:]:
        print(f"signa {__version__}")
        return 0
    app = QApplication.instance() or SignaApplication(argv)
    app.setApplicationName(APP_ID)
    app.setApplicationDisplayName("Signa")
    app.setDesktopFileName(APP_ID)
    app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = MainWindow()
    window.show()
    if isinstance(app, SignaApplication):
        app.window = window
        if app.pending_file is not None:
            window.open_pdf(app.pending_file)
    if len(argv) > 1 and not argv[1].startswith("-"):
        window.open_pdf(Path(argv[1]))
    if "--smoke-test" in argv[1:]:  # démarrage puis sortie (tests de lancement)
        return 0
    return app.exec()
