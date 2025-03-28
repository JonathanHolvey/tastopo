import math

from ..mapdata import Layer
from ..types import Point, BoxSize


class TileGrid:
    """Calculate the dimensions of a grid of map tiles"""

    def __init__(self, layer: Layer, level: int, centre: Point, size: BoxSize):
        """Create a new tile grid

        :param layer: The map layer to the grid is for
        :param level: The LOD level of the grid image
        :param centre: The coordinates of the centre of the grid
        :param size: The width and height of the grid
        """
        self.layer = layer
        self.level = level
        self.centre = centre
        self.size = size

    def tiles(self) -> list[Point]:
        """Get a list of tile coordinates to cover a real-world map area

        :returns: A list of grid tile coordinates
        """
        start, shape = self.grid()
        return [(start[0] + col, start[1] + row)
                for row in range(int(shape[1]), 0, -1) for col in range(int(shape[0]))]

    def grid(self) -> tuple[Point, BoxSize]:
        """Get the grid definition

        :returns: The coordinates of the start of the grid, and its size
        """
        x1, y1 = self.bbox()[:2]
        overflow = self.overflow()

        start = math.floor(self.tileunits(x1)), math.floor(self.tileunits(y1))
        shape = (
            round(self.tileunits(self.size[0]) + sum(overflow[0])),
            round(self.tileunits(self.size[1]) + sum(overflow[1])),
        )

        return start, shape

    def bbox(self) -> tuple[float, float, float, float]:
        """Get the coordinates of the corners bounding the map area

        :returns: The coordinates of the top left and bottom right corners of the grid
        """
        x1 = self.centre[0] - self.layer.origin[0] - self.size[0] / 2
        x2 = self.centre[0] - self.layer.origin[0] + self.size[0] / 2
        y1 = self.centre[1] - self.layer.origin[1] - self.size[1] / 2
        y2 = self.centre[1] - self.layer.origin[1] + self.size[1] / 2
        return x1, y1, x2, y2

    def tileunits(self, size: float) -> float:
        """Convert a real-world distance in metres to a number of tile widths

        :param size: The dimension to be converted
        :returns: The converted value in metres
        """
        resolution = self.layer.resolution(self.level)
        return size / (resolution * self.layer.tilesize)

    def pixelsize(self) -> BoxSize:
        """Get the grid dimensions in pixels

        :returns: The size of the grid in pixels
        """
        resolution = self.layer.resolution(self.level)
        w, h = self.size
        return round(w / resolution), round(h / resolution)

    def overflow(self) -> tuple[tuple[float, float], tuple[float, float]]:
        """Get the proportion of a tile that the grid extends beyond the map area by on each side

        :returns: The overflow amount on each side, grouped by horizontal and vertical dimensions
        """
        x1, y1, x2, y2 = self.bbox()

        left = self.tileunits(x1) % 1
        bottom = self.tileunits(y1) % 1
        top = 1 - self.tileunits(y2) % 1
        right = 1 - self.tileunits(x2) % 1
        return (left, right), (top, bottom)

    def origin(self) -> Point:
        """Get the pixel position of the first tile, relative to the start of the map area

        :returns: The position of the first tile, in pixels
        """
        overflow = self.overflow()

        left = -1 * round(overflow[0][0] * self.layer.tilesize)
        top = -1 * round(overflow[1][0] * self.layer.tilesize)
        return left, top
