"""
Creates a multi-valued 'year_isim' field by parsing input strings.
"""

import re
import typing


RANGE = re.compile(r"(.*)/(.*)")
YEAR = re.compile(r"\b(\d\d\d\d|\d\d\d)\b")


def integer_years(dates: typing.Any) -> typing.List[int]:
    """Maps a list of 'normalized_date' strings to a sorted list of integer years.

    Args:
        dates: A list of strings containing dates in the 'normalized_date' format.

    Returns:
        A list of years extracted from "dates".

    """
    if not isinstance(dates, typing.Iterable):
        return []

    years: typing.Set[int] = set()
    for date in dates:
        if not isinstance(date, str):
            continue
        match = RANGE.search(date)
        if match:
            start_str, end_str = match.groups()
            start = get_year(start_str)
            end = get_year(end_str)
            if start and end:
                years.update(range(start, end + 1))
        else:
            year = get_year(date)
            if year:
                years.add(year)
    return sorted(years)


def get_year(date: str) -> typing.Optional[int]:
    """Extracts the single 4-digit year found in the input date string.

    Args:
        date: a string containing a date in 'normalized_date' format.

    Returns:
        A single integer year.

    """
    matches = YEAR.findall(date)
    if len(matches) == 1:
        return int(matches[0])
    return None
