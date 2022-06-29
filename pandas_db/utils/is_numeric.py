from .parse_nums import parse_nums
import pandas as pd


def is_numeric(data, ignore_letters=True):
    'Checks if there are numbers in an object.'
    if ignore_letters and isinstance(data, str):
        if parse_nums(data):
            return True
        return False
    else:
        try:
            pd.to_numeric(data)
            return True
        except ValueError:
            return False
