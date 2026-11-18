# SPDX-License-Identifier: GPL-3.0-or-later
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pymupdf
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from signa import app as app_module
from signa.settings import Settings
from conftest import TEST_PASSWORD


@pytest.fixture
def window(qtbot, tmp_path, monkeypatch, work_pdf, p12_file):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    win = app_module.MainWindow(Settings())
    qtbot.addWidget(win)
    win.show()
    assert win.open_pdf(work_pdf)
    return win


def drag(win, start, end):
    QTest.mousePress(win.view, Qt.MouseButton.LeftButton, pos=QPoint(*start))
    QTest.mouseMove(win.view, QPoint(*end))
    QTest.mouseRelease(win.view, Qt.MouseButton.LeftButton, pos=QPoint(*end))


def test_sign_button_requires_zone_and_cert(window, p12_file):
    assert not window.sign_btn.isEnabled()
    window.settings.certificate_path = str(p12_file)
    drag(window, (50, 50), (250, 120))
    window._refresh_state()
    assert window.sign_btn.isEnabled()


def test_drag_produces_integer_pdf_box(window):
    drag(window, (14, 14), (140, 70))  # ZOOM = 1.4 → 10..100 pt, 10..50 pt
    box = window.current_box()
    assert box.as_tuple() == (10, 792, 100, 832)


def test_zone_is_remembered(window, tmp_path, work_pdf):
    drag(window, (14, 14), (140, 70))
    reopened = Settings.load()
    assert reopened.zone_page == 0 and reopened.zone_rect


def test_full_signing_flow(window, p12_file, monkeypatch):
    window.settings.certificate_path = str(p12_file)
    drag(window, (50, 50), (250, 120))
    monkeypatch.setattr(window, "ask_password", lambda: TEST_PASSWORD)
    shown = []
    monkeypatch.setattr(window, "_show_success", shown.append)
    window.sign()
    assert shown and shown[0].name == "document-signe.pdf" and shown[0].exists()


def test_wrong_password_shows_error(window, p12_file, monkeypatch):
    window.settings.certificate_path = str(p12_file)
    window.invisible_check.setChecked(True)
    monkeypatch.setattr(window, "ask_password", lambda: "faux")
    errors = []
    monkeypatch.setattr(app_module.QMessageBox, "critical", lambda *a: errors.append(a[2]))
    window.sign()
    assert errors and "Mot de passe" in errors[0]


def test_open_invalid_pdf(window, tmp_path, monkeypatch):
    bad = tmp_path / "bad.pdf"
    bad.write_text("pas un pdf")
    monkeypatch.setattr(app_module.QMessageBox, "critical", lambda *a: None)
    assert window.open_pdf(bad) is False


def test_smoke_start(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    assert app_module.main(["signa", "--smoke-test"]) == 0
