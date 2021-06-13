from base64 import b64encode
from lxml import etree


class SVG:
    """An XML wrapper for manipulating SVG documents"""
    NAMESPACES = {
        'svg': 'http://www.w3.org/2000/svg',
        'xlink': 'http://www.w3.org/1999/xlink',
    }

    def __init__(self, filepath):
        self.document = etree.parse(filepath)
        self.elements = {}

    def ns(self, fullname):
        """Convert a SVG namespace prefix into a full namespace URI"""
        [ns, name] = fullname.split(':')
        namespace = self.NAMESPACES[ns]
        return f'{{{namespace}}}{name}'

    def select(self, paths):
        """Find elements by xpath and store against a key for later use"""
        for key, path in paths.items():
            try:
                self.elements[key] = self.document.xpath(path, namespaces=self.NAMESPACES)[0]
            except AttributeError:
                pass

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
    TEMPLATE_PATH = './template.svg'
    """A map sheet layout"""
    def __init__(self, sheet):
        super().__init__(self.TEMPLATE_PATH)
        self.sheet = sheet
        self.select({
            'image': '//svg:image[@id="map-data"]',
            'title': '//svg:text[@id="map-title"]',
            'border': '//svg:rect[@id="map-border"]',
            'clip': '//svg:clipPath[@id="map-clip"]/svg:rect',
        })
        self._size(sheet)

    def _size(self, sheet):
        """Prepare the template for the sheet size in use"""
        self.position('image', *sheet.viewport(True))
        self.position('border', *sheet.viewport())
        self.position('clip', *sheet.viewport())

    def compose(self, image, title):
        """Set the layout's variable elements"""
        mapdata = 'data:image/png;base64,' + b64encode(image.mapdata).decode('utf-8')
        self.get('image').attrib[self.ns('xlink:href')] = mapdata
        self.get('title').text = title
