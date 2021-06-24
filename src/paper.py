import math
import re


class Paper:
    """A piece of paper"""
    def __init__(self, spec):
        if not re.match(r'^[aA]\d+$', spec):
            raise ValueError(f"'{spec}' is not a valid ISO 216 A-series paper size")
        self.spec = spec
        self.series = spec[0]
        self.size = int(spec[1:])

    def dimensions(self):
        """Get the dimensions of an ISO 216 A-series paper size"""
        size = 0
        area = 1e6  # A0 area in square mm
        while size < self.size:
            area /= 2
            size += 1

        width = math.sqrt(area / math.sqrt(2))
        height = width * math.sqrt(2)

        rounder = round if size == 0 else math.floor
        return rounder(width), rounder(height)
