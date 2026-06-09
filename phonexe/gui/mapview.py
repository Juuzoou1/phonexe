"""
Fully-offline world map widget.

Renders bundled Natural Earth land polygons (public domain) with QPainter in
an equirectangular projection — no network or tile server required — and plots
geolocation markers on top. Supports wheel-zoom, drag-pan, and fit-to-markers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QWidget

from . import theme

try:  # Python 3.9+ resource access
    from importlib.resources import files as _res_files
except Exception:  # pragma: no cover
    _res_files = None


def _load_land() -> list[list[list[float]]]:
    try:
        if _res_files is not None:
            data = (
                _res_files("phonexe.gui.assets")
                .joinpath("world_land.json")
                .read_text(encoding="utf-8")
            )
        else:  # pragma: no cover
            from pathlib import Path

            data = (Path(__file__).parent / "assets" / "world_land.json").read_text(
                encoding="utf-8")
        return json.loads(data).get("polygons", [])
    except Exception:
        return []


@dataclass
class MapMarker:
    lat: float
    lon: float
    label: str = ""


class OfflineMap(QWidget):
    def __init__(self):
        super().__init__()
        self._land = _load_land()
        self._markers: list[MapMarker] = []
        self._zoom = 1.0
        self._offset = QPointF(0, 0)
        self._drag_origin: QPoint | None = None
        self.setMinimumHeight(280)
        self.setMouseTracking(True)

    # ------------------------------------------------------------ data
    def set_markers(self, markers: list[MapMarker]) -> None:
        self._markers = markers
        self.fit_to_markers()
        self.update()

    def fit_to_markers(self) -> None:
        if not self._markers:
            self._zoom = 1.0
            self._offset = QPointF(0, 0)
            return
        lats = [m.lat for m in self._markers]
        lons = [m.lon for m in self._markers]
        # Center the view on the marker centroid at a comfortable zoom.
        clat = sum(lats) / len(lats)
        clon = sum(lons) / len(lons)
        self._zoom = 4.0 if len(self._markers) > 1 else 6.0
        w, h = max(self.width(), 1), max(self.height(), 1)
        cx, cy = self._project(clat, clon, w, h, zoom=1.0, offset=QPointF(0, 0))
        # offset so the centroid lands in the middle of the viewport
        self._offset = QPointF(
            w / 2 - cx * self._zoom, h / 2 - cy * self._zoom
        )

    # ------------------------------------------------------------ projection
    def _project(self, lat, lon, w, h, zoom=None, offset=None):
        zoom = self._zoom if zoom is None else zoom
        offset = self._offset if offset is None else offset
        x = (lon + 180.0) / 360.0 * w
        y = (90.0 - lat) / 180.0 * h
        return x * zoom + offset.x(), y * zoom + offset.y()

    # ------------------------------------------------------------ interaction
    def wheelEvent(self, e):  # noqa: N802
        factor = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        self._zoom = max(1.0, min(40.0, self._zoom * factor))
        self.update()

    def mousePressEvent(self, e):  # noqa: N802
        self._drag_origin = e.position().toPoint()

    def mouseMoveEvent(self, e):  # noqa: N802
        if self._drag_origin is not None:
            p = e.position().toPoint()
            delta = p - self._drag_origin
            self._offset += QPointF(delta)
            self._drag_origin = p
            self.update()

    def mouseReleaseEvent(self, e):  # noqa: N802
        self._drag_origin = None

    # ------------------------------------------------------------ paint
    def paintEvent(self, _e):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#0c1424"))

        # graticule every 30°
        grid = QPen(QColor(theme.BORDER), 1, Qt.PenStyle.DotLine)
        p.setPen(grid)
        for lon in range(-180, 181, 30):
            x, _ = self._project(0, lon, w, h)
            p.drawLine(int(x), 0, int(x), h)
        for lat in range(-90, 91, 30):
            _, y = self._project(lat, 0, w, h)
            p.drawLine(0, int(y), w, int(y))

        # land polygons
        p.setPen(QPen(QColor("#2a3a57"), 1))
        p.setBrush(QColor("#16233c"))
        for ring in self._land:
            poly = QPolygonF()
            for lon, lat in ring:
                x, y = self._project(lat, lon, w, h)
                poly.append(QPointF(x, y))
            p.drawPolygon(poly)

        # markers
        f = QFont()
        f.setPointSize(8)
        p.setFont(f)
        for m in self._markers:
            x, y = self._project(m.lat, m.lon, w, h)
            # pin
            p.setPen(QPen(QColor("#0a0e1a"), 1))
            p.setBrush(QColor(theme.DANGER))
            p.drawEllipse(QPointF(x, y), 6, 6)
            p.setBrush(QColor("#ffffff"))
            p.drawEllipse(QPointF(x, y), 2, 2)
            if m.label:
                p.setPen(QColor(theme.TEXT))
                p.drawText(int(x) + 9, int(y) + 4, m.label)
        p.end()
