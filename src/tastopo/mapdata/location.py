from functools import cached_property
import re
import json

from .api import listapi, magapi
from .geometry import centroid
from ..types import Point


class Location():
    """A location on the map"""

    GEOMETRIES = {
        'point': 'esriGeometryPoint',
        'polygon': 'esriGeometryPolygon',
    }

    """Specify a map location

    :param description: A string describing the location, by name or coordinates
    :param translate: Offset the centre of the location by a distance in km
    """
    def __init__(self, description: str, translate: Point = (0, 0)):
        self.description = description
        self.translate = translate

    @cached_property
    def coordinates(self) -> Point:
        """Look up the location's EPSG:3857 (WGS 84) coordinates

        :returns: The location's position as lat and lon coordinates, offset by the translate amount
        """
        if self.description.startswith('geo:'):
            coord = self._from_decimaldegrees(self.description[4:])
        else:
            coord = self._from_placename(self.description)

        return coord[0] + self.translate[0], coord[1] + self.translate[1]

    def _from_placename(self, placename: str) -> Point:
        """Look up a location from a place name

        :param placename: The name of the place to look up
        :returns: The location's position as lat and lon coordinates
        :raises ValueError: When the place can't be found
        """
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

    def _from_decimaldegrees(self, coordinates: str) -> Point:
        """Look up a location from decimal degree coordinates

        :param coordinates: The coordinates of a place as a single comma-separated string
        :returns: The location's position as lat and lon coordinates
        """
        r = listapi.get('Utilities/Geometry/GeometryServer/fromGeoCoordinateString', params={
            'sr': '3857',
            'conversionType': 'DD',
            'strings': json.dumps([coordinates]),
        })

        return r.json()['coordinates'][0]

    @cached_property
    def latlon(self) -> Point:
        """Get the location as a decimal degree latitude and longitude

        :returns: The location's position as lat and lon coordinates
        """
        r = listapi.get('Utilities/Geometry/GeometryServer/toGeoCoordinateString', params={
            'sr': '3857',
            'conversionType': 'DD',
            'coordinates': json.dumps([self.coordinates]),
        })
        # Convert directional coordinates to absolute values
        matches = re.findall(r'([-.\d]+)([NSEW])', r.json()['strings'][0])
        return tuple([v if d in 'NE' else f'-{v}' for v, d in matches])

    @property
    def uri(self) -> str:
        """Get URI that describes the location's position

        :returns: A geo URI for the selected location
        """
        return 'geo:{},{}'.format(*self.latlon)

    @cached_property
    def declination(self) -> float:
        """Get the location's current magnetic declination

        :returns: The magnetic declination offset in degrees
        """
        lat, lon = self.latlon
        r = magapi.get('calculateDeclination', params={'lat1': lat, 'lon1': lon})
        return r.json()['result'][0]['declination']
