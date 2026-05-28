# mypy: disallow_untyped_defs=False
"""
tests for year_parser.py

Creates a multi-valued 'year_isim' field by parsing 'normalized_date'.
"""

import datetime

import pytest

from feed_ursus import date_parser


@pytest.mark.parametrize(
    ("normalized_dates", "expected"),
    [
        (["1941-10-01"], [datetime.datetime(1941, 10, 1)]),
    ],
)
def test_iso_8601(normalized_dates: list[str], expected: list[datetime.datetime]):
    """Parses an iso 8601 standard string"""
    result = date_parser.get_dates(normalized_dates)
    assert result == expected


def test_just_year():
    """Parses a bare year."""
    test_date = datetime.datetime(1953, 1, 1)
    assert date_parser.get_dates(["1953"]) == [test_date]


def test_year_and_month():
    """Parses YYYY-MM"""
    test_date = datetime.datetime(1953, 10, 1)
    assert date_parser.get_dates(["1953-10"]) == [test_date]


def test_multiple_dates():
    """Parses multiple input values into a list of outputs."""
    test_dates = [
        datetime.datetime(1941, 10, 1),
        datetime.datetime(1935, 1, 1),
        datetime.datetime(1945, 1, 1),
    ]
    assert date_parser.get_dates(["1941-10-01", "1935", "1945"]) == sorted(test_dates)


def test_empty():
    """Returns an empty list if given an empty input."""
    assert date_parser.get_dates([]) == []


@pytest.mark.parametrize(
    ("normalized_dates", "expected"),
    [
        (["1953", "[between 1928-1939]"], [datetime.datetime(1953, 1, 1)]),
        (["1989-4-20"], []),
    ],
)
def test_unparseable(normalized_dates: list[str], expected: list[datetime.datetime]):
    """Raises an error when it encounters unparseable values."""
    with pytest.raises(ValueError):
        date_parser.get_dates(normalized_dates)


def test_range():
    """Parses YYYY/YYYY into dates."""

    assert date_parser.get_dates(["1937/1939", "1942/1943"]) == [
        datetime.datetime(1937, 1, 1),
        datetime.datetime(1939, 1, 1),
        datetime.datetime(1942, 1, 1),
        datetime.datetime(1943, 1, 1),
    ]

    # Parses YYY/YYYY into dates.

    assert date_parser.get_dates(["990/1000"]) == [
        datetime.datetime(990, 1, 1),
        datetime.datetime(1000, 1, 1),
    ]


def test_range_with_months():
    """Months can be included in range elements, but are ingored."""

    assert date_parser.get_dates(["1934-06/1934-07"]) == [
        datetime.datetime(1934, 6, 1),
        datetime.datetime(1934, 7, 1),
    ]


def test_impossible_range():
    """Months can be included in range elements, but are ingored."""

    with pytest.raises(ValueError):
        date_parser.get_dates(["2026/1980"])


def test_duplicates():
    """Deduplicates elements in output."""

    assert date_parser.get_dates(["1934-06/1935-07", "1934-06-01", "1934"]) == [
        datetime.datetime(1934, 1, 1),
        datetime.datetime(1934, 6, 1),
        datetime.datetime(1935, 7, 1),
    ]


def test_non_string():
    with pytest.raises(ValueError):
        date_parser.get_dates([datetime.datetime(2012, 12, 15)])


def test_range_too_many_parts():
    with pytest.raises(ValueError):
        date_parser.get_dates(["1945", "1980/2012/2020"])
