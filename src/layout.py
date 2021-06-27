from importlib import resources
import math

from base64 import b64encode
from lxml import etree


class SVG:
    """An XML wrapper for manipulating SVG documents"""
    NAMESPACES = {
        'svg': 'http://www.w3.org/2000/svg',
        'xlink': 'http://www.w3.org/1999/xlink',
    }

    def __init__(self, filepath, aliases):
        self.document = etree.parse(str(filepath))
        self.elements = self._alias(aliases)

    def _alias(self, paths):
        """Build a dictionary of element aliases"""
        elements = {}
        for key, path in paths.items():
            try:
                elements[key] = self.document.xpath(path, namespaces=self.NAMESPACES)[0]
            except IndexError:
                pass
        return elements

    def ns(self, fullname):
        """Convert a SVG namespace prefix into a full namespace URI"""
        [ns, name] = fullname.split(':')
        namespace = self.NAMESPACES[ns]
        return f'{{{namespace}}}{name}'

    def get(self, key):
        """Get a previously selected element by key"""
        return self.elements[key]

    def position(self, key, x, y, width=None, height=None):
        """Set the size and position of a SVG node"""
        element = self.elements[key]
        if element.tag == self.ns('svg:g'):
            self._position_transform(element, x, y)
        else:
            self._position_absolute(element, x, y, width, height)

    def _position_absolute(self, element, x, y, width, height):
        """Set the positional attributes on an element"""
        element.attrib.update({
            'x': str(x),
            'y': str(y),
            'width': str(width),
            'height': str(height),
        })

    def _position_transform(self, element, x, y):
        """Set the transform attribute on an element"""
        element.attrib['transform'] = f'translate({x} {y})'

    def line(self, parent_key, start, end):
        """Add a line element with a start and end point"""
        element = etree.SubElement(self.get(parent_key), 'line')
        element.attrib.update({
            'x1': str(start[0]),
            'y1': str(start[1]),
            'x2': str(end[0]),
            'y2': str(end[1]),
        })


class Layout:
    MIN_GRID_SPACING = 30
    INFO_ORDER = ['scale', 'grid', 'datum', 'centre', 'size', 'version']

    """A map sheet layout"""
    def __init__(self, sheet, location, image, title=None):
        self.sheet = sheet
        self.location = location
        self.image = image
        self.title = title or location.description.title()
        self.grid = False
        self.details = {
            'scale': f'1:{image.scale}',
            'size': sheet.size,
        }

    def compose(self):
        """Set the layout's variable elements"""
        with resources.path(__package__, 'template.svg') as template_path:
            svg = SVG(template_path, {
                'image': '//svg:image[@id="map-data"]',
                'title': '//svg:text[@id="map-title"]',
                'border': '//svg:rect[@id="map-border"]',
                'clip': '//svg:clipPath[@id="map-clip"]/svg:rect',
                'grid': '//svg:g[@id="map-grid"]',
                'logos': '//svg:g[@id="footer-logos"]',
                'text': '//svg:g[@id="footer-text"]',
                'info': '//svg:g[@id="map-info"]',
            })

        self._size(svg)
        mapdata = 'data:image/png;base64,' + b64encode(self.image.mapdata).decode('utf-8')
        svg.get('image').attrib[svg.ns('xlink:href')] = mapdata
        svg.get('title').text = self.title
        if self.grid:
            self._drawgrid(svg)

        return svg.document.getroot()

    def _size(self, svg):
        """Prepare the template for the sheet size in use"""
        root = svg.document.getroot()
        width, height = self.sheet.dimensions()
        viewport = self.sheet.viewport()
        margin = self.sheet.MARGIN
        footer = self.sheet.FOOTER_HEIGHT

        root.attrib['width'] = f'{width}mm'
        root.attrib['height'] = f'{height}mm'
        root.attrib['viewBox'] = f'0 0 {width} {height}'

        svg.position('image', *self.sheet.viewport(True))
        svg.position('border', *viewport)
        svg.position('clip', *viewport)
        svg.position('grid', *viewport)
        svg.position('logos', width - margin - 73.5, height - footer - 1.5)
        svg.position('text', margin + 0.2, height - footer - 0.5)

    def _drawgrid(self, svg):
        """Add a grid to the map template"""
        width, height = self.sheet.viewport()[2:]
        km_size = 1e6 / int(self.image.scale)
        grid_size = math.ceil(max(self.MIN_GRID_SPACING, km_size) / km_size)
        spacing = grid_size * km_size

        for x in range(1, int(width / spacing) + 1):
            svg.line('grid', (x * spacing, 0), (x * spacing, height))
        for y in range(1, int(height / spacing) + 1):
            svg.line('grid', (0, height - y * spacing), (width, height - y * spacing))        

        self.details['grid'] = f'{grid_size}km'

    def format_info(self):
        """Format map info details"""
        version = self.details.pop('version', None)
        items = [f'{k.upper()} {v}' for k, v in self.details.items()]
        if version:
            items.append(f'TasTopo {version}')
        return '    '.join(items)
