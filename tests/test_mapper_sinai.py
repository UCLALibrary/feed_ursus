# mypy: disallow_untyped_defs=False
"""Tests for mapper/sinai.py"""

# pylint: disable=no-self-use

import random

import pytest  # type: ignore

import feed_ursus.mapper.sinai as mapper


class TestVisibility:
    """Tests for mapper.visibility"""

    @pytest.mark.parametrize(
        ["visibility", "expected_result"],
        [
            # Mapping values
            ("authenticated", "authenticated"),
            ("discovery", "sinai"),
            ("open", "open"),
            ("private", "restricted"),
            ("public", "open"),
            ("registered", "authenticated"),
            ("restricted", "restricted"),
            ("sinai", "sinai"),
            ("ucla", "authenticated"),
            # String cleanup
            (" open", "open"),
            ("open       ", "open"),
            ("OPEN", "open"),
        ],
    )
    def test_visibility_included(self, visibility, expected_result):
        """Mappings of the 'visibility' field if included in csv"""
        row = {
            "Visibility": visibility,
            "Item Status": random.choice(("Completed", "Incomplete")),  # ignored
        }

        assert mapper.visibility(row) == expected_result

    @pytest.mark.parametrize(
        ["item_status", "expected_result"],
        [
            ("Completed", "open"),
            ("Completed with minimal metadata", "open"),
            ("Incomplete", "restricted"),
            ("Anything", "restricted"),
            ("Else", "restricted"),
        ],
    )
    def test_visibility_inferred(self, item_status, expected_result):
        """Infer from from 'Item Status' if 'Visibility' not in csv."""

        row = {"Item Status": item_status}
        assert mapper.visibility(row) == expected_result
