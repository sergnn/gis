from math import sin, pi, atanh, atan, exp, asin, log, tan

from PyQt5.QtCore import QPointF

from utils.tiles import LonLat


class Projection:
    def to_pixel(self, coordinates: LonLat):
        pass


class MercatorProjection(Projection):
    VRadiusA = 6378137
    VRadiusB = 6356752
    MerkElipsK = 0.000000001
    fexct = (VRadiusA * VRadiusA - VRadiusB * VRadiusB) ** (1 / 2) / VRadiusA

    def to_pixel(self, coordinates: LonLat):
        x = (0.5 + coordinates.lat / 360)
        z = sin(coordinates.lon * pi / 180)
        c = (1 / (2 * pi))
        y = (0.5 - c * (atanh(z) - self.fexct * atanh(self.fexct * z)))

        return QPointF(x, y)

    def to_geo(self, point: QPointF) -> LonLat:
        x = (point.x() - 0.5) * 360

        if point.y() > 0.5:
            yy = (point.y() - 0.5)
        else:
            yy = (0.5 - point.y())

        yy = yy * (2 * pi)
        zu = 2 * atan(exp(yy)) - pi / 2
        e_y = exp(2 * yy)
        y = zu * (180 / pi)
        while True:
            zum1 = zu
            v_sin = sin(zum1)
            zu = asin(1 - (1 + v_sin) * pow((1 - self.fexct * v_sin) / (1 + self.fexct * v_sin), self.fexct) / e_y)
            if abs(zum1 - zu) < self.MerkElipsK:
                break

        if point.y() > 0.5:
            y = -zu * 180 / pi
        else:
            y = zu * 180 / pi
        return LonLat(x, y)

    def y2lat(self, a):
        return 180.0 / pi * (2.0 * atan(exp(a * pi / 180.0)) - pi / 2.0)

    def lat2y(self, a):
        return 180.0 / pi * log(tan(pi / 4.0 + a * (pi / 180.0) / 2.0))
