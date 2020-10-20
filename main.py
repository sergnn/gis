import json
import sys
from math import ceil
from pathlib import Path

from PyQt5 import QtGui
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget

from utils.tiles import LonLat, deg_per_tile, TILE_SIZE, tile_geo, YandexSatellite

SETTINGS = Path('settings.json')


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.drag_start_point = QPoint(0, 0)
        self.left_mouse_button_pressed = False

        settings = json.loads(SETTINGS.read_text())

        # Init zoom
        self.zoom_level = settings['zoom']

        # Central point Lat (-90 - 90), Lon (0 - 180)
        self.central_point_geo = LonLat(settings['lon'],
                                        settings['lat'])

        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(screen.width() // 4, screen.height() // 4, screen.width() // 2, screen.height() // 2)
        self.setWindowTitle('GIS')
        self.calc_geo()
        self.show()

    def calc_geo(self):
        self.deg_per_tile = deg_per_tile(self.zoom_level)

        self.deg_per_pixel = LonLat(self.deg_per_tile.lon / TILE_SIZE,
                                    self.deg_per_tile.lat / TILE_SIZE)

        self.central_point_tile = QPoint(int((self.central_point_geo.lon + LonLat.TOTAL_LON / 2) / self.deg_per_tile.lon),
                                         int((LonLat.TOTAL_LAT / 2 - self.central_point_geo.lat) / self.deg_per_tile.lat))

        self.window_width = self.geometry().width()
        self.window_height = self.geometry().height()

        self.tiles_count = QPoint(ceil(self.window_width / TILE_SIZE),
                                  ceil(self.window_height / TILE_SIZE))

        self.central_point = QPoint(self.window_width // 2,
                                    self.window_height // 2)

        self.central_point_tile_geo = tile_geo(self.central_point_tile.x(), self.central_point_tile.y(), self.zoom_level)
        print(self.central_point_tile_geo.lat, self.central_point_tile_geo.lon)
        self.tile_shift = QPoint(-int((self.central_point_geo.lon - self.central_point_tile_geo.lon) / self.deg_per_pixel.lon),
                                 int((self.central_point_geo.lat - self.central_point_tile_geo.lat) / self.deg_per_pixel.lat))
        print(self.central_point_tile)
        print(self.tile_shift)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        qp.setFont(QFont('Calibri', 10))
        self.draw_text(event, qp)
        qp.end()

    def wheelEvent(self, event):
        wheel_up = event.angleDelta().y() > 0

        self.zoom_level += 1 if wheel_up else - 1
        if self.zoom_level < 1:
            self.zoom_level = 1

        self.calc_geo()
        self.repaint()

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.left_mouse_button_pressed = a0.button() == Qt.LeftButton
        self.drag_start_point = QPoint(a0.x(), a0.y())
        self.drag_start_central_point_geo = self.central_point_geo

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.button() == Qt.LeftButton:
            self.left_mouse_button_pressed = False

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.central_point_geo = LonLat(self.drag_start_central_point_geo.lon - (a0.x() - self.drag_start_point.x()) * self.deg_per_pixel.lon,
                                        self.drag_start_central_point_geo.lat + (a0.y() - self.drag_start_point.y()) * self.deg_per_pixel.lat)
        self.calc_geo()
        self.repaint()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.calc_geo()
        self.repaint()

    def draw_tile(self, x, y, z, qp):
        tile = YandexSatellite().get_tile(self.central_point_tile.x() + x,
                                          self.central_point_tile.y() + y,
                                          z)

        tile_start = QPoint(x * TILE_SIZE + self.tile_shift.x() + self.central_point.x(),
                            y * TILE_SIZE + self.tile_shift.y() + self.central_point.y())
        qp.drawPixmap(tile_start,
                      tile)
        text = f'{self.central_point_tile.x() + x} {self.central_point_tile.y() + y}'

        qp.drawLine(tile_start, tile_start + QPoint(TILE_SIZE, 0))
        qp.drawLine(tile_start, tile_start + QPoint(0, TILE_SIZE))

        qp.setPen(QColor(255, 0, 0))
        qp.drawText(tile_start + QPoint(5, 15), text)

    def spiral(self, width, height, z, qp, function):
        x = y = 0
        dx = 0
        dy = -1
        for _ in range(max(width, height) ** 2):
            if (-width / 2 < x <= width / 2) and (-height / 2 < y <= height / 2):
                function(x, y, z, qp)
            if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
                dx, dy = -dy, dx
            x, y = x + dx, y + dy

    def draw_text(self, event, qp):
        self.spiral(self.tiles_count.x() + 2, self.tiles_count.y() + 2, self.zoom_level, qp, self.draw_tile)

        qp.setPen(QColor(255, 255, 255))

        # Draw aim
        qp.drawLine(self.central_point.x(), self.central_point.y() - 10, self.central_point.x(), self.central_point.y() - 3)
        qp.drawLine(self.central_point.x(), self.central_point.y() + 10, self.central_point.x(), self.central_point.y() + 3)
        qp.drawLine(self.central_point.x() - 10, self.central_point.y(), self.central_point.x() - 3, self.central_point.y())
        qp.drawLine(self.central_point.x() + 10, self.central_point.y(), self.central_point.x() + 3, self.central_point.y())

        # Draw bottom panel
        brush = QBrush(QColor(128, 128, 128, 200))
        qp.fillRect(0, self.window_height - 15, self.window_width, 15, brush)
        text = f'Zoom: z{self.zoom_level} ' \
               f'Geo: {self.central_point_geo.lat:.6f}°, {self.central_point_geo.lon:.6f}° ' \
               f'Central Tile: {self.central_point_tile.x()}, {self.central_point_tile.y()}'

        qp.drawText(3, self.window_height - 3, text)

    def closeEvent(self, event):
        SETTINGS.write_text(json.dumps({'zoom': self.zoom_level, 'lat': self.central_point_geo.lat, 'lon': self.central_point_geo.lon}))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    ex = MainWindow()

    sys.exit(app.exec_())
