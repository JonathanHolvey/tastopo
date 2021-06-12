#! /usr/bin/env python3

"""Tasmania Topo - Generate printable topographic maps from TheList mapping service

Usage: tastopo generate [options] <location>

Options:
    -h --help        - Show this help message
    --version        - Show version information
    --scale <ratio>  - Specify the scale of the printed map [default: 25000]
    --title <text>   - Set the title on the map sheet, instead of the location name
    --paper <size>   - Specify the paper size for printing [default: A4]
    --portrait       - Orientate the map in portrait, rather than landscape
    --format <type>  - The file format to export; either PDF or SVG [default: PDF]

Map location
The <location> argument is used to specify the centre of the map. This argument
can take the form of a place name or a pair of ListMap <x>,<y> coordinates.
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
PRINT_DPI = 150
TEMPLATE_PATH = './templates/a4-landscape.svg'
IMAGE_BLEED = 2  # Allow for misalignment in PDF generation

MAP_SHEETS = [{
    'size': 'a4',
    'orientation': 'landscape',
    'viewport': (286.86, 185.67),
}]


def svgns(fullname):
    """Convert a SVG namespace prefix into a full namespace URI"""
    [ns, name] = fullname.split(':')
    namespace = SVG_NAMESPACES[ns]
    return f'{{{namespace}}}{name}'


class MapSheet:
    def __init__(self, config):
        self.config = config

    def mapsize(self):
        """Get the required map with and height in pixels"""
        resolution = PRINT_DPI / 25.4
        return [round(resolution * (i + 2 * IMAGE_BLEED)) for i in self.config['viewport']]


def get_mapsheet(size, orientation):
    """Select a map sheet by size and orientation"""
    for config in MAP_SHEETS:
        if config['size'] == size.lower() and config['orientation'] == orientation.lower():
            return MapSheet(config)


def find_location(location):
    """Find the coordinates of a map location by its place name"""
    if re.match(r'[-\d.]+,[-\d.]+', location):
        return location

    url = f'{API_URL}/Public/PlacenamePoints/MapServer/find'
    params = {
        'f': 'json',
        'searchText': location,
        'layers': '0',
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    for place in r.json()['results']:
        if place['value'].casefold() == location.casefold():
            return place['geometry']['x'], place['geometry']['y']

    raise Exception('Location {} not found')


def compose_map(location, scale, sheet, title):
    """Compose a map sheet as SVG"""
    url = f'{API_URL}/Basemaps/{BASE_MAP}/MapServer/export'
    params = {
        'f': 'image',
        'format': 'png',
        'bbox': f'{location},{location}',
        'mapScale': scale,
        'size': '{},{}'.format(*sheet.mapsize()),
        'dpi': PRINT_DPI,
    }

    r = requests.get(url, params=params)
    r.raise_for_status()
    map_data = b64encode(r.content)
    del r

    template = etree.parse(TEMPLATE_PATH)
    image_node = template.xpath('//svg:image[@id="map-data"]', namespaces=SVG_NAMESPACES)[0]
    title_node = template.xpath('//svg:text[@id="map-title"]', namespaces=SVG_NAMESPACES)[0]

    image_node.attrib[svgns('xlink:href')] = f'data:image/png;base64,{map_data.decode("utf-8")}'
    title_node.text = title

    return template.getroot()


def export_map(svg, format):
    """Export a map document"""
    format = format.casefold()
    if format == 'svg':
        with open('map.svg', 'wb') as f:
            f.write(etree.tostring(svg))
        return
    if format == 'pdf':
        renderer = SvgRenderer(None)
        drawing = renderer.render(svg)
        renderPDF.drawToFile(drawing, 'map.pdf')
        return

    raise Exception(f'Format \'{format}\' not suppported')


if __name__ == '__main__':
    args = docopt(__doc__)

    orientation = 'portrait' if args.get('--portrait') else 'landscape'
    sheet = get_mapsheet(args.get('--paper'), orientation)
    location = find_location(args.get('<location>'))
    title = args.get('--title') or args.get('<location>').title()
    print(location)

    svg = compose_map(location, int(args.get('--scale')), sheet, title)
    export_map(svg, args.get('--format'))
