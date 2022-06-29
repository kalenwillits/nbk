import pandas as pd

CORE_TYPES = (str, int, float, bool)
OUTER_TYPES = (list, dict)


def retrieve_foreign_data(db, model_name, pk: str):
    if not (query_df := db.query(model_name, pk=pk)).empty:
        foreign_data = next(hydrate(db, model_name, query_df))
        return foreign_data

    return None


def isnull(value) -> bool:
    if pd.Series(value).isnull().sum():
        return True
    return False


def parse_datatype(db, datatype, value):
    if hasattr(datatype, '__origin__'):
        outer_type = datatype.__origin__
        inner_types = datatype.__args__

        if outer_type is list:
            # Modify value for ellipsis
            if not inner_types[-1] is Ellipsis:
                while len(value) < len(inner_types):
                    if (inner_type := inner_types[0]) in db.models:
                        value.append(None)
                    else:
                        value.append(inner_type())

                value = value[:len(inner_types) + 1]

            result = []
            for index, inner_type in enumerate(inner_types):
                if index < len(value):
                    # Handle nested foreign Key
                    if inner_type in db.models:
                        result.append(parse_datatype(db, inner_type, value[index]))

                    # Handle repeated value
                    elif inner_type is Ellipsis:
                        if other_values := value[:-1]:
                            for inner_value in other_values:
                                result.append(parse_datatype(db, inner_types[index - 1], inner_value))

                    # Handle other outer types.
                    elif inner_type in OUTER_TYPES or hasattr(inner_type, '__origin__'):
                        result.append(parse_datatype(db, inner_type, value[index]))

                    # Handle all else.
                    elif inner_type in CORE_TYPES:
                        if value[index] is None:
                            result.append(None)
                        else:
                            result.append(inner_type(value[index]))

            return result

        elif outer_type is dict:
            assert len(inner_types) == 2, f'{inner_types} <- dict types can only contain a key type and value type.'
            assert inner_types[0] in CORE_TYPES, f'{inner_types[0]} <- is not a supported key type.'
            assert isinstance(value, dict), f'Validation error: {value} is not of type {datatype}'

            key_type = inner_types[0]
            value_type = inner_types[1]
            result = {}
            for key, data in value.items():
                result[key_type(key)] = parse_datatype(db, value_type, data)

            return result

        else:
            raise TypeError(f'Invalid iter type {outer_type}')

    elif datatype in CORE_TYPES:
        if not value:
            return None
        return datatype(value)

    elif datatype in db.models:
        return str(value)

    else:
        raise Exception(f'{datatype} is not supported.')


def hydrate(db, model_name: str, df: pd.DataFrame):
    instance = db.models[model_name]()
    for index in range(df.shape[0]):
        record = df.iloc[index].to_dict()
        for field, datatype, default_value in instance._schema.items():

            if hasattr(datatype, '__origin__'):
                outer_type = datatype.__origin__
                inner_types = datatype.__args__
                if outer_type is list:
                    if result := next(dig(db, outer_type, inner_types, record[field]), None):
                        record[field] = result

                elif outer_type is dict:
                    if result := next(dig(db, outer_type, inner_types, record[field]), None):
                        record[field] = result

            elif datatype in db.models:
                if isinstance(record[field], dict):
                    pk = record[field].get('pk', '')
                else:
                    pk = record[field]

                if pk:
                    record[field] = next(hydrate(db, datatype.__name__, db.query(datatype.__name__, pk=pk)), None)

        yield record


def dig(db, outer_type, inner_types, data):
    record = None
    if outer_type is list:
        record = []

        if data:
            if hasattr(inner_types[0], '__origin__'):
                for value in data:
                    if hasattr(inner_types[0].__args__[0], '__origin__'):
                        record.append(next(dig(db, inner_types[0].__origin__, inner_types[0].__args__, value), None))
                    elif inner_types[0] in db.models:
                        record.append(next(
                            hydrate(db, inner_types[0].__name__, db.query(inner_types[0].__name__, pk=value)), None))
                    else:
                        record.append(value)

            else:
                for value in data:
                    if inner_types[0] in db.models:
                        if isinstance(value, str):
                            record.append(next(
                                hydrate(
                                    db, inner_types[0].__name__, db.query(inner_types[0].__name__, pk=value)), None))
                    else:
                        record.append(value)

    elif outer_type is dict:
        record = {}
        if data:
            for key, value in data.items():
                if hasattr(inner_types[1], '__origin__'):
                    record.update({key: next(dig(db, inner_types[1].__origin__, inner_types[1].__args__, value), None)})
                elif inner_types[1] in db.models:
                    if isinstance(value, dict):
                        pk = value.get('pk')
                    else:
                        pk = value

                    if pk:
                        record.update(
                            {key: next(
                                hydrate(db, inner_types[1].__name__, db.query(inner_types[1].__name__, pk=pk)), None)})
                else:
                    record.update({key: value})

    else:
        raise TypeError(f'type({outer_type}) is not supported.')

    yield record
