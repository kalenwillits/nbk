import re

def parse_nums(string):
    nums_list = re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", string)
    nums_str = ''.join(nums_list)
    return nums_str
