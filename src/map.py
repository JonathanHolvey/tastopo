from functools import cached_property

from .listmap import TiledData
from .paper import Paper


class Sheet(Paper):
    MIN_PAPER_SIZE = 5
    IMAGE_BLEED = 2
    FOOTER_HEIGHT = 15
    MARGIN = 6

    def __init__(self, size, rotated=False):
        super().__init__(size)
        self.rotated = rotated
        if self.size > self.MIN_PAPER_SIZE:
            raise ValueError(f'Paper size must not be smaller than A{self.MIN_PAPER_SIZE}')

    def dimensions(self):
        """Get the sheet dimensions; landscape by default"""
        dimensions = super().dimensions()
        return reversed(dimensions) if not self.rotated else dimensions

    def imagesize(self):
        """Get the required map with and height in mm"""
        return self.viewport(True)[-2:]

    def viewport(self, with_bleed=False):
        """Get the position, width and height of the map view in mm"""
        bleed = self.IMAGE_BLEED if with_bleed else 0
        width, height = self.dimensions()

        x = self.MARGIN - bleed
        y = x
        width -= 2 * x
        height -= x + self.MARGIN + self.FOOTER_HEIGHT - bleed

        return x, y, width, height


class Image():
    """A ListMap map image"""
    BASE_MAP = 'Topographic'
    RES_FACTOR = 1.78117  # Maximise image resolution at 1:25000 scale
    IMAGE_DPI = 150

    def __init__(self, location, sheet, scale, zoom):
        self.location = location
        self.sheet = sheet
        self.scale = int(scale)
        self.zoom = int(zoom)
        self.datum = 'GDA94 MGA55'

    @cached_property
    def mapdata(self):
        """Get a map image at the optimum resolution for the selected scale and size"""
        zoom = 2 ** self.zoom
        scale = self.scale / self.RES_FACTOR * zoom
        size = [self.pixels(d * self.RES_FACTOR / zoom) for d in self.sheet.imagesize()]

        layers = TiledData(scale, self.IMAGE_DPI, self.location.coordinates, size)
        return layers.getlayer(self.BASE_MAP)

    def pixels(self, size):
        """Convert a physical size in mm into pixels"""
        return round(size * self.IMAGE_DPI / 25.4)
