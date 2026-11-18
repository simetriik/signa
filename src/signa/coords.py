# SPDX-License-Identifier: GPL-3.0-or-later
"""Conversion des coordonnées affichées vers les coordonnées PDF.

Le PDF a son origine en bas à gauche ; l'affichage l'a en haut à gauche.
Toutes les fonctions ici sont pures et testables sans interface graphique.
"""

from __future__ import annotations

from dataclasses import dataclass

import pymupdf


@dataclass(frozen=True)
class PdfBox:
    """Rectangle en coordonnées PDF entières (origine en bas à gauche)."""

    x1: int
    y1: int
    x2: int
    y2: int

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.x1, self.y1, self.x2, self.y2)


def normalize(x_a: float, y_a: float, x_b: float, y_b: float) -> tuple[float, float, float, float]:
    """Ordonne deux coins opposés en (gauche, haut, droite, bas)."""
    return (min(x_a, x_b), min(y_a, y_b), max(x_a, x_b), max(y_a, y_b))


def view_rect_to_pdf_box(page: pymupdf.Page, rect: tuple[float, float, float, float]) -> PdfBox:
    """Convertit un rectangle exprimé en points de la page affichée en PdfBox.

    `rect` est en points, origine en haut à gauche de la page telle qu'elle
    est affichée (rotation appliquée). On passe par les matrices de PyMuPDF
    pour gérer rotation, MediaBox/CropBox décalées et inversion de l'axe Y.
    """
    left, top, right, bottom = normalize(*rect)
    unrotated = pymupdf.Rect(left, top, right, bottom) * page.derotation_matrix
    pdf_rect = unrotated * ~page.transformation_matrix
    pdf_rect.normalize()
    return PdfBox(
        round(pdf_rect.x0),
        round(pdf_rect.y0),
        round(pdf_rect.x1),
        round(pdf_rect.y1),
    )


def pdf_box_to_view_rect(page: pymupdf.Page, box: PdfBox) -> tuple[float, float, float, float]:
    """Opération inverse : restitue le rectangle affiché (pour la mémoire de zone)."""
    pdf_rect = pymupdf.Rect(*box.as_tuple())
    unrotated = pdf_rect * page.transformation_matrix
    view = unrotated * page.rotation_matrix
    view.normalize()
    return (view.x0, view.y0, view.x1, view.y1)
