import re

from fiql_parser import parse_str_to_expression
from sqlalchemy_filters import apply_filters, apply_pagination


def to_fiql(filter_spec):
    transformations = [(r'\beq\b', r'=='),
                       (r'\bne\b', r'!='),
                       (r'\bgt\b', r'=gt='),
                       (r'\bge\b', r'=ge='),
                       (r'\blt\b', r'=lt='),
                       (r'\ble\b', r'=le='),
                       (r'\band\b', r';'),
                       (r'\bor\b', r','),
                       (r'"', r"'"),
                       (r'\s', r'')]
    for a, b in transformations:
        filter_spec = re.sub(a, b, filter_spec, flags=re.I)

    return parse_str_to_expression(filter_spec).to_python()


def to_sql_alchemy(filter_spec):
    if isinstance(filter_spec, tuple):
        if "'" in filter_spec[2]:
            value = filter_spec[2].replace("'", "")
        else:
            try:
                value = int(filter_spec[2])
            except ValueError:
                value = filter_spec[2]

        return {'field': filter_spec[0], 'op': filter_spec[1], 'value': value}

    if isinstance(filter_spec, list):
        return {filter_spec[0].lower(): [to_sql_alchemy(e) for e in filter_spec[1:]]}


def apply_filter(query, filter_spec, page_size=10, page_number=1):
    query = apply_filters(query, to_sql_alchemy(to_fiql(filter_spec)))
    query, _ = apply_pagination(query, page_number=page_number, page_size=page_size)
    return query
