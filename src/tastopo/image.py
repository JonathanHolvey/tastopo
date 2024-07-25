import io
from typing import Iterable

from PIL import Image

from .mapdata import Tile
from .types import Point, BoxSize


def frombytes(data: bytes) -> Image:
    """Create an image object from a PNG byte array

    :param data: The PNG byte data to parse
    :returns: A PIL image object
    """
    return Image.open(io.BytesIO(bytes(data)))


def tobytes(image: Image) -> bytes:
    """Convert an image object to a PNG byte array

    :param image: A PIL image object to export
    :returns: An PNG byte array
    """
    data = io.BytesIO()
    image.save(data, format='PNG')
    return data.getvalue()


def stitch(tiles: Iterable[Tile], size: BoxSize, start: Point = (0, 0)) -> bytes:
    """Join an array of image tiles into a single image

    :param tiles: A list of tiles to stitch
    :param size: The size of the grid to stitch the tiles into
    :param start: The position in the grid of the first tile
    :returns: A single image made up of all the tiles
    """
    result = Image.new('RGBA', size)

    x = 0
    y = 0
    for index, tile in enumerate(tiles):
        tileimage = frombytes(tile)
        result.paste(tileimage, (x + start[0], y + start[1]))
        x += tileimage.width
        if x >= size[0] - start[0]:
            x = 0
            y += tileimage.height

    return tobytes(result)


def layer(background: bytes, *layers: tuple[bytes, float]) -> bytes:
    """Merge multiple image layers together

    :param background: The image to use as the base layer
    :param layers: Additional images to layer on top, with opacity in 0-1 range
    :returns: The layers combined in a single image
    """
    result = frombytes(background)

    for imagedata, opacity in layers:
        image = frombytes(imagedata)
        image = image.resize(result.size, Image.BILINEAR)
        result = Image.blend(result, image, alpha=opacity)

    return tobytes(result)
