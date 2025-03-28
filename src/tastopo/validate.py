import re
from typing import Mapping, Any


LATLON_REGEX = r'[\d.-]+,[\d.-]+'


def validate(args: Mapping[str, Any]) -> None:
    """Validate CLI arguments and raise exception on invalid input

    :param args: The parsed CLI arguments provided by docopt
    :returns: Nothing
    :raises ValueError
    """
    location = args['<location>']
    if location.startswith('geo:') and not re.match(f'geo:{LATLON_REGEX}', location):
        raise ValueError('Invalid or unsupported geo URI')

    if not re.match(LATLON_REGEX, args['--translate']):
        raise ValueError('Invalid input for argument \'--translate\'')
