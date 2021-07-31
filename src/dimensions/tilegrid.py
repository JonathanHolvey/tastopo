import math


class TileGrid:
    """Calculate the dimensions of a grid of map tiles"""
    def __init__(self, layer, level, centre, size):
        self.layer = layer
        self.level = level
        self.centre = centre
        self.size = size

    def tiles(self):
        """Get a list of tile coordinates to cover a real-world map area"""
        start, shape = self.grid()
        return [(start[0] + col, start[1] + row)
                for row in range(shape[1], 0, -1) for col in range(shape[0])]

    def grid(self):
        """Get the start tile and shape of a grid of tiles"""
        x1, y1 = self.bbox()[:2]
        overflow = self.overflow()

        start = math.floor(self.tileunits(x1)), math.floor(self.tileunits(y1))
        shape = (
            round(self.tileunits(self.size[0]) + sum(overflow[0])),
            round(self.tileunits(self.size[1]) + sum(overflow[1])),
        )

        return start, shape

    def bbox(self):
        """Get the coordinates of the corners bounding the map area"""
        x1 = self.centre[0] - self.layer.origin[0] - self.size[0] / 2
        x2 = self.centre[0] - self.layer.origin[0] + self.size[0] / 2
        y1 = self.centre[1] - self.layer.origin[1] - self.size[1] / 2
        y2 = self.centre[1] - self.layer.origin[1] + self.size[1] / 2
        return x1, y1, x2, y2

    def tileunits(self, size):
        """Convert a real-world distance in metres to a number of tile widths"""
        resolution = self.layer.resolution(self.level)
        return size / (resolution * self.layer.tilesize)

    def pixelsize(self):
        """Get the grid dimensions in pixels"""
        resolution = self.layer.resolution(self.level)
        return [round(s / resolution) for s in self.size]

    def overflow(self):
        """Get the proportion of a tile that the grid extends beyond the map area by on each side"""
        x1, y1, x2, y2 = self.bbox()

        left = self.tileunits(x1) % 1
        bottom = self.tileunits(y1) % 1
        top = 1 - self.tileunits(y2) % 1
        right = 1 - self.tileunits(x2) % 1
        return (left, right), (top, bottom)

    def origin(self):
        """Get the position of the first tile in pixels"""
        overflow = self.overflow()

        left = -1 * round(overflow[0][0] * self.layer.tilesize)
        top = -1 * round(overflow[1][0] * self.layer.tilesize)
        return left, top
