import json


def parse_headers(headers: dict):
    '''
    Parses headers to prepare for clients sending headers to server.
    '''
    parsed_headers = {}
    for header, value in headers.items():
        parsed_headers[header] = json.dumps(value)

    return parsed_headers



