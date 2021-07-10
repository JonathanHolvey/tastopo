import requests
from functools import cached_property
from urllib.parse import urljoin
import re
import json
import math

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
    """Find the coordinates of a map location"""
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


class MapData:
    """Get map data for a certain area"""
    MAX_RESOLUTION = 4098

    def __init__(self, scale, dpi, centre, size):
        self.api = ListAPI()
        self.scale = scale
        self.dpi = dpi
        self.centre = centre
        self.size = size

    def getlayer(self, name):
        """Fetch an image for a layer"""
        return self._fetch(name, self.centre, self.size)

    def _fetch(self, name, centre, size):
        """Fetch an image for a specified layer, centre and size"""
        if any(d > self.MAX_RESOLUTION for d in size):
            raise ValueError(f'Image dimensions exceed API limit of {self.MAX_RESOLUTION} pixels')

        r = self.api.get(f'Basemaps/{name}/MapServer/export', params={
            'f': 'image',
            'format': 'png24',
            'bbox': '{0},{1},{0},{1}'.format(*centre),
            'mapScale': self.scale,
            'size': '{},{}'.format(*size),
            'dpi': self.dpi,
        })
        return r.content


class TiledData(MapData):
    TILE_SIZE = 500

    def getlayer(self, name):
        """Fetch and combine all tiles"""
        columns, rows = self.shape()
        tiles = []
        for row in reversed(range(rows)):
            for column in range(columns):
                tiles.append(self._fetch(name, **self.tileparams(column, row)))

        return image.stitch(tiles, self.size)

    def shape(self):
        """Get the number of columns and rows in the tile grid"""
        return [math.ceil(d / self.TILE_SIZE) for d in self.size]

    def metres(self, pixels):
        """Convert a pixel size into a real-world size in metres"""
        return self.scale * pixels / (self.dpi * 1000/25.4)

    def tileparams(self, column, row):
        """Calculate the pixel size and coordinate centre of a tile"""
        imagewidth, imageheight = self.size
        image_x, image_y = self.centre

        width = min(imagewidth, self.TILE_SIZE * (column + 1)) - self.TILE_SIZE * column
        height = min(imageheight, self.TILE_SIZE * (row + 1)) - self.TILE_SIZE * row
        x = image_x + self.metres(imagewidth / -2 + self.TILE_SIZE * column + width / 2)
        y = image_y + self.metres(imageheight / -2 + self.TILE_SIZE * row + height / 2)

        return {'centre': (x, y), 'size': (width, height)}
