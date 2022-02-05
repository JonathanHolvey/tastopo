import re


LATLON_REGEX = r'[\d.-]+,[\d.-]+'


def validate(args):
    """Validate CLI arguments and raise exception on invalid input"""
    location = args['<location>']
    if location.startswith('geo:') and not re.match(f'geo:{LATLON_REGEX}', location):
        raise ValueError('Invalid or unsupported geo URI')

    if not re.match(LATLON_REGEX, args['--translate']):
        raise ValueError('Invalid input for argument \'--translate\'')
