import re


def to_snake(name_string):
    '''
    Converts a string in title case to snake case.
    '''
    word_list = re.findall('[A-Z][^A-Z]*', name_string)
    snake_case = '_'.join((f'{w.lower()}' for w in word_list))
    return snake_case
