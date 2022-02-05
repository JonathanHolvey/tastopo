from functools import cached_property

from .api import listapi


class Layer:
    """Image tile metadata for a map layer"""
    def __init__(self, name):
        self.api = listapi
        self.name = name

    @cached_property
    def properties(self):
        """Fetch layer properties from the API"""
        r = self.api.get(f'Basemaps/{self.name}/MapServer')
        return r.json()

    @property
    def origin(self):
        """Get the coordinates of the first tile"""
        point = self.properties['tileInfo']['origin']
        return point['x'], point['y']

    @property
    def tilesize(self):
        """Get the pixel size of a single tile"""
        return self.properties['tileInfo']['rows']

    def resolution(self, level):
        """Get the tile resolution for a certain level of detail"""
        level = min(level, len(self.properties['tileInfo']['lods']) - 1)
        return self.properties['tileInfo']['lods'][level]['resolution']


class Tile:
    """A tile from the map service"""
    def __init__(self, grid, layer, position):
        self.api = listapi
        self.grid = grid
        self.layer = layer
        self.position = position

    def fetch(self):
        """Fetch the image data"""
        col, row = [abs(p) for p in self.position]
        r = self.api.get(f'Basemaps/{self.layer.name}/MapServer/tile/{self.grid.level}/{row}/{col}')
        self.type = r.headers['Content-Type']
        self.data = r.content

    def __bytes__(self):
        """Cast to bytes"""
        return self.data
