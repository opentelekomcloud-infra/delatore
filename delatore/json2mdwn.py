markdown = ''
tab = '    '


def convert(json_data):
    depth = 0
    parse_json(json_data, depth)
    global markdown
    markdown = markdown.replace('#######', '######')
    return markdown.replace('_', '-')


def parse_json(json_block, depth):
    if isinstance(json_block, dict):
        parse_dict(json_block, depth)
    if isinstance(json_block, list):
        parse_list(json_block, depth)


def parse_dict(dictionary, depth):
    for key in dictionary:
        if isinstance(dictionary[key], (dict, list)):
            add_header(key, depth)
            parse_json(dictionary[key], depth + 1)
        else:
            add_value(key, dictionary[key], depth)


def parse_list(_list, depth):
    for value in _list:
        if not isinstance(value, (dict, list)):
            index = _list.index(value)
            add_value(index, value, depth)
        else:
            parse_dict(value, depth)


def add_value(key, value, depth):
    chain = tab * (bool(depth - 1)) + ' ' + str(key) + ' :  `' + str(value) + ' `' + \
            '\n'
    global markdown
    markdown += chain


def add_header(value, depth):
    chain = '* ' + ' ' * (depth + 1) + ' value ' + ('' * (depth + 1) + ': *' + '\n')
    global markdown
    markdown += chain.replace('value', value.title())
