from functools import cached_property
import math
import threading
from queue import Queue

from .dimensions import Paper
from .dimensions import TileGrid
from .mapdata import Layer, Tile
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
    LOD_BOUNDARY = 0.6
    BASE_LOD = 12

    def __init__(self, location, sheet, scale, zoom):
        self.location = location
        self.sheet = sheet
        self.scale = int(scale)
        self.zoom = int(zoom)
        self.datum = 'GDA94 MGA55'

    @cached_property
    def mapdata(self):
        """Get a map image"""
        size = [self.metres(d) for d in self.sheet.imagesize()]

        mapdata = MapData(self.location.coordinates, size)
        basemap = mapdata.getlayer(self.BASEMAP, self.level)
        shading = mapdata.getlayer(self.SHADING, self.level - 2)

        return image.layer(basemap, (shading, 0.12))

    @property
    def level(self):
        """Calculate the level of detail for the selected scale"""
        level = math.log((self.scale - 1) / 100000, 2)
        # Find the position of the current scale between adjacent scale halvings
        scale_factor = (2 ** (level % 1)) % 1
        # Adjust the point between adjacent scale halvings where the level of detail changes
        zoom = round(0.5 + self.LOD_BOUNDARY - scale_factor) - self.zoom
        return max(0, self.BASE_LOD - math.floor(level) + zoom)

    def metres(self, size):
        """Convert a map dimension in mm to a real-world size in metres"""
        return self.scale * size / 1000


class MapData:
    """A composite image built from multiple tiles"""
    MAX_THREADS = 8

    def __init__(self, centre, size):
        self.centre = centre
        self.size = size

    def getlayer(self, name, level):
        """Fetch and combine all tiles"""
        layer = Layer(name)
        grid = TileGrid(layer, level, self.centre, self.size)
        queue = Queue()

        tilelist = grid.tiles()
        tiles = [Tile(grid, layer, position) for position in tilelist]
        for tile in tiles:
            queue.put(tile)

        for _ in range(min(self.MAX_THREADS, len(tiles))):
            worker = threading.Thread(target=self._job, args=(queue,))
            worker.start()

        queue.join()
        return image.stitch(tiles, grid.pixelsize(), grid.origin())

    def _job(self, queue):
        """Consume a single tile-fetching job from the queue"""
        while not queue.empty():
            tile = queue.get()
            tile.fetch()
            queue.task_done()
