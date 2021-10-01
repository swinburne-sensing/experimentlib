import re
import regex
import typing

import attr


class ParseError(Exception):
    pass


_RE_PARSE_DICT = regex.compile(r'{((?>[^{}]+|(?R))*)}')
_RE_PAIR_DICT = regex.compile(r'^([\"\w\d_]+)\s*:\s*([^\r\n]+)$')

_RE_PARSE_LIST = regex.compile(r'\[((?>[^\[\]]+|(?R))*)\]')

_RE_PAIR_ASSIGN = re.compile(r'^\s*([\"\w\d_]+)\s*:\s*([^,\r\n]+)[\s,]*$')
_RE_OBJ_ASSIGN = re.compile(r'^\s*([\w]+)\.([\w\d\[\]]*)\s+=\s+([^;]+);$')
_RE_VAR_ASSIGN = re.compile(r'\s*var\s+(\w+)\s+=\s+([^;]+);', re.MULTILINE)


@attr.s(frozen=True)
class JavascriptMapping(object):
    name: str = attr.ib()

    def __str__(self):
        return self.name


# All types assignable during parsing
T_ASSIGNMENT = typing.Union[
    bool,
    float,
    int,
    str,
    JavascriptMapping,
    typing.Dict[typing.Union[int, str], 'T_ASSIGNMENT'],
    typing.List['T_ASSIGNMENT']
]


def _parse_dict(value: str) -> typing.Dict[typing.Union[int, str], T_ASSIGNMENT]:
    value_dict = {}

    for value_inst in _parse_list(value):
        value_inst = value_inst.strip()

        if (pair_match := _RE_PAIR_DICT.match(value_inst)) is not None:
            pair_key = pair_match[1]

            if pair_key.isdigit():
                pair_key = int(pair_key)

            value_dict[pair_key] = parse_value(pair_match[2])

    return value_dict


def _parse_list(value: str) -> typing.Sequence[str]:
    value_list = []
    value_inst_list = []

    dict_depth = 0
    list_depth = 0

    for value_char in value:
        if value_char == '[':
            list_depth += 1
        elif value_char == ']':
            list_depth -= 1

            if list_depth < 0:
                raise ParseError(f"Mismatched list brackets in input \"{value}\"")
        elif value_char == '{':
            dict_depth += 1
        elif value_char == '}':
            dict_depth -= 1

            if dict_depth < 0:
                raise ParseError(f"Mismatched dict brackets in input \"{value}\"")

        if dict_depth == 0 and list_depth == 0 and value_char == ',':
            value_list.append(''.join(value_inst_list))
            value_inst_list.clear()
        else:
            value_inst_list.append(value_char)

    # Append final instance
    value_list.append(''.join(value_inst_list))

    return value_list


def parse_value(value: str) -> typing.Optional[T_ASSIGNMENT]:
    """

    :param value:
    :return:
    """
    value = value.strip()

    if value == 'true':
        return True

    if value == 'false':
        return False

    # Catch strings
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    
    if (dict_match := _RE_PARSE_DICT.match(value)) is not None:
        return _parse_dict(dict_match[1])

    if (list_match := _RE_PARSE_LIST.match(value)) is not None:
        return [parse_value(x) for x in _parse_list(list_match[1])]

    # Attempt to parse numeric values
    try:
        if '.' in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        pass

    # Unhandled value, probably a mapping to something else
    return JavascriptMapping(value)


def parse_properties(code: str, namespace: str) -> typing.Dict[str, T_ASSIGNMENT]:
    """ Parse JavaScript code for assignments of properties to objects.

    This is a standalone and fairly trivial implementation of a parser, so it would normally get a lot wrong in
    real-world applications, but for IoT style applications it's fine.

    :param code: JavaScript code as a string
    :param namespace: filter for assignments to object matching this name
    :return: dict of property assignments
    """
    assignments = {}

    for line in code.split('\n'):
        obj_assign = _RE_OBJ_ASSIGN.match(line)

        if obj_assign is None:
            continue

        # Only save matching object names
        if obj_assign[1] != namespace:
            continue

        assign_value = parse_value(obj_assign[3])

        if assign_value is not None:
            assignments[obj_assign[2]] = assign_value

    return assignments


def parse_variables(code: str) -> typing.Dict[str, T_ASSIGNMENT]:
    """ Parse JavaScript code for assignments to variables.

    This is a standalone and fairly trivial implementation of a parser, so it would normally get a lot wrong in
    real-world applications, but for IoT style applications it's fine.

    :param code: JavaScript code as a string
    :return: dict of variable assignment
    """
    assignments = {}

    for var_match in _RE_VAR_ASSIGN.finditer(code):
        var_name = var_match[1]
        var_value = parse_value(var_match[2])

        if var_value is not None:
            assignments[var_name] = var_value

    return assignments
