import re


def validate(args):
    """Validate CLI arguments and raise exception on invalid input"""
    if not re.match(r'\d+,\d+', args['--translate']):
        raise ValueError('Invalid input for argument \'--translate\'')
