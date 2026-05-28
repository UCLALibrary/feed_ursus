# pyright: standard

"""Tests for feed_ursus.py"""

from typing import Any

import pytest

from feed_ursus.reindex import (
    get_record_diff,
    normalize_record,
    normalize_value,
)


@pytest.mark.parametrize(
    ("_summary", "r1", "r2", "is_different"),
    [
        ("empty dicts", {}, {}, False),
        (
            "identical dicts",
            {"a": 1, "b": [2, 3]},
            {"a": 1, "b": [2, 3]},
            False,
        ),
        (
            "totally different",
            {"a": 1},
            {"b": 4},
            True,
        ),
        (
            "ignores difference in order",
            {"a": 1, "b": 2},
            {"b": 2, "a": 1},
            False,
        ),
        (
            "ignores new root items",
            {"a": 1, "b": [2, 3]},
            {"a": 1, "b": [2, 3], "c": 4},
            False,
        ),
        (
            "ignores additions to nested arrays",
            {"a": 1, "b": [2, 3]},
            {"a": 1, "b": [2, 3, 4]},
            False,
        ),
        (
            "flags removed dict item",
            {"a": 1, "b": [2, 3]},
            {"a": 1},
            True,
        ),
        (
            "ignores removal of specifically listed fields",
            {"a": 1, "member_ids_ssim": [2]},
            {"a": 1},
            False,
        ),
        (
            "ignores removal of empty or falsy fields",
            {"a": None, "b": [], "c": "", "d": [""]},
            {},
            False,
        ),
        (
            "ignores access group changes, since they're well understood and correct based on visibility",
            {"read_access_group_ssim": ["registered"]},
            {},
            False,
        ),
        (
            "doesn't flag fixed MARC codes",
            {"creator_sim": ["Bunche, Ralph J. (Ralph Johnson), $d 1904-1971"]},
            {"creator_sim": ["Bunche, Ralph J. (Ralph Johnson), 1904-1971"]},
            False,
        ),
    ],
)
def test_get_record_diff(_summary, r1, r2, is_different):
    result = get_record_diff(r1, r2)
    assert bool(result) == is_different


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ({"dimensions_tesim": ["4 x 5 in. "]}, {"dimensions_tesim": ["4 x 5 in."]}),
        (
            {"named_subject_tesim": ["a", "b "]},
            {"named_subject_tesim": ["a", "b"]},
        ),
    ],
)
def test_normalize_record(value: Any, expected: Any):
    assert normalize_record(value) == expected


class TestNormalizedValue:
    @pytest.mark.parametrize(
        ("field",),
        [
            ("regular",),
            ("subject",),
        ],
    )
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("", None),
            ([""], []),
            ([" "], []),
            ("a", "a"),
            ("  a ", "a"),
            ("\ta ", "a"),
            (["\ta ", "b"], ["a", "b"]),
            (123, 123),
            ("4 x 5 in. ", "4 x 5 in."),
        ],
    )
    def test_normalize_value(self, value: Any, expected: Any, field):
        assert normalize_value(value, field) == expected

    @pytest.mark.parametrize(
        ("value", "field", "expected"),
        [
            ("abc $d xyz", "xyz", "abc xyz"),
            (["abc $d xyz"], "xyz", ["abc xyz"]),
            ("abc $d xyz", "subject", "abc--xyz"),
            (["abc $d xyz"], "subject", ["abc--xyz"]),
        ],
    )
    def test_by_field_type(self, value: Any, expected: Any, field):
        assert normalize_value(value, field) == expected
