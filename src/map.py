from functools import cached_property
import math

from .listmap import MapData
from .paper import Paper
from . import image


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
    BASEMAP = 'Topographic'
    SHADING = 'HillshadeGrey'
    MIN_DPI = 267.17615604
    LOD_BOUNDARY = 0.3

    def __init__(self, location, sheet, scale, zoom):
        self.location = location
        self.sheet = sheet
        self.scale = int(scale)
        self.datum = 'GDA94 MGA55'

        # Find the position of the current scale between adjacent scale halvings
        scale_factor = 2 ** (math.log(self.scale / 100000, 2) % 1)

        # Calculate the highest possible DPI for the current scale
        self.dpi = self.MIN_DPI * scale_factor
        # Adjust the point between adjacent scale halvings where the level of detail changes
        self.zoom = int(zoom) + (1 if scale_factor - 1 > self.LOD_BOUNDARY else 0)

    @cached_property
    def mapdata(self):
        """Get a map image at the optimum resolution for the selected scale"""
        size = [self.metres(d) for d in self.sheet.imagesize()]

        # TODO: Calculate level of detail dynamically
        mapdata = MapData(16, self.location.coordinates, size)
        basemap = mapdata.getlayer(self.BASEMAP)
        shading = mapdata.getlayer(self.SHADING)

        return image.layer(basemap, (shading, 0.15))

    def metres(self, size):
        """Convert a map dimension in mm to a real-world size in metres"""
        return self.scale * size / 1000
