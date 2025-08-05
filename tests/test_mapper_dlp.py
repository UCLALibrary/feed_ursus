# mypy: disallow_untyped_defs=False
"""Tests for mapper/dlp.py"""

# pylint: disable=no-self-use

import random

import pytest  # type: ignore

import feed_ursus.mapper.dlp as mapper


class TestVisibility:
    """Tests for mapper.visibility and mapper.access_group"""

    @pytest.mark.parametrize(
        ["visibility", "expected_visibility", "expected_access_group"],
        [
            # Mapping values
            ("authenticated", "authenticated", ["public"]),
            ("discovery", "sinai", []),
            ("open", "open", ["public"]),
            ("private", "restricted", []),
            ("public", "open", ["public"]),
            ("registered", "authenticated", ["public"]),
            ("restricted", "restricted", []),
            ("sinai", "sinai", []),
            ("ucla", "authenticated", ["public"]),
            # String cleanup
            (" open", "open", ["public"]),
            ("open       ", "open", ["public"]),
            ("OPEN", "open", ["public"]),
        ],
    )
    def test_visibility_included(
        self, visibility, expected_visibility, expected_access_group
    ):
        """Mappings of the 'visibility' field if included in csv"""
        row = {
            "Visibility": visibility,
            "Item Status": random.choice(("Completed", "Incomplete")),  # ignored
        }

        assert mapper.visibility(row) == expected_visibility
        assert mapper.access_group(row) == expected_access_group

    @pytest.mark.parametrize(
        ["item_status", "expected_visibility", "expected_access_group"],
        [
            ("Completed", "open", ["public"]),
            ("Completed with minimal metadata", "open", ["public"]),
            ("Incomplete", "restricted", []),
            ("Anything", "restricted", []),
            ("Else", "restricted", []),
        ],
    )
    def test_visibility_inferred(
        self, item_status, expected_visibility, expected_access_group
    ):
        """Infer from from 'Item Status' if 'Visibility' not in csv."""

        row = {"Item Status": item_status}
        assert mapper.visibility(row) == expected_visibility
        assert mapper.access_group(row) == expected_access_group
