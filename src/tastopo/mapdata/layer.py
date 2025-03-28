from __future__ import annotations
from functools import cached_property
from typing import Mapping, SupportsBytes, TYPE_CHECKING

from .api import listapi
if TYPE_CHECKING:
    from ..dimensions import TileGrid
    from ..types import Point


class Layer:
    """Image tile metadata for a map layer"""

    def __init__(self, name: str):
        """Create a named map layer

        :param name: The name to give the layer
        """
        self.api = listapi
        self.name = name

    @cached_property
    def properties(self) -> Mapping:
        """Fetch layer properties from the API

        :returns: A JSON object containing the layer's details
        """
        r = self.api.get(f'Basemaps/{self.name}/MapServer')
        return r.json()

    @property
    def origin(self) -> Point:
        """Get the coordinates of the first tile

        :returns: The real-world coordinates of the first map tile
        """
        point = self.properties['tileInfo']['origin']
        return point['x'], point['y']

    @property
    def tilesize(self) -> int:
        """Get the pixel size of a single tile

        :returns: The size of a tile in pixels
        """
        return self.properties['tileInfo']['rows']

    def resolution(self, level: int) -> float:
        """Get the tile resolution for a certain level of detail

        :param level: The LOD to query the resolution for
        :returns: The resolution in pixels per metre
        """
        level = min(level, len(self.properties['tileInfo']['lods']) - 1)
        return self.properties['tileInfo']['lods'][level]['resolution']


class Tile(SupportsBytes):
    """A tile from the map service"""

    def __init__(self, grid: TileGrid, layer: Layer, position: Point):
        """Create a single map tile

        :param grid: The grid the tile is a member of
        :param layer: The map layer the grid represents
        :param position: The coordinates of the tile in the grid
        """
        self.api = listapi
        self.grid = grid
        self.layer = layer
        self.position = position

    def fetch(self) -> None:
        """Fetch the image data"""
        col, row = [abs(p) for p in self.position]
        r = self.api.get(f'Basemaps/{self.layer.name}/MapServer/tile/{self.grid.level}/{row}/{col}')
        self.type = r.headers['Content-Type']
        self.data = r.content

    def __bytes__(self) -> bytes:
        """Get the map data as bytes"""
        return self.data
