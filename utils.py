"""
Utilities functions used in this project

© Anime no Sekai — 2021
"""

from re import compile

INT_REGEX = compile("[^0-9]")

def convert_to_int(element):
    """
    Safely converts anything to an integer
    """
    element = INT_REGEX.sub("", str(element).split('.')[0])
    if element != '':
        return int(element)
    else:
        return 0

def evaluate_fraction(fractional_value):
    values = [convert_to_int(number) for number in str(fractional_value).split("/")]
    if len(values) >= 1:
        return safe_division(values[0], values[1])
    return -1

def safe_division(x, y, error_returned=-1):
    if y != 0:
        return x / y
    return error_returned