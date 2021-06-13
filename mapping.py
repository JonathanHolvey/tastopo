import json

from api import ListAPI, cached_property

MAP_SHEETS = [{
    'size': 'a4',
    'orientation': 'landscape',
    'viewport': (286.86, 185.67),
}]


class Sheet:
    PRINT_DPI = 150
    IMAGE_BLEED = 2

    def __init__(self, config):
        self.config = config

    def mapsize(self):
        """Get the required map with and height in pixels"""
        resolution = self.PRINT_DPI / 25.4
        return [round(resolution * (i + 2 * self.IMAGE_BLEED)) for i in self.config['viewport']]


def get_sheet(size, orientation):
    """Select a map sheet by size and orientation"""
    for config in MAP_SHEETS:
        if config['size'] == size.lower() and config['orientation'] == orientation.lower():
            return Sheet(config)


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
            'size': '{},{}'.format(*self.sheet.mapsize()),
            'dpi': self.sheet.PRINT_DPI,
        })
        return r.content
