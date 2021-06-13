import json

from api import ListAPI, cached_property
from paper import Paper


class Sheet(Paper):
    PRINT_DPI = 150
    IMAGE_BLEED = 2
    MARGIN_BOTTOM = 18
    MARGIN_SIDE = 4

    def __init__(self, size, rotated=False):
        super().__init__(size)
        self.rotated = rotated

    def dimensions(self):
        """Get the sheet dimensions; landscape by default"""
        dimensions = super().dimensions()
        return reversed(dimensions) if not self.rotated else dimensions

    def imagesize(self):
        """Get the required map with and height in pixels"""
        x, y, width, height = self.viewport(True)
        return self.pixels(width), self.pixels(height)

    def viewport(self, with_bleed=False):
        """Get the position, width and height of the map view in mm"""
        bleed = self.IMAGE_BLEED if with_bleed else 0
        width, height = self.dimensions()

        x = self.MARGIN_SIDE - bleed
        y = x
        width -= 2 * x
        height -= x + self.MARGIN_BOTTOM - bleed

        return x, y, width, height

    def pixels(self, size):
        """Convert a physical size in mm into pixels"""
        return size * self.PRINT_DPI / 25.4


class Location():
    """Find the coordinates of a map location"""
    def __init__(self, description):
        self.api = ListAPI()
        self.description = description

    @cached_property
    def coordinates(self):
        if ':' in self.description and self.description.split(':')[0] == 'geo':
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

        raise Exception(f'Location {self.description} not found')

    def _from_decimaldegrees(self, coordinates):
        """Look up a location from decimal degree coordinates"""
        r = self.api.get('Utilities/Geometry/GeometryServer/fromGeoCoordinateString', params={
            'sr': '3857',
            'conversionType': 'DD',
            'strings': json.dumps([coordinates]),
        })

        return r.json()['coordinates'][0]


class Image():
    """A ListMap map image"""
    BASE_MAP = 'Topographic'

    def __init__(self, location, sheet, scale):
        self.api = ListAPI()
        self.location = location
        self.sheet = sheet
        self.scale = scale

    @cached_property
    def mapdata(self):
        return self._maplayer(self.BASE_MAP)

    def _maplayer(self, name):
        """Fetch a map layer image in PNG format"""
        r = self.api.get(f'Basemaps/{name}/MapServer/export', params={
            'f': 'image',
            'format': 'png',
            'bbox': '{0},{1},{0},{1}'.format(*self.location.coordinates),
            'mapScale': self.scale,
            'size': '{},{}'.format(*self.sheet.imagesize()),
            'dpi': self.sheet.PRINT_DPI,
        })
        return r.content
