def parse_set(string: str):
    return set(string.replace('{', '').replace('}', '').replace('\'', '').replace('\"', '').split(','))
