"""Module with functions to work with tiles"""
from collections import OrderedDict
from pathlib import Path
from random import randint

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPixmap
from requests import get

TILE_SIZE = 256


def total_tiles_on_zoom(zoom):
    """Return total tiles count available on selected zoom"""
    return QPoint(2 ** (zoom - 1),
                  2 ** (zoom - 1))


def deg_per_tile(zoom):
    """Get degreen per tile for selected zoom"""
    return LonLat(LonLat.TOTAL_LON / total_tiles_on_zoom(zoom).x(),
                  LonLat.TOTAL_LAT / total_tiles_on_zoom(zoom).y())


def tile_geo(tile_x, tile_y, tile_z):
    """Get tile geo coordinates"""
    dpt = deg_per_tile(tile_z)
    return LonLat(tile_x * dpt.lon - LonLat.TOTAL_LON / 2,
                  -tile_y * dpt.lat + LonLat.TOTAL_LAT / 2)


def download(url, destination):
    """Download file"""
    destination.parent.mkdir(parents=True, exist_ok=True)

    with open(destination, 'wb') as handle:
        response = get(url, stream=True)

        if not response.ok:
            print(url, response)
            return False

        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)
    return True


class LimitedSizeDict(OrderedDict):
    """Dict with limited size"""

    def __init__(self, *args, **kwds):
        self.size_limit = kwds.pop("size_limit", None)
        OrderedDict.__init__(self, *args, **kwds)
        self._check_size_limit()

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self._check_size_limit()

    def _check_size_limit(self):
        """Check dict size less than predefined size"""
        if self.size_limit is not None:
            while len(self) > self.size_limit:
                self.popitem(last=False)


TILE_CACHE = LimitedSizeDict(size_limit=200)


class LonLat:
    """Coordinates object"""
    TOTAL_LAT = 180
    TOTAL_LON = 360

    def __init__(self, lon: float, lat: float):
        self.lat = lat  # Latitude -90 — 90 (up-down from equator)
        self.lon = lon  # Longitude -180 — 180 (left-right)

    def __str__(self):
        return f'Lon: {self.lon}, Lat: {self.lat}'

    def __eq__(self, other):
        return self.lat == other.lat and self.lon == other.lon


class Map:
    """Tiles Map"""

    def __init__(self):
        self.map_id = 'map'

    def local_tile(self, x: int, y: int, z: int) -> Path:
        """Get local tile"""

    def get_tile_url(self, x: int, y: int, z: int) -> str:
        """Get tile url"""

    def get_tile(self, x: int, y: int, z: int) -> QPixmap:
        """Get tile from cache or download"""
        if x < 0 or y < 0 or z < 0:
            return QPixmap()

        tile_id = (self.map_id, x, y, z)
        cached_tile = TILE_CACHE.get(tile_id)
        if cached_tile:
            return cached_tile

        local_tile_file = self.local_tile(x, y, z)

        if not local_tile_file.exists():
            download(self.get_tile_url(x, y, z), local_tile_file)

        loaded_tile = QPixmap(str(local_tile_file))
        TILE_CACHE[tile_id] = loaded_tile

        return loaded_tile


class YandexSatellite(Map):
    """Tile implementation for Yandex Maps"""

    def __init__(self):
        super().__init__()
        self.map_id = 'yasat'

    def local_tile(self, x, y, z):
        return (CACHE / self.map_id / f'z{z}' / '0' / f'x{x}' / '0' / f'y{y}').with_suffix('.jpg')

    def get_tile_url(self, x, y, z):
        return f'https://sat0{randint(1, 4)}.maps.yandex.net/tiles' \
               f'?l=sat&scale=1&lang=ru_RU&x={x}&y={y}&z={z - 1}'
