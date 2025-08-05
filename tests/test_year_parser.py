# mypy: disallow_untyped_defs=False
"""
tests for year_parser.py

Creates a multi-valued 'year_isim' field by parsing 'normalized_date'.
"""

from feed_ursus import year_parser


def test_iso_8601():
    """Parses an iso 8601 standard string"""

    assert year_parser.integer_years(["1941-10-01"]) == [1941]


def test_just_year():
    """Parses a bare year."""

    assert year_parser.integer_years(["1953"]) == [1953]


def test_year_and_month():
    """Parses YYYY-MM"""

    assert year_parser.integer_years(["1953-10"]) == [1953]


def test_multiple_dates():
    """Parses multiple input values into a list of outputs."""

    assert year_parser.integer_years(["1941-10-01", "1935", "1945"]) == [
        1935,
        1941,
        1945,
    ]


def test_empty():
    """Returns an empty list if given an empty input."""
    assert year_parser.integer_years([]) == []


def test_unparseable():
    """Doesn't return anything for unparseable values, but still parses other elements in input."""

    assert year_parser.integer_years(["1953", "[between 1928-1939]"]) == [1953]


def test_range():
    """Parses YYYY/YYYY into a range of years."""

    assert year_parser.integer_years(["1937/1939", "1942/1943"]) == [
        1937,
        1938,
        1939,
        1942,
        1943,
    ]

    # Parses YYY/YYYY into a range of years.

    assert year_parser.integer_years(["990/1000"]) == [
        990,
        991,
        992,
        993,
        994,
        995,
        996,
        997,
        998,
        999,
        1000,
    ]


def test_range_with_months():
    """Months can be included in range elements, but are ingored."""

    assert year_parser.integer_years(["1934-06/1934-07"]) == [1934]


def test_duplicates():
    """Deduplicates elements in output."""

    assert year_parser.integer_years(["1934-06/1935-07", "1934-06-01", "1934"]) == [
        1934,
        1935,
    ]
