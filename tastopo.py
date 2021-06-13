#! /usr/bin/env python3

"""TasTopo - Generate printable topographic maps from TheList mapping service

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
    can take the form of a place name or a geo URI. Examples:
    - 'South East Cape'
    - 'geo:-43.643611,146.8275'
"""

from base64 import b64encode

from docopt import docopt
from lxml import etree
from svglib.svglib import SvgRenderer
from reportlab.graphics import renderPDF

import mapping


TEMPLATE_PATH = './templates/a4-landscape.svg'
SVG_NAMESPACES = {
    'svg': 'http://www.w3.org/2000/svg',
    'xlink': 'http://www.w3.org/1999/xlink',
}


def svgns(fullname):
    """Convert a SVG namespace prefix into a full namespace URI"""
    [ns, name] = fullname.split(':')
    namespace = SVG_NAMESPACES[ns]
    return f'{{{namespace}}}{name}'


def compose_map(sheet, image, title):
    """Compose a map sheet as SVG"""
    map_data = b64encode(image.mapdata)

    template = etree.parse(TEMPLATE_PATH)
    image_node = template.xpath('//svg:image[@id="map-data"]', namespaces=SVG_NAMESPACES)[0]
    title_node = template.xpath('//svg:text[@id="map-title"]', namespaces=SVG_NAMESPACES)[0]

    image_node.attrib[svgns('xlink:href')] = f'data:image/png;base64,{map_data.decode("utf-8")}'
    title_node.text = title

    return template.getroot()


def export_map(svg, filetype):
    """Export a map document"""
    filetype = filetype.casefold()
    if filetype == 'svg':
        with open('map.svg', 'wb') as f:
            f.write(etree.tostring(svg))
        return
    if filetype == 'pdf':
        renderer = SvgRenderer(None)
        drawing = renderer.render(svg)
        renderPDF.drawToFile(drawing, 'map.pdf')
        return

    raise Exception(f'Format \'{filetype}\' not suppported')


if __name__ == '__main__':
    args = docopt(__doc__)

    orientation = 'portrait' if args.get('--portrait') else 'landscape'
    location = mapping.Location(args.get('<location>'))

    sheet = mapping.get_sheet(args.get('--paper'), orientation)
    image = mapping.Image(location, sheet, args.get('--scale'))
    title = args.get('--title') or args.get('<location>').title()

    svg = compose_map(sheet, image, title)
    export_map(svg, args.get('--format'))
