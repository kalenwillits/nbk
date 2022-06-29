def parse_list(string: str):
    return string.replace('[', '').replace(']', '').replace('\'', '').replace('\"', '').split(',')
