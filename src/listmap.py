import requests
from functools import cached_property
from urllib.parse import urljoin
import re
import json
import math
import threading
from queue import Queue

from . import image


class ListAPI(requests.Session):
    """A client for the ListMap ArcGIS API"""
    BASE_URL = 'https://services.thelist.tas.gov.au/arcgis/rest/services/'
    DEFAULT_PARAMS = {
        'f': 'json',
    }

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.BASE_URL, url)
        params = {**self.DEFAULT_PARAMS, **kwargs.pop('params', {})}

        response = super().request(method, url, *args, params=params, **kwargs)
        response.raise_for_status()
        return response


class Location():
    """A location on the map"""
    def __init__(self, description):
        self.api = ListAPI()
        self.description = description

    @cached_property
    def coordinates(self):
        if self.description.startswith('geo:'):
            return self._from_decimaldegrees(self.description[4:])
        return self._from_placename(self.description)

    def _from_placename(self, placename):
        """Look up a location from a place name"""
        r = self.api.get('Public/PlacenamePoints/MapServer/find', params={
            'searchText': placename,
            'layers': '0',
        })

        for place in r.json()['results']:
            if place['value'].casefold() == placename.casefold():
                return place['geometry']['x'], place['geometry']['y']

        raise ValueError(f"Location '{self.description}' not found")

    def _from_decimaldegrees(self, coordinates):
        """Look up a location from decimal degree coordinates"""
        r = self.api.get('Utilities/Geometry/GeometryServer/fromGeoCoordinateString', params={
            'sr': '3857',
            'conversionType': 'DD',
            'strings': json.dumps([coordinates]),
        })

        return r.json()['coordinates'][0]

    @cached_property
    def uri(self):
        """Get a geo URI for the location"""
        r = self.api.get('Utilities/Geometry/GeometryServer/toGeoCoordinateString', params={
            'sr': '3857',
            'conversionType': 'DD',
            'coordinates': json.dumps([self.coordinates]),
        })

        # Convert directional coordinates to absolute values
        matches = re.findall(r'([-.\d]+)([NSEW])', r.json()['strings'][0])
        coordinates = [v if d in 'NE' else f'-{v}' for v, d in matches]
        return 'geo:{},{}'.format(*coordinates)


class Layer:
    """Image tile metadata for a map layer"""
    def __init__(self, name):
        self.api = ListAPI()
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
        return self.properties['tileInfo']['lods'][level]['resolution']


class TileGrid:
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


class Tile:
    """A tile from the map service"""
    def __init__(self, grid, layer, position):
        self.api = ListAPI()
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
