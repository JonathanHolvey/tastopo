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

from docopt import docopt
import requests


API_URL = 'https://services.thelist.tas.gov.au/arcgis/rest/services'
BASE_MAP = 'Topographic'
RESOLUTION = 2000


def generateMap(location, scale):
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

    with requests.get(url, params=params, stream=True) as r:
        r.raise_for_status()
        with open('./map.png', 'wb') as f:
            for chunk in r.iter_content():
                f.write(chunk)


if __name__ == '__main__':
    args = docopt(__doc__)

    generateMap(args.get('<location>'), args.get('<scale>'))
