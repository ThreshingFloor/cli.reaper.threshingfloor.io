import sys

import six


def prompt(message, error_message, is_valid=lambda v: True, default=None):
    """
    Prompt for input given a message and return that value after verifying the input.

    Keyword arguments:
    message: the message to display when asking the user for the value
    error_message: the message to display when the value fails validation
    is_valid: a function that returns True if the value given by the user is valid
    default: a default value for the prompt
    """
    res = None

    while res is None:
        if default:
            res = six.moves.input("%s (enter for '%s'): " % (message, default))
            if not res:
                res = default
        else:
            res = six.moves.input("%s: " % message)

        if not is_valid(res):
            sys.stderr.write("%s\n" % error_message)
            res = None

    return res
