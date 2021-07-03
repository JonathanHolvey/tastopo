import json
import re

from .api import ListAPI, cachedproperty
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


class Location():
    """Find the coordinates of a map location"""
    def __init__(self, description):
        self.api = ListAPI()
        self.description = description

    @cachedproperty
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

    @cachedproperty
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


class Image():
    """A ListMap map image"""
    BASE_MAP = 'Topographic'
    IMAGE_DPI = 150
    ZOOM_FACTOR = 1.78117  # Maximise image resolution at 1:25000 scale

    def __init__(self, location, sheet, scale):
        self.api = ListAPI()
        self.location = location
        self.sheet = sheet
        self.scale = int(scale)
        self.datum = 'GDA94 MGA55'

    @cachedproperty
    def mapdata(self):
        scale = self.scale / self.ZOOM_FACTOR
        width, height = [self.pixels(s) for s in self.sheet.imagesize()]

        return self.getlayer(self.BASE_MAP, scale, width, height)

    def pixels(self, size):
        """Convert a physical size in mm into pixels"""
        return size * self.IMAGE_DPI * self.ZOOM_FACTOR / 25.4

    def getlayer(self, name, scale, width, height):
        """Fetch a map layer image in PNG format"""
        r = self.api.get(f'Basemaps/{name}/MapServer/export', params={
            'f': 'image',
            'format': 'png',
            'bbox': '{0},{1},{0},{1}'.format(*self.location.coordinates),
            'mapScale': scale,
            'size': f'{width},{height}',
            'dpi': self.IMAGE_DPI,
        })
        return r.content
