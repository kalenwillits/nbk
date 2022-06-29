import pandas as pd


def is_datetime(string):
    if not isinstance(string, str):
        return False

    if len(string) < 10:
        return False

    if string:
        try:
            pd.to_datetime(string)
            return True
        except ValueError:
            return False
    else:
        return False
