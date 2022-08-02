import platform
import re

from lxml import etree
from svglib.svglib import SvgRenderer
from reportlab.graphics import renderPDF

INVALID_FILENAME_CHARS = {
    'Linux': '/',
    'Darwin': '/:',
    'Windows': '\\:'
}


def clean_filename(filename):
    """Remove invalid characters from a filename"""
    invalid = INVALID_FILENAME_CHARS.get(platform.system(), INVALID_FILENAME_CHARS['Linux'])
    return re.sub(r' +', ' ', ''.join(c for c in filename if c not in invalid))


def export_map(svg, filetype, filename):
    """Export a map document"""
    filetype = filetype.casefold()
    extension = '.' + filetype
    if not filename.endswith(extension):
        filename += extension

    if filetype == 'svg':
        with open(filename, 'wb') as f:
            f.write(etree.tostring(svg))
        return
    if filetype == 'pdf':
        renderer = SvgRenderer(None)
        drawing = renderer.render(svg)
        renderPDF.drawToFile(drawing, filename)
        return

    raise ValueError(f"Format '{filetype}' not suppported")
