#! /usr/bin/env python3

"""Map Tasmania - Generate printable maps from TheList mapping service

Usage: maptas generate [options] <location> <scale>

Options:
    -h --help      - Show this help message
    --version      - Show version information
    --size <paper> - Specify the paper size for printing [default: A4]
    --portrait     - Orientate the map in portrait, rather than landscape

Arguments:
    <location> - A map location to centre the map on, in the form of <x>,<y> coordinates
    <scale>    - The scale to generate the map at
"""

import re
from base64 import b64encode

from docopt import docopt
import requests
from lxml import etree
from svglib.svglib import SvgRenderer
from reportlab.graphics import renderPDF


SVG_NAMESPACES = {
    'svg': 'http://www.w3.org/2000/svg',
    'xlink': 'http://www.w3.org/1999/xlink',
}

API_URL = 'https://services.thelist.tas.gov.au/arcgis/rest/services'
BASE_MAP = 'Topographic'
RESOLUTION = 2000
TEMPLATE_PATH = './templates/a4-landscape.svg'


def svgns(fullname):
    """Convert a SVG namespace prefix into a full namespace URI"""
    [ns, name] = fullname.split(':')
    namespace = SVG_NAMESPACES[ns]
    return f'{{{namespace}}}{name}'


def generateMap(location, scale):
    """Generate a PDF map"""
    if not re.match(r'[-\d.]+,[-\d.]+', location):
        raise Exception('Location must be x,y coordinates')

    url = f'{API_URL}/Basemaps/{BASE_MAP}/MapServer/export'
    params = {
        'f': 'image',
        'format': 'png',
        'bbox': f'{location},{location}',
        'mapScale': scale,
        'size': f'{RESOLUTION},{RESOLUTION}',
    }

    r = requests.get(url, params=params)
    r.raise_for_status()
    map_data = b64encode(r.content)
    del r

    template = etree.parse(TEMPLATE_PATH)
    image_node = template.xpath('//svg:image[@id="mapData"]', namespaces=SVG_NAMESPACES)[0]
    image_node.attrib[svgns('xlink:href')] = f'data:image/png;base64,{map_data.decode("utf-8")}'

    renderer = SvgRenderer(None)
    drawing = renderer.render(template.getroot())
    renderPDF.drawToFile(drawing, 'map.pdf')


if __name__ == '__main__':
    args = docopt(__doc__)

    generateMap(args.get('<location>'), args.get('<scale>'))
