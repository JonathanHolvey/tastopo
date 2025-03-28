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


def clean_filename(filename: str) -> str:
    """Remove invalid characters from a filename

    :param filename: The original file name for cleaning
    :returns: The sanitised file name
    """
    invalid = INVALID_FILENAME_CHARS.get(platform.system(), INVALID_FILENAME_CHARS['Linux'])
    return re.sub(r' +', ' ', ''.join(c for c in filename if c not in invalid))


def export_map(svg: etree._Element, filetype: str, filename: str):
    """Export a map document

    :param svg: The map SVG root element to be exported
    :param filetype: The file type/extension to export the map SVG as
    :param filename: The name of the output file, with or without an extension"""
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
