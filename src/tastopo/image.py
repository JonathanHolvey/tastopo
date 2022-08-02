import io

from PIL import Image


def frombytes(data):
    """Create an image object from a PNG byte array"""
    return Image.open(io.BytesIO(bytes(data)))


def tobytes(image):
    """Convert an image object to a PNG byte array"""
    data = io.BytesIO()
    image.save(data, format='PNG')
    return data.getvalue()


def stitch(tiles, size, start=(0, 0)):
    """Join an array of image tiles into a single image"""
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


def layer(background, *layers):
    """Merge multiple image layers together"""
    result = frombytes(background)

    for image, opacity in layers:
        image = frombytes(image)
        image = image.resize(result.size, Image.BILINEAR)
        result = Image.blend(result, image, alpha=opacity)

    return tobytes(result)
