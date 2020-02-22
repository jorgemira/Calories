import re

from fiql_parser import parse_str_to_expression, FiqlException
from sqlalchemy_filters import apply_filters, apply_pagination
from sqlalchemy_filters.exceptions import FieldNotFound, BadFilterFormat
from werkzeug.exceptions import abort


def to_fiql(filter_spec):
    """
    Transform a filter specification in out format to Fiql
    :param filter_spec:
    :type filter_spec: str
    :return:
    """
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
    """
    Transform a Fiql object into a SQLAlchemy filter expression
    :param filter_spec: Fiql object containing the filter
    :type filter_spec: dict
    :return: The SQLAlchemy filter expression
    """
    if None in filter_spec:
        raise FiqlException
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


def apply_filter(query, filter_spec=None, page_size=10, page_number=1):
    """
    Apply filtering and pagination to any given query
    :param query: Query to apply filtering to
    :param filter_spec: Filter to apply to the query
    :type filter_spec: str
    :param page_size: Page size used for pagination
    :type page_size: int
    :param page_number: Page number used for pagination
    :type page_number: int
    :return: The query after applying the filter and pagination options selected, and the pagination information
    :rtype: tuple
    """

    if filter_spec:
        try:
            query = apply_filters(query, to_sql_alchemy(to_fiql(filter_spec)))
        except (FiqlException, FieldNotFound, BadFilterFormat):
            abort(400, f"Filter '{filter_spec}' is invalid")
    query, pagination = apply_pagination(query, page_number=page_number, page_size=page_size)
    return query, pagination
