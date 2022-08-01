from functools import cached_property
import re
import json

from .api import listapi, magapi
from .geometry import centroid


class Location():
    """A location on the map"""
    GEOMETRIES = {
        'point': 'esriGeometryPoint',
        'polygon': 'esriGeometryPolygon',
    }

    def __init__(self, description, translate=(0, 0)):
        self.description = description
        self.translate = translate

    @cached_property
    def coordinates(self):
        """Look up the location's EPSG:3857 (WGS 84) coordinates"""
        if self.description.startswith('geo:'):
            coord = self._from_decimaldegrees(self.description[4:])
        else:
            coord = self._from_placename(self.description)

        return [sum(i) for i in zip(coord, self.translate)]

    def _from_placename(self, placename):
        """Look up a location from a place name"""
        r = listapi.get('Public/SearchService/MapServer/find', params={
            'searchText': placename,
            'layers': '0',
        })

        for place in r.json()['results']:
            if place['value'].casefold() == placename.casefold():
                if place['geometryType'] == self.GEOMETRIES['point']:
                    return place['geometry']['x'], place['geometry']['y']
                if place['geometryType'] == self.GEOMETRIES['polygon']:
                    return centroid(place['geometry']['rings'][0])

        raise ValueError(f"Location '{self.description}' not found")

    def _from_decimaldegrees(self, coordinates):
        """Look up a location from decimal degree coordinates"""
        r = listapi.get('Utilities/Geometry/GeometryServer/fromGeoCoordinateString', params={
            'sr': '3857',
            'conversionType': 'DD',
            'strings': json.dumps([coordinates]),
        })

        return r.json()['coordinates'][0]

    @cached_property
    def latlon(self):
        """Get the location as a decimal degree latitude and longitude"""
        r = listapi.get('Utilities/Geometry/GeometryServer/toGeoCoordinateString', params={
            'sr': '3857',
            'conversionType': 'DD',
            'coordinates': json.dumps([self.coordinates]),
        })
        # Convert directional coordinates to absolute values
        matches = re.findall(r'([-.\d]+)([NSEW])', r.json()['strings'][0])
        return [v if d in 'NE' else f'-{v}' for v, d in matches]

    @property
    def uri(self):
        """Get a geo URI for the location"""
        return 'geo:{},{}'.format(*self.latlon)

    @cached_property
    def declination(self):
        """Get the location's magnetic declination"""
        lat, lon = self.latlon
        r = magapi.get('calculateDeclination', params={'lat1': lat, 'lon1': lon})
        return r.json()['result'][0]['declination']
