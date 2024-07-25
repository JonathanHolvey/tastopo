from functools import cached_property
import math
import threading
from queue import Queue

from . import image
from .dimensions import Paper
from .dimensions import TileGrid
from .mapdata import Layer, Tile, Location
from .types import Point, BoxSize, Box


class Sheet(Paper):
    MIN_PAPER_SIZE = 5
    IMAGE_BLEED = 2
    FOOTER_HEIGHT = 15
    MARGIN = 6

    def __init__(self, size: str, rotated: bool = False):
        """Create a map sheet

        :param size: The paper size to use
        :param rotated: Set the orientation of the sheet; portrait when True, landscape otherwise
        """
        super().__init__(size)
        self.rotated = rotated
        if self.size > self.MIN_PAPER_SIZE:
            raise ValueError(f'Paper size must not be smaller than A{self.MIN_PAPER_SIZE}')

    def dimensions(self) -> BoxSize:
        """Get the sheet dimensions while considering the sheet orientation.

        Landscape is used when self.rotated is not True
        :returns: The width and height in mm
        """
        dimensions = super().dimensions()
        return dimensions[::-1] if not self.rotated else dimensions

    def imagesize(self) -> BoxSize:
        """Get the size of the map image for the selected paper size

        :returns: The width and height of the image in mm
        """
        return self.viewport(True)[-2:]

    def viewport(self, with_bleed: bool = False) -> Box:
        """Get the dimensions and position of the map image for the selected paper size

        :param with_bleed: When True, the dimensions include extra width and height so the image overlaps the viewport
        :returns: The width, height, and x and y offsets in mm
        """
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

    def __init__(self, location: Location, sheet: Sheet, scale: float, zoom: float):
        """Create a ListMap map image for a specifiec region

        :param location: The location to centre the image on
        :param sheet: The map sheet the image is to fit
        :param scale: The map scale to use, as a ratio 1:scale
        :param zoom: The LOD offset to use, relative to BASE_LOD
        """
        self.location = location
        self.sheet = sheet
        self.scale = int(scale)
        self.zoom = int(zoom)
        self.datum = 'GDA94 MGA55'

    @cached_property
    def mapdata(self) -> bytes:
        """Get a map image

        :returns: The map image data
        """
        w, h = self.sheet.imagesize()
        size = self.metres(w), self.metres(h)

        mapdata = MapData(self.location.coordinates, size)
        basemap = mapdata.getlayer(self.BASEMAP, self.level)
        shading = mapdata.getlayer(self.SHADING, self.level - 2)

        return image.layer(basemap, (shading, 0.12))

    @property
    def level(self) -> int:
        """Calculate the level of detail for the selected scale

        :returns: The absolute LOD for the current map image
        """
        level = math.log((self.scale - 1) / 100000, 2)
        # Find the position of the current scale between adjacent scale halvings
        scale_factor = (2 ** (level % 1)) % 1
        # Adjust the point between adjacent scale halvings where the level of detail changes
        zoom = round(0.5 + self.LOD_BOUNDARY - scale_factor) - self.zoom
        return max(0, self.BASE_LOD - math.floor(level) + zoom)

    def metres(self, size: float) -> float:
        """Convert a map dimension in mm to a real-world size

        :param size: The dimension to convert
        :returns: The converted value, in metres
        """
        return self.scale * size / 1000


class MapData:
    """A composite image built from multiple tiles"""
    MAX_THREADS = 8

    def __init__(self, centre: Point, size: BoxSize):
        self.centre = centre
        self.size = size

    def getlayer(self, name: str, level: int) -> bytes:
        """Fetch and combine all tiles

        :param name: A name to give the layer
        :param level: The LOD level to fetch the layer image at
        :returns: The map image data
        """
        layer = Layer(name)
        grid = TileGrid(layer, level, self.centre, self.size)
        queue = Queue[Tile]()

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
