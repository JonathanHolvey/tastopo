from importlib import resources

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
            except AttributeError:
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

    def position(self, key, x, y, width, height):
        """Set the size and position of a SVG node"""
        self.elements[key].attrib['x'] = str(x)
        self.elements[key].attrib['y'] = str(y)
        self.elements[key].attrib['width'] = str(width)
        self.elements[key].attrib['height'] = str(height)


class Layout(SVG):
    """A map sheet layout"""
    def __init__(self, sheet):
        with resources.path(__package__, 'template.svg') as template_path:
            super().__init__(template_path, {
                'image': '//svg:image[@id="map-data"]',
                'title': '//svg:text[@id="map-title"]',
                'border': '//svg:rect[@id="map-border"]',
                'clip': '//svg:clipPath[@id="map-clip"]/svg:rect',
            })

        self.sheet = sheet
        self._size(sheet)

    def _size(self, sheet):
        """Prepare the template for the sheet size in use"""
        root = self.document.getroot()
        width, height = sheet.dimensions()
        root.attrib['width'] = f'{width}mm'
        root.attrib['height'] = f'{height}mm'
        root.attrib['viewBox'] = f'0 0 {width} {height}'

        self.position('image', *sheet.viewport(True))
        self.position('border', *sheet.viewport())
        self.position('clip', *sheet.viewport())

    def compose(self, image, title):
        """Set the layout's variable elements"""
        mapdata = 'data:image/png;base64,' + b64encode(image.mapdata).decode('utf-8')
        self.get('image').attrib[self.ns('xlink:href')] = mapdata
        self.get('title').text = title
