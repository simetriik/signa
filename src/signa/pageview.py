# SPDX-License-Identifier: GPL-3.0-or-later
"""Widget d'affichage d'une page PDF avec tracé du rectangle de signature."""

from __future__ import annotations

import pymupdf
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

MIN_DRAG_POINTS = 5.0  # en dessous, le clic est ignoré (évite un rectangle nul)


class PageView(QWidget):
    """Affiche une page ; le rectangle est conservé en points PDF (indépendant du zoom)."""

    rect_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._scale = 1.0
        self._rect: tuple[float, float, float, float] | None = None
        self._origin: QPointF | None = None
        self._drawing_enabled = True
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMinimumSize(200, 200)

    @property
    def scale(self) -> float:
        return self._scale

    def rect_points(self) -> tuple[float, float, float, float] | None:
        """Rectangle (gauche, haut, droite, bas) en points de la page affichée."""
        return self._rect

    def set_rect_points(self, rect: tuple[float, float, float, float] | None) -> None:
        self._rect = rect
        self.update()
        self.rect_changed.emit()

    def set_drawing_enabled(self, enabled: bool) -> None:
        self._drawing_enabled = enabled
        self.setCursor(Qt.CursorShape.CrossCursor if enabled else Qt.CursorShape.ArrowCursor)
        self.update()

    def show_page(self, page: pymupdf.Page | None, scale: float) -> None:
        self._scale = scale
        if page is None:
            self._pixmap = None
            self.setFixedSize(200, 200)
        else:
            pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
            image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            self._pixmap = QPixmap.fromImage(image.copy())
            self.setFixedSize(pix.width, pix.height)
        self.update()

    def _to_points(self, pos: QPointF) -> tuple[float, float]:
        x = min(max(pos.x(), 0), self.width())
        y = min(max(pos.y(), 0), self.height())
        return (x / self._scale, y / self._scale)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._drawing_enabled and self._pixmap and event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._origin is not None:
            x1, y1 = self._to_points(self._origin)
            x2, y2 = self._to_points(event.position())
            self._rect = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._origin is None:
            return
        self._origin = None
        if self._rect and (self._rect[2] - self._rect[0] < MIN_DRAG_POINTS or self._rect[3] - self._rect[1] < MIN_DRAG_POINTS):
            self._rect = None
        self.update()
        self.rect_changed.emit()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        if self._pixmap:
            painter.drawPixmap(0, 0, self._pixmap)
        else:
            painter.fillRect(self.rect(), self.palette().window())
        if self._rect and self._drawing_enabled:
            s = self._scale
            r = QRectF(self._rect[0] * s, self._rect[1] * s, (self._rect[2] - self._rect[0]) * s, (self._rect[3] - self._rect[1]) * s)
            painter.fillRect(r, QColor(30, 110, 220, 50))
            painter.setPen(QPen(QColor(30, 110, 220), 2))
            painter.drawRect(r)
