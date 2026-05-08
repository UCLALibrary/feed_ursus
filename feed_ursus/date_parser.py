# mypy: disallow_untyped_defs=False
"""
Creates a multi-valued 'year_isim' field by parsing input strings.
"""

import re
import typing
from datetime import datetime

from dateutil import parser

NORMALIZED_RANGE = re.compile(r"(.*)/(.*)")


def get_dates(normalized_dates: typing.Any, strict=True):
    """Maps a list of 'normalized_date' strings to a sorted list of datetime.

    Args:
        dates: A list of strings containing dates in the 'normalized_date' format.

    Returns:
        A list of years extracted from "dates".

    """
    if not isinstance(normalized_dates, typing.Iterable):
        return []
    solr_dts = set()
    for normalized_date in normalized_dates:
        if not isinstance(normalized_date, str):
            continue
        match = NORMALIZED_RANGE.search(normalized_date)
        if match:
            start_str, end_str = match.groups()
            start = get_date(start_str, strict=strict)
            end = get_date(end_str, strict=strict)
            if start and end:
                solr_dts.update({start, end})
        else:
            solr_date = get_date(normalized_date, strict=strict)
            if solr_date:
                solr_dts.add(solr_date)
    return sorted(solr_dts)


def get_date(date: str, strict=True):
    """Extracts the single 4-digit year found in the input date string.

    Args:
        date: a string containing a date in 'normalized_date' format.

    Returns:
        A single date.

    """
    try:
        parsed_date = parser.parse(date, default=datetime(1978, 1, 1))
        return parsed_date
    except ValueError as err:
        if strict:
            raise err
        else:
            return None
