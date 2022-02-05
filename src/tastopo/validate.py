import re


def validate(args):
    """Validate CLI arguments and raise exception on invalid input"""
    location = args['<location>']
    if location.startswith('geo:') and not re.match(r'geo:[\d.-]+,[\d.-]+', location):
        raise ValueError('Invalid or unsupported geo URI')

    if not re.match(r'\d+,\d+', args['--translate']):
        raise ValueError('Invalid input for argument \'--translate\'')
