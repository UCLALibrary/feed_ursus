# mypy: disallow_untyped_defs=False

import datetime
import re

from dateutil import parser


def get_dates(normalized_dates: list[str]) -> list[datetime.datetime]:
    """Maps a list of 'normalized_date' strings to a sorted list of datetime.

    Args:
        dates: A list of strings containing dates in the 'normalized_date' format.

    Returns:
        A list of years extracted from "dates".

    """

    return sorted(
        {
            item
            for normalized_date in normalized_dates
            for item in parse_normalized_date(normalized_date)
        }
    )


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


def get_date(date: str) -> datetime.datetime:
    """Parses the input date string, which should be in ISO8601 format except insofar as
    we allow years to be expressed with three (but not fewer) digits.

    Args:
        date: a string containing a date in modified ISO8601 format.

    Returns:
        A single datetime object.

    """

    # We accept 3-digit year values, but must pad them to the iso-standard 4 digits
    if THREE_DIGIT_YEAR_REGEX.match(date):
        return parser.isoparse("0" + date)
    else:
        return parser.isoparse(date)
