

def assert_datatypes(db, datatype, value, field: str) -> None:
    '''
    Checks the datatype against value and ensures the value matches the datatype.
    '''
    assert_message = f'Field({field}): type({datatype}) does not match value({value}): type({type(value)})'

    if hasattr(datatype, '__origin__'):
        outer_type = datatype.__origin__
        inner_types = datatype.__args__
        assert type(value) is outer_type, assert_message

        if outer_type is list:
            if inner_types[-1] is Ellipsis:
                inner_type = inner_types[0]
                for inner_value in value:
                    assert_datatypes(db, inner_type, inner_value, field)

            for inner_value, inner_type in zip(value[:len(inner_types)], inner_types):
                if inner_type is Ellipsis:
                    assert_datatypes(db, inner_types[0], inner_value, field)
                else:
                    assert_datatypes(db, inner_type, inner_value, field)

        elif outer_type is dict:
            assert len(inner_types) == 2, assert_message
            for key, value in value.items():
                assert_datatypes(db, inner_types[0], key, field)
                assert_datatypes(db, inner_types[1], value, field)

        else:
            raise TypeError(f'Type{datatype} is an unsupported type.')

    else:
        if datatype in db.models:
            if value is not None:
                assert type(value) is str, assert_message
        else:
            assert type(value) is datatype, assert_message
