# mypy: disallow_untyped_defs=False
"""Tests for mapper/dlp.py"""

# pylint: disable=no-self-use

import random
from math import e

import pytest  # type: ignore

import feed_ursus.mapper.dlp as mapper


class TestArchivalCollection:
    def test_all_fields(self):
        row = {
            "Box": "4",
            "Folder": "5",
            "Archival Collection Number": "123",
            "Archival Collection Title": "Boring Collection",
        }
        expected = "Boring Collection (123), Box 4, Folder 5"

        assert mapper.archival_collection(row) == expected

    def test_says_box_or_folder(self):
        row = {
            "Box": "box 4",
            "Folder": " Folder 5",
            "Archival Collection Number": "123",
            "Archival Collection Title": "Boring Collection",
        }
        expected = "Boring Collection (123), Box 4, Folder 5"

        assert mapper.archival_collection(row) == expected

    def test_no_collection_number(self):
        row = {
            "Box": "4",
            "Folder": "5",
            "Archival Collection Title": "Boring Collection",
        }
        expected = "Boring Collection, Box 4, Folder 5"

        assert mapper.archival_collection(row) == expected

    def test_no_collection_title(self):
        row = {
            "Box": "4",
            "Folder": "5",
            "Archival Collection Number": "123",
            "Archival Collection Title": "",
        }
        expected = "Archival Collection 123, Box 4, Folder 5"

        assert mapper.archival_collection(row) == expected

    def test_no_collection_title_or_number(self):
        row = {
            "Box": "4",
            "Folder": "5",
            "Archival Collection Number": "",
            "Archival Collection Title": "",
        }
        expected = "Boring Collection (123), Box 4, Folder 5"

        assert mapper.archival_collection(row) == None

    def test_no_box(self):
        row = {
            "Folder": "5",
            "Archival Collection Number": "123",
            "Archival Collection Title": "Boring Collection",
        }
        expected = "Boring Collection (123), Folder 5"

        assert mapper.archival_collection(row) == expected

    def test_no_folder(self):
        row = {
            "Box": "4",
            "Archival Collection Number": "123",
            "Archival Collection Title": "Boring Collection",
        }
        expected = "Boring Collection (123), Box 4"

        assert mapper.archival_collection(row) == expected

    def test_no_box_or_folder(self):
        row = {
            "Archival Collection Number": "123",
            "Archival Collection Title": "Boring Collection",
        }
        expected = "Boring Collection (123)"

        assert mapper.archival_collection(row) == expected


class TestResourceTypeID:
    def test_single_value(self):
        row = {"Type.typeOfResource": "cartographic"}
        expected = ["http://id.loc.gov/vocabulary/resourceTypes/car"]

        assert mapper.resource_type_id(row) == expected

    def test_multi_value(self):
        row = {
            "Type.typeOfResource": "moving image|~|sound recording|~|sound recording-musical|~|sound recording-nonmusical"
        }
        expected = [
            "http://id.loc.gov/vocabulary/resourceTypes/mov",
            "http://id.loc.gov/vocabulary/resourceTypes/aud",
            "http://id.loc.gov/vocabulary/resourceTypes/aum",
            "http://id.loc.gov/vocabulary/resourceTypes/aun",
        ]

        assert mapper.resource_type_id(row) == expected

    def test_empty(self):
        row = {"Type.typeOfResource": ""}
        expected: list[str] = []

        assert mapper.resource_type_id(row) == expected
        assert mapper.resource_type_id(row) == expected

    def test_none(self):
        row = {"Type.typeOfResource": ""}
        expected: list[str] = []

        assert mapper.resource_type_id(row) == expected

    def test_not_in_csv(self):
        row: dict[str, str] = {}
        expected: list[str] = []

        assert mapper.resource_type_id(row) == expected


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
            # Column is present but empty for row
            ("", "open", ["public"]),
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
    def test_visibility_inferred_from_item_status(
        self, item_status, expected_visibility, expected_access_group
    ):
        """Infer from from 'Item Status' if 'Visibility' not in csv."""

        row = {"Item Status": item_status}
        assert mapper.visibility(row) == expected_visibility
        assert mapper.access_group(row) == expected_access_group

    def test_no_visibility_or_satus(self):
        assert mapper.visibility({}) == "open"
        assert mapper.access_group({"Item Status": ""}) == ["public"]
