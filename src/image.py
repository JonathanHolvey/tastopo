from PIL import Image
import io


def frombytes(data):
    """Create an image object from a PNG byte array"""
    return Image.open(io.BytesIO(data))


def tobytes(image):
    """Convert an image object to a PNG byte array"""
    data = io.BytesIO()
    image.save(data, format='PNG')
    return data.getvalue()


def stitch(tiles, size):
    """Join an array image tiles into a single image"""
    result = Image.new('RGB', size)

    x = 0
    y = 0
    for index, tile in enumerate(tiles):
        tileimage = frombytes(tile)
        result.paste(tileimage, (x, y))
        x += tileimage.width
        if x >= size[0]:
            x = 0
            y += tileimage.height

    return tobytes(result)
