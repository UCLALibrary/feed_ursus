"""Tests for feed_ursus.shared_types module.

Tests type annotations, validators, and enums defined in the shared_types __init__.py.
"""

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from feed_ursus import util


class TestEmpty:
    def test_validates_empty_string(self) -> None:
        assert TypeAdapter(util.Empty).validate_strings("") is None

    def test_validates_whitespace(self) -> None:
        assert TypeAdapter(util.Empty).validate_strings(" \t  ") is None

    def test_validates_empty_list(self) -> None:
        assert TypeAdapter(util.Empty).validate_python([]) is None

    def test_rejects_string(self) -> None:
        with pytest.raises(ValidationError):
            TypeAdapter(util.Empty).validate_strings("123")

    def test_rejects_list(self) -> None:
        with pytest.raises(ValidationError):
            TypeAdapter(util.Empty).validate_strings(["123"])

    class TestInUnion:
        class SomeClass(BaseModel):
            a: int | util.Empty

        def test_empty_cell(self):
            assert self.SomeClass.model_validate_json('{"a": ""}').a is None

        def test_with_value(self):
            assert self.SomeClass.model_validate_json('{"a": "123"}').a == 123

        def test_fails_validation(self):
            with pytest.raises(ValidationError) as excinfo:
                self.SomeClass.model_validate_json('{"a": "abc"}')

            assert "Input should be a valid integer" in str(excinfo.value)
            assert "Input should be null" in str(excinfo.value)


class TestMARCString:
    class SomeClass(BaseModel):
        field: util.MARCString

    @pytest.mark.parametrize(
        ["input_str", "expected"],
        [
            ("One $a Two", "One Two"),
            ("$a Start", "Start"),
            ("End $z  ", "End"),
            ("No symbols", "No symbols"),
            (" $b Multiple $c", "Multiple"),
            (" Whitespace  ", "Whitespace"),
        ],
    )
    def test_marc_symbol_parsing(self, input_str: str, expected: str) -> None:
        record = self.SomeClass.model_validate({"field": input_str})
        assert record.field == expected

    def test_min_length(self) -> None:
        with pytest.raises(
            ValidationError,
            match="String should have at least 1 character",
        ):
            self.SomeClass.model_validate({"field": ""})


class TestMARCSubject:
    class SomeClass(BaseModel):
        field: util.MARCSubject

    def test_marc_symbol_parsing(self) -> None:
        record = self.SomeClass.model_validate({"field": "abc $d xyz"})
        assert record.field == "abc | xyz"

    def test_min_length(self) -> None:
        with pytest.raises(
            ValidationError,
            match="String should have at least 1 character",
        ):
            self.SomeClass.model_validate({"field": ""})


class TestMarcList:
    class RandoClass(BaseModel):
        strings: util.MARCList[util.MARCString]
        ints: util.MARCList[int] | util.Empty = None

    @pytest.mark.parametrize(
        ["input_str", "expected"],
        [
            ("Item1|~|Item2|~|Item3", ["Item1", "Item2", "Item3"]),
            ("Single", ["Single"]),
        ],
    )
    def test_parses_list(self, input_str: str, expected: list[str]) -> None:
        record = self.RandoClass.model_validate({"strings": input_str})
        assert record.strings == expected

    def test_uses_MarcString(self) -> None:
        input_str = "parses $s marc $k codes $q|~|  strips whitespace  "
        record = self.RandoClass.model_validate({"strings": input_str})
        assert record.strings == ["parses marc codes", "strips whitespace"]

    def test_raises_marc_errors(self) -> None:
        input_str = "no empty items|~|"
        with pytest.raises(
            ValidationError,
            match="String should have at least 1 character",
        ):
            self.RandoClass.model_validate({"strings": input_str})

    def test_raises_type_errors(self) -> None:
        with pytest.raises(
            ValidationError,
            match="unable to parse string as an integer",
        ):
            self.RandoClass.model_validate({"strings": "123", "ints": "abc"})


class TestArk:
    """Tests the Ark type, which extends shared_types.Ark to add the Ark prefix if necessary."""

    @pytest.mark.parametrize(
        ["item_ark", "expected"],
        [
            ("ark:/21198/abc", "ark:/21198/abc"),
            ("21198/abc", "ark:/21198/abc"),
            ("ark:/21198/abc/xyz", "ark:/21198/abc/xyz"),
            ("21198/abc/xyz", "ark:/21198/abc/xyz"),
        ],
    )
    def test_item_ark_prefix(self, item_ark: str, expected: str) -> None:
        result = util.ark_validator.validate_strings(item_ark)
        assert result == expected

    @pytest.mark.parametrize(
        ["value"],
        [
            ("ark:/abc/abc",),
            (">>>ark:/123/abc",),
            ("ark:/123/abc<<<",),
            ("21198-abc",),
            ("",),
        ],
    )
    def test_errors(self, value: str) -> None:
        with pytest.raises(ValidationError):
            TypeAdapter(util.Ark).validate_strings(value)


class TestUrsusId:
    @pytest.mark.parametrize(
        ["value"],
        [
            ("cba-321",),
            ("654-321",),
        ],
    )
    def test_validates_good_id(self, value: str):
        assert TypeAdapter(util.BaseUrsusId).validate_strings(value) == value

    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            ("ark:/123/abc", "cba-321"),
            ("123/abc", "cba-321"),
        ],
    )
    def test_transforms_good_ark(self, value: str, expected: str):
        assert TypeAdapter(util.UrsusId).validate_strings(value) == expected

    @pytest.mark.parametrize(
        ["value"],
        [
            ("ark:/123/&%4",),  # invalid characters
            ("ark:/abc/123",),  # first part of ARK must be a number
            ("123-abc",),  # last part of ursus ID must be a number
            (">>>654-321",),  # invalid characters at start of string
            ("654-321<<<",),  # invalid characters at end of string
        ],
    )
    def test_raises_errors(self, value: str):
        with pytest.raises(ValidationError):
            assert TypeAdapter(util.UrsusId).validate_strings(value)
