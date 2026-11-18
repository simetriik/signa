# SPDX-License-Identifier: GPL-3.0-or-later
import pymupdf
import pytest
from conftest import make_pdf

from signa.coords import PdfBox, normalize, pdf_box_to_view_rect, view_rect_to_pdf_box


def open_page(tmp_path, **kw):
    path = tmp_path / "c.pdf"
    make_pdf(path, **kw)
    return pymupdf.open(path)[0]


def test_normalize_orders_corners():
    assert normalize(10, 50, 5, 20) == (5, 20, 10, 50)


def test_origin_is_bottom_left(tmp_path):
    page = open_page(tmp_path)
    # Coin haut-gauche de la vue → haut de la page PDF (y = 842).
    box = view_rect_to_pdf_box(page, (0, 0, 100, 50))
    assert box == PdfBox(0, 792, 100, 842)


def test_bottom_of_view_is_y_zero(tmp_path):
    page = open_page(tmp_path)
    box = view_rect_to_pdf_box(page, (10, 800, 110, 842))
    assert box == PdfBox(10, 0, 110, 42)


def test_drag_direction_is_irrelevant(tmp_path):
    page = open_page(tmp_path)
    a = view_rect_to_pdf_box(page, (100, 50, 0, 0))
    b = view_rect_to_pdf_box(page, (0, 0, 100, 50))
    assert a == b


def test_values_are_integers(tmp_path):
    page = open_page(tmp_path)
    box = view_rect_to_pdf_box(page, (10.4, 20.6, 100.5, 80.2))
    assert all(isinstance(v, int) for v in box.as_tuple())


def test_offset_mediabox(tmp_path):
    page = open_page(tmp_path, mediabox_origin=True)
    box = view_rect_to_pdf_box(page, (0, 0, 100, 50))
    # La page démarre à x=50 et son bord haut est à y=942.
    assert box == PdfBox(50, 892, 150, 942)


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_roundtrip(tmp_path, rotation):
    page = open_page(tmp_path, rotation=rotation)
    rect = (20.0, 30.0, 120.0, 90.0)
    box = view_rect_to_pdf_box(page, rect)
    back = pdf_box_to_view_rect(page, box)
    assert back == pytest.approx(rect, abs=1.0)


def test_rotation_90_maps_view_corner(tmp_path):
    page = open_page(tmp_path, rotation=90)
    # Page tournée de 90° : le coin haut-gauche de la vue est le coin bas-gauche du PDF.
    box = view_rect_to_pdf_box(page, (0, 0, 50, 100))
    assert (box.x1, box.y1) == (0, 0)
    assert (box.x2, box.y2) == (100, 50)
