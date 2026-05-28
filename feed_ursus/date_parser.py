# mypy: disallow_untyped_defs=False
"""
Creates a multi-valued 'year_isim' field by parsing input strings.
"""

import datetime
import re
from typing import Any

from dateutil import parser


def get_dates(normalized_dates: Any) -> list[datetime.datetime]:
    """Maps a list of 'normalized_date' strings to a sorted list of datetime.

    Args:
        dates: A list of strings containing dates in the 'normalized_date' format.

    Returns:
        A list of years extracted from "dates".

    """

    if not isinstance(normalized_dates, list):
        raise ValueError("must be a list of normalized date strings")

    solr_dts: set[datetime.datetime] = set()
    for normalized_date in normalized_dates:  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(normalized_date, str):
            raise ValueError("must be a list of normalized date strings")
        solr_dts.update(parse_normalized_date(normalized_date))

    return sorted(solr_dts)


def parse_normalized_date(normalized_date: str) -> tuple[datetime.datetime, ...]:
    match normalized_date.split("/"):
        case []:
            pass
        case [date]:
            return (get_date(date),)
        case [start, end]:
            start = get_date(start)
            end = get_date(end)
            if start > end:
                raise ValueError("start date must be before end date")
            return (start, end)
        case _:
            raise ValueError(
                "normalized_date must have form [START_DATE] or [START_DATE]/[END_DATE]"
            )

    return tuple()


THREE_DIGIT_YEAR_REGEX = re.compile(r"^\d\d\d\b")


def get_date(date: str):
    """Extracts the single 4-digit year found in the input date string.

    Args:
        date: a string containing a date in 'normalized_date' format.

    Returns:
        A single date.

    """

    # We accept 3-digit year values, but must pad them to the iso-standard 4 digits
    if THREE_DIGIT_YEAR_REGEX.match(date):
        return parser.isoparse("0" + date)
    else:
        return parser.isoparse(date)
