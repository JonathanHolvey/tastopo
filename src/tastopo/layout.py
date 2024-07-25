from importlib import resources
from base64 import b64encode
from datetime import date
from typing import Mapping, Optional

from lxml import etree

from .map import Sheet, Image
from .mapdata import Location
from .types import Point


class SVG:
    """An XML wrapper for manipulating SVG documents"""

    NAMESPACES = {
        'svg': 'http://www.w3.org/2000/svg',
        'xlink': 'http://www.w3.org/1999/xlink',
    }

    def __init__(self, filepath: str, aliases: Mapping[str, str]):
        """Create an SVG document from a template file

        :param filepath: The path to the template file
        :param aliases: A map of xpath selectors to aliases for easy lookup of SVG elements
        """
        self.document = etree.parse(str(filepath))
        self.elements = self._alias(aliases)

    def _alias(self, paths: Mapping[str, str]) -> dict[str, etree._Element]:
        """Build a dictionary of element aliases

        :param paths: A list of xpaths aliases to store
        :retuns: A dictionary containing XML elements with their aliases as keys
        """
        elements = {}
        for key, path in paths.items():
            try:
                elements[key] = self.document.xpath(path, namespaces=self.NAMESPACES)[0]
            except IndexError:
                pass
        return elements

    def ns(self, fullname: str) -> str:
        """Convert a SVG namespace prefix into a full namespace URI

        :param fullname: The namespace and element name string, eg svg:text
        :returns: The full namespace URI, eg {http://www.w3.org/2000/svg}text
        """
        [ns, name] = fullname.split(':')
        namespace = self.NAMESPACES[ns]
        return f'{{{namespace}}}{name}'

    def get(self, key: str) -> etree._Element:
        """Get a previously selected element by key

        :param key: The alias of the SVG element to get
        :returns: The requested SVG element
        """
        return self.elements[key]

    def remove(self, key: str) -> None:
        """Remove a selected element from the document

        :param key: The alias of the SVG element to be removed
        """
        element = self.get(key)
        element.getparent().remove(element)

    def position(
        self,
        key: str,
        x: float,
        y: float,
        width: Optional[float] = None,
        height: Optional[float] = None
    ) -> None:
        """Set the size and position of a SVG node

        :param key: The alias of the SVG element to be positioned
        :param x: The horizontal position in SVG coordinates
        :param y: The vertical position in SVG coordinates
        :param width: Optionally, the width to set the element to
        :param height: Optionally, the height to set the element to
        """
        element = self.elements[key]
        if element.tag == self.ns('svg:g'):
            self._position_transform(element, x, y)
        else:
            self._position_absolute(element, x, y)
        if width and height:
            self._size(element, width, height)

    def _size(self, element: etree._Element, width: float, height: float) -> None:
        """Set the width and height attributes on an element

        :param element: The element to set the attributes on
        :param width: The width to set the element to
        :param height: The height to set the element to
        """
        element.attrib.update({'width': str(width), 'height': str(height)})

    def _position_absolute(self, element: etree._Element, x: float, y: float) -> None:
        """Set the positional attributes on an element

        :param x: The horizontal position in SVG coordinates
        :param y: The vertical position in SVG coordinates
        """
        element.attrib.update({'x': str(x), 'y': str(y)})

    def _position_transform(self, element, x, y):
        """Set the transform attribute on an element"""
        element.attrib['transform'] = f'translate({x} {y})'

    def line(self, parent_key: str, start: Point, end: Point) -> None:
        """Add a line element with a start and end point

        :param parent_key: The alias of the parent SVG element to add the line to
        :param start: The position of the start of the line in SVG coordinates
        :param end: The position of the end of the line in SVG coordinates
        """
        element = etree.SubElement(self.get(parent_key), 'line')
        element.attrib.update({
            'x1': str(start[0]),
            'y1': str(start[1]),
            'x2': str(end[0]),
            'y2': str(end[1]),
        })


class Layout:
    """A map sheet layout"""

    MAX_GRID_SPACING = 50
    INFO_ORDER = ['scale', 'grid', 'datum', 'declination', 'centre', 'size']
    GRID_SIZES = [200, 100, 50, 25, 10, 5, 4, 3, 2, 1, 0.5, 0.25, 0.1, 0.05, 0.025, 0.01]

    def __init__(self, sheet: Sheet, location: Location, image: Image, title: Optional[str] = None):
        """Create a map layout

        :param sheet: The map sheet to fit the layout to
        :param location: The location the map will show
        :param image: The map image to be shown on the sheet
        :param title: A title to use instead of the location description
        """
        self.sheet = sheet
        self.location = location
        self.image = image
        self.title = title or location.description.title()
        self.grid = False
        self.details = {
            'scale': f'1:{image.scale}',
            'datum': image.datum,
            'centre': location.uri,
            'size': sheet.spec.upper(),
            'declination': '{:+.1f}°'.format(self.location.declination)
        }
        self.date = date.today()

    def compose(self) -> etree._Element:
        """Set the layout's variable elements

        :returns: The SVG root element containing the composed layout
        """
        with resources.path(__package__ + '.templates', 'default.svg') as template_path:
            svg = SVG(str(template_path), {
                'image': '//svg:image[@id="map-data"]',
                'title': '//svg:text[@id="map-title"]',
                'info': '//svg:text[@id="map-info"]',
                'border': '//svg:rect[@id="map-border"]',
                'clip': '//svg:clipPath[@id="map-clip"]/svg:rect',
                'grid': '//svg:g[@id="map-grid"]',
                'logos': '//svg:g[@id="footer-logos"]',
                'text': '//svg:g[@id="footer-text"]',
                'date': '//svg:text[@id="date"]',
            })

        self._size(svg)
        if self.grid:
            self._drawgrid(svg)
        mapdata = 'data:image/png;base64,' + b64encode(self.image.mapdata).decode('utf-8')
        svg.get('image').attrib[svg.ns('xlink:href')] = mapdata
        svg.get('title').text = self.title
        svg.get('info').text = self.format_info()
        svg.get('date').text = self.date.strftime('%Y-%m-%d')

        return svg.document.getroot()

    # TODO: Add type hints for these private methods
    def _size(self, svg):
        """Prepare the template for the sheet size in use"""
        root = svg.document.getroot()
        width, height = self.sheet.dimensions()
        viewport = self.sheet.viewport()
        margin = self.sheet.MARGIN
        footer = self.sheet.FOOTER_HEIGHT + margin

        root.attrib['width'] = f'{width}mm'
        root.attrib['height'] = f'{height}mm'
        root.attrib['viewBox'] = f'0 0 {width} {height}'

        svg.position('image', *self.sheet.viewport(True))
        svg.position('border', *viewport)
        svg.position('clip', *viewport)
        svg.position('grid', *viewport)
        svg.position('logos', width - margin - 68, height - footer + 2.5)
        svg.position('text', margin + 0.2, height - footer + 3.5)

    def _drawgrid(self, svg):
        """Add a grid to the map template"""
        width, height = self.sheet.viewport()[2:]
        grid_size, km_size = self._gridsize(max(width, height), self.image.scale)
        spacing = grid_size * km_size

        for x in range(1, int(width / spacing) + 1):
            svg.line('grid', (x * spacing, 0), (x * spacing, height))
        for y in range(1, int(height / spacing) + 1):
            svg.line('grid', (0, height - y * spacing), (width, height - y * spacing))

        self.details['grid'] = (f'{grid_size}\u2009km' if grid_size >= 1
                                else f'{grid_size * 1000:.0f}\u2009m')

    def _gridsize(self, size, scale):
        """Select the best grid size for the map scale"""
        km = 1e6 / scale
        for grid in self.GRID_SIZES:
            if grid <= self.MAX_GRID_SPACING / km:
                break
        return grid, km

    def format_info(self) -> str:
        """Format map info details

        :returns: A string containing all the map info details, padded with spaces
        """
        items = [f'{k.upper()} {self.details[k]}' for k in self.INFO_ORDER if k in self.details]
        if 'version' in self.details:
            items.append(f'TasTopo {self.details["version"]}')
        return '    '.join(items)
