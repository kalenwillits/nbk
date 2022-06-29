def resolve_default_value(datatype):
    if hasattr(datatype, '__origin__'):
        return datatype.__origin__()
    elif datatype in (list, dict, int, str, float, bool):
        return datatype()

    return None
