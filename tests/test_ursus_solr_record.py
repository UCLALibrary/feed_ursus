"""Tests for solr_record.py"""

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from feed_ursus.controlled_fields import (
    ObjectType,
    RightsStatement,
    Visibility,
)
from feed_ursus.ursus_solr_record import UrsusSolrRecord

MINIMAL_RECORD: dict[str, Any] = {
    "Item ARK": "ark:/123/test",
    "Title": "Test Item",
}


class TestUrsusSolrRecord:
    def test_basic_validation(self) -> None:
        record = UrsusSolrRecord.model_validate({**MINIMAL_RECORD})
        assert isinstance(record, UrsusSolrRecord)

    class TestRightsStatement:
        @pytest.mark.parametrize(
            ["input", "expected"],
            [
                ("unknown", ["http://vocabs.library.ucla.edu/rights/unknown"]),
                ("copyrighted", ["http://vocabs.library.ucla.edu/rights/copyrighted"]),
                (
                    "public domain",
                    ["http://vocabs.library.ucla.edu/rights/publicDomain"],
                ),
                ("pd", ["http://vocabs.library.ucla.edu/rights/publicDomain"]),
                ("", None),
                (None, None),
            ],
        )
        def test_good_rights_statement(
            self,
            input: str | None,
            expected: RightsStatement | None,
        ) -> None:
            result = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Rights.copyrightStatus": input,
                }
            )
            assert result.rights_statement_tesim == expected

        def test_bad_rights_statement(self) -> None:
            with pytest.raises(ValidationError):
                UrsusSolrRecord.model_validate(
                    {
                        **MINIMAL_RECORD,
                        "Rights.copyrightStatus": "probably fine",
                    }
                )

    class TestComputedArchivalCollection:
        def test_all_fields(self) -> None:
            row = MINIMAL_RECORD | {
                "Box": "4",
                "Folder": "5",
                "Archival Collection Number": "123",
                "Archival Collection Title": "Boring Collection",
            }
            expected = "Boring Collection (123), Box 4, Folder 5"

            assert (
                UrsusSolrRecord.model_validate(
                    row,
                    by_name=True,
                ).archival_collection_tesi
                == expected
            )

        def test_says_box_or_folder(self) -> None:
            row = MINIMAL_RECORD | {
                "Box": "box 4",
                "Folder": " Folder 5",
                "Archival Collection Number": "123",
                "Archival Collection Title": "Boring Collection",
            }
            expected = "Boring Collection (123), Box 4, Folder 5"

            assert (
                UrsusSolrRecord.model_validate(row).archival_collection_tesi == expected
            )

        def test_no_collection_number(self) -> None:
            row = MINIMAL_RECORD | {
                "Box": "4",
                "Folder": "5",
                "Archival Collection Title": "Boring Collection",
            }
            expected = "Boring Collection, Box 4, Folder 5"

            assert (
                UrsusSolrRecord.model_validate(row).archival_collection_tesi == expected
            )

        def test_no_collection_title(self) -> None:
            row = MINIMAL_RECORD | {
                "Box": "4",
                "Folder": "5",
                "Archival Collection Number": "123",
                "Archival Collection Title": "",
            }
            expected = "Archival Collection 123, Box 4, Folder 5"

            assert (
                UrsusSolrRecord.model_validate(row).archival_collection_tesi == expected
            )

        def test_no_collection_title_or_number(self) -> None:
            row = MINIMAL_RECORD | {
                "Box": "4",
                "Folder": "5",
                "Archival Collection Number": "",
                "Archival Collection Title": "",
            }

            assert UrsusSolrRecord.model_validate(row).archival_collection_tesi is None

        def test_no_box(self) -> None:
            row = MINIMAL_RECORD | {
                "Folder": "5",
                "Archival Collection Number": "123",
                "Archival Collection Title": "Boring Collection",
            }
            expected = "Boring Collection (123), Folder 5"

            assert (
                UrsusSolrRecord.model_validate(row).archival_collection_tesi == expected
            )

        def test_no_folder(self) -> None:
            row = MINIMAL_RECORD | {
                "Box": "4",
                "Archival Collection Number": "123",
                "Archival Collection Title": "Boring Collection",
            }
            expected = "Boring Collection (123), Box 4"

            assert (
                UrsusSolrRecord.model_validate(row).archival_collection_tesi == expected
            )

        def test_no_box_or_folder(self) -> None:
            row = MINIMAL_RECORD | {
                "Archival Collection Number": "123",
                "Archival Collection Title": "Boring Collection",
            }
            expected = "Boring Collection (123)"

            assert (
                UrsusSolrRecord.model_validate(row).archival_collection_tesi == expected
            )

    class TestCoordinates:
        """Tests for latitude and longitude same length validator"""

        def test_same_length(self) -> None:
            record = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Description.latitude": "1.0|~|2.0",
                    "Description.longitude": "3.0|~|4.0",
                }
            )
            assert record.latitude_tesim == ["1.0", "2.0"]
            assert record.longitude_tesim == ["3.0", "4.0"]
            assert record.geographic_coordinates_ssim == ["1.0, 3.0", "2.0, 4.0"]

        def test_different_length(self) -> None:
            with pytest.raises(ValueError, match="Mismatched lengths:"):
                UrsusSolrRecord.model_validate(
                    {
                        **MINIMAL_RECORD,
                        "Description.latitude": "1.0|~|2.0",
                        "Description.longitude": "3.0",
                    }
                )

    class TestHasModel:
        """Tests for Object_Type enum parsing. The class does some mapping"""

        @pytest.mark.parametrize(
            ["object_type", "expected"],
            [
                ("ChildWork", ObjectType.CHILD_WORK),
                ("Page", ObjectType.CHILD_WORK),
                ("Work", ObjectType.WORK),
                ("Manuscript", ObjectType.WORK),
                ("Collection", ObjectType.COLLECTION),
                ("", ObjectType.WORK),  # Default
                (None, ObjectType.WORK),  # Default
            ],
        )
        def test_object_type_mapping(
            self,
            object_type: str,
            expected: ObjectType,
        ) -> None:
            record = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Object Type": object_type,
                }
            )
            assert record.has_model_ssim == expected

        def test_no_object_type(self) -> None:
            record = UrsusSolrRecord.model_validate(MINIMAL_RECORD)
            assert record.has_model_ssim == ObjectType.WORK

        def test_object_type_error(self) -> None:
            with pytest.raises(
                ValidationError,
                match="Input should be 'Collection', 'Work' or 'ChildWork'",
            ):
                UrsusSolrRecord.model_validate(
                    {**MINIMAL_RECORD, "Object Type": "Invalid"}
                )

    class TestLanguage:
        """Tests for language field parsing"""

        @pytest.mark.parametrize(
            ["input", "ids", "names"],
            [
                ("eng", ["eng"], ["English"]),
                ("eng|~|fre", ["eng", "fre"], ["English", "French"]),
                ("", None, None),
            ],
        )
        def test_language_parsing(
            self,
            input: str,
            ids: list[str] | None,
            names: list[str] | None,
        ) -> None:
            serialized = UrsusSolrRecord.model_validate(
                {**MINIMAL_RECORD, "Language": input}
            ).model_dump(mode="json")

            assert serialized["human_readable_language_tesim"] == names
            assert serialized["human_readable_language_sim"] == names
            assert serialized["language_sim"] == ids
            assert serialized["language_tesim"] == ids

        def test_unknown_language(self) -> None:
            with pytest.raises(ValidationError):
                UrsusSolrRecord.model_validate(
                    {**MINIMAL_RECORD, "Language": "eng|~|invalid"}
                )

    class TestRelatedRecord:
        def test_both_blank(self) -> None:
            result = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Related Records": None,
                    "human_readable_related_record_title_ssm": None,
                }
            )
            assert result.related_record_ssm == None
            assert result.human_readable_related_record_title_ssm == None

        def test_equal_length(self) -> None:
            result = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Related Records": ["ark:/21198/abc123", "ark:/21198/abc456"],
                    "human_readable_related_record_title_ssm": ["Title 1", "Title 2"],
                }
            )
            assert result.related_record_ssm == [
                "ark:/21198/abc123",
                "ark:/21198/abc456",
            ]
            assert result.human_readable_related_record_title_ssm == [
                "Title 1",
                "Title 2",
            ]

        def test_different_length(self) -> None:
            with pytest.raises(
                ValidationError,
                match="Value error, related_record_ssm and human_readable_related_record_title_ssm must be of equal length",
            ):
                UrsusSolrRecord.model_validate(
                    {
                        **MINIMAL_RECORD,
                        "Related Records": "ark:/21198/abc123|~|ark:/21198/abc456",
                        "human_readable_related_record_title_ssm": ["Title 1"],
                    }
                )

        def test_only_ids(self) -> None:
            with pytest.raises(
                ValidationError,
                match="Value error, related_record_ssm and human_readable_related_record_title_ssm must be of equal length",
            ):
                UrsusSolrRecord.model_validate(
                    {
                        **MINIMAL_RECORD,
                        "Related Records": "ark:/21198/abc123",
                    }
                )

        def test_only_titles(self) -> None:
            with pytest.raises(
                ValidationError,
                match="Value error, related_record_ssm and human_readable_related_record_title_ssm must be of equal length",
            ):
                UrsusSolrRecord.model_validate(
                    {
                        **MINIMAL_RECORD,
                        "human_readable_related_record_title_ssm": ["Title 1"],
                    }
                )

    def test_computed_uniform_title_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "AltTitle.uniform": "Uniform Title",
            }
        )
        assert record.uniform_title_sim == ["Uniform Title"]

    def test_computed_uniform_title_sim_empty(self) -> None:
        record = UrsusSolrRecord.model_validate(MINIMAL_RECORD)
        assert record.uniform_title_sim is None

    # Add more tests for other computed fields as needed
    def test_computed_architect_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Name.architect": ["Arch1"],
            }
        )
        assert record.architect_sim == ["Arch1"]

    def test_computed_author_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Author": ["Auth1"],
            }
        )
        assert record.author_sim == ["Auth1"]

    def test_computed_illuminator_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Name.illuminator": ["Ill1"],
            }
        )
        assert record.illuminator_sim == ["Ill1"]

    def test_computed_scribe_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Scribe": ["Scr1"],
            }
        )
        assert record.scribe_sim == ["Scr1"]

    def test_computed_rubricator_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Name.rubricator": ["Rub1"],
            }
        )
        assert record.rubricator_sim == ["Rub1"]

    def test_computed_commentator_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Name.commentator": ["Com1"],
            }
        )
        assert record.commentator_sim == ["Com1"]

    def test_computed_translator_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Translator": ["Tra1"],
            }
        )
        assert record.translator_sim == ["Tra1"]

    def test_computed_lyricist_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Name.lyricist": ["Lyr1"],
            }
        )
        assert record.lyricist_sim == ["Lyr1"]

    def test_computed_composer_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Name.composer": ["Comp1"],
            }
        )
        assert record.composer_sim == ["Comp1"]

    def test_computed_illustrator_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Illustrator": ["Illu1"],
            }
        )
        assert record.illustrator_sim == ["Illu1"]

    def test_computed_editor_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Editor": ["Edit1"],
            }
        )
        assert record.editor_sim == ["Edit1"]

    def test_computed_calligrapher_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Calligrapher": ["Call1"],
            }
        )
        assert record.calligrapher_sim == ["Call1"]

    def test_computed_engraver_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "Engraver": ["Eng1"],
            }
        )
        assert record.engraver_sim == ["Eng1"]

    @pytest.mark.parametrize(
        ["file_name", "expected"],
        [
            ("test.jpg", "Masters/test.jpg"),
            ("Masters/test.jpg", "Masters/test.jpg"),
            ("", None),
            ("folder/file.png", "Masters/folder/file.png"),
        ],
    )
    def test_preservation_copy(self, file_name: str, expected: str) -> None:
        record = UrsusSolrRecord.model_validate(
            {**MINIMAL_RECORD, "File Name": file_name}
        )
        assert record.preservation_copy_ssi == expected

    def test_computed_printmaker_sim(self) -> None:
        record = UrsusSolrRecord.model_validate(
            {
                **MINIMAL_RECORD,
                "printmaker_tesim": ["Print1"],
            }
        )
        assert record.printmaker_sim == ["Print1"]

    class TestResourceTypeSerializer:
        def test_single_value(self) -> None:
            result = UrsusSolrRecord.model_validate(
                {**MINIMAL_RECORD, "Type.typeOfResource": "cartographic"}
            ).model_dump()
            expected = ["http://id.loc.gov/vocabulary/resourceTypes/car"]

            assert result["resource_type_sim"] == expected

        def test_multi_value(self) -> None:
            result = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Type.typeOfResource": "moving image|~|sound recording|~|sound recording-musical|~|sound recording-nonmusical",
                }
            ).model_dump()["resource_type_sim"]
            expected = [
                "http://id.loc.gov/vocabulary/resourceTypes/mov",
                "http://id.loc.gov/vocabulary/resourceTypes/aud",
                "http://id.loc.gov/vocabulary/resourceTypes/aum",
                "http://id.loc.gov/vocabulary/resourceTypes/aun",
            ]

            assert result == expected

        def test_unknown_value(self) -> None:
            with pytest.raises(ValidationError, match="Input should be"):
                UrsusSolrRecord.model_validate(
                    {**MINIMAL_RECORD, "Type.typeOfResource": ["physical object"]}
                )

        def test_empty(self) -> None:
            result = UrsusSolrRecord.model_validate(
                {**MINIMAL_RECORD, "Type.typeOfResource": ""}
            ).model_dump(exclude_defaults=True)
            assert result["resource_type_sim"] == None

        def test_default(self) -> None:
            result = UrsusSolrRecord.model_validate(MINIMAL_RECORD)

            assert result.resource_type_sim == None

    class TestVisibility:
        @pytest.mark.parametrize(
            ["visibility"],
            [
                ("authenticated",),
                ("private",),
                ("registered",),
                ("restricted",),
                ("discovery",),
                ("sinai",),
            ],
        )
        @pytest.mark.parametrize(
            ["item_status"],
            [
                ("Completed",),
                ("Completed with minimal metadata",),
                ("Incomplete",),
                ("",),
                (None,),
            ],
        )
        def test_visibility_authenticated(self, visibility: str, item_status: str):
            record = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Visibility": visibility,
                    "Item Status": item_status,
                }
            )
            assert record.visibility_ssi == Visibility.AUTHENTICATED

        @pytest.mark.parametrize(
            ["visibility"],
            [
                ("open",),
                ("public",),
                ("",),  # Column present but cell empty
            ],
        )
        @pytest.mark.parametrize(
            ["item_status"],
            [
                ("Completed",),
                ("Completed with minimal metadata",),
                ("Incomplete",),
                ("",),
                (None,),
            ],
        )
        def test_visibility_open(self, visibility: str, item_status: str):
            record = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Visibility": visibility,
                    "Item Status": item_status,
                }
            )
            assert record.visibility_ssi == Visibility.OPEN

        @pytest.mark.parametrize(
            ["item_status", "expected"],
            [
                ("Completed", Visibility.OPEN),
                ("Completed with minimal metadata", Visibility.OPEN),
                ("Incomplete", Visibility.AUTHENTICATED),
                ("Anything Else", Visibility.AUTHENTICATED),
                ("", Visibility.AUTHENTICATED),
                (None, Visibility.OPEN),
            ],
        )
        def test_visibility_from_status(self, item_status: str, expected: Visibility):
            record = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Item Status": item_status,
                }
            )
            assert record.visibility_ssi == expected

    class TestDateDtsort:
        def test_single(self) -> None:
            result = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Date.normalized": ["1980"],
                }
            ).date_dtsort

            assert result == "1980-01-01T00:00:00Z"

        def test_range(self) -> None:
            result = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Date.normalized": ["1980/2026"],
                }
            ).date_dtsort

            assert result == "1980-01-01T00:00:00Z"

        def test_empty(self) -> None:
            assert UrsusSolrRecord.model_validate(MINIMAL_RECORD).date_dtsort is None

    def test_title_required(self) -> None:
        record_without_title = deepcopy(MINIMAL_RECORD)
        record_without_title.pop("Title")

        with pytest.raises(ValidationError, match=r"Title\s*Field required"):
            UrsusSolrRecord.model_validate(record_without_title)

    class TestYear:
        def test_single(self) -> None:
            result = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Date.normalized": ["1980"],
                }
            ).year_isim

            assert result == [1980]

        def test_range(self) -> None:
            result = UrsusSolrRecord.model_validate(
                {
                    **MINIMAL_RECORD,
                    "Date.normalized": ["1980/2026"],
                }
            ).year_isim

            assert result == list(range(1980, 2027))

        def test_none(self) -> None:
            result = UrsusSolrRecord.model_validate(MINIMAL_RECORD).year_isim

            assert result == None

    def test_handle_empty_cells(self) -> None:
        result = UrsusSolrRecord.model_validate(MINIMAL_RECORD).alternative_title_tesim
        assert result is None

    class TestValidateComputedFields:
        def test_valid_computed_fields_match(self) -> None:
            # Provide computed field values that match what the model would compute
            data = MINIMAL_RECORD | {
                "architect_tesim": ["Arch1"],
                "architect_sim": ["Arch1"],  # matches computed
            }
            record = UrsusSolrRecord.model_validate(data, by_name=True, by_alias=False)
            assert record.architect_sim == ["Arch1"]

        def test_valid_enum_vs_string(self) -> None:
            # validates to ResourceType enum member, which a naive validator would reject as not matching the input
            data = MINIMAL_RECORD | {
                "human_readable_resource_type_tesim": ["still image"],
                "human_readable_resource_type_sim": ["still image"],
            }
            record = UrsusSolrRecord.model_validate(data, by_name=True, by_alias=False)
            assert record.human_readable_resource_type_sim == ["still image"]

        def test_invalid_computed_field_raises(self) -> None:
            # Provide a computed field value that does not match what the model would compute
            data = MINIMAL_RECORD | {
                "architect_tesim": ["Arch1"],
                "architect_sim": ["WrongValue"],  # does not match computed
            }

            with pytest.raises(
                ValueError,
                match="Inputs do not match computed:",
            ) as excinfo:
                UrsusSolrRecord.model_validate(data)

        def test_multiple_invalid_computed_fields(self) -> None:
            # Multiple computed fields do not match
            data = MINIMAL_RECORD | {
                "architect_tesim": ["Arch1"],
                "architect_sim": ["WrongValue"],
                "Author": ["Author1"],
                "author_sim": ["WrongAuthor"],
            }

            with pytest.raises(ValueError) as excinfo:
                UrsusSolrRecord.model_validate(data)
            # Both fields should be listed
            assert "architect_sim" in str(excinfo.value)
            assert "author_sim" in str(excinfo.value)

        def test_no_computed_fields_in_input(self) -> None:
            # No computed fields provided, should validate fine
            data = MINIMAL_RECORD | {
                "architect_tesim": ["Arch1"],
            }
            record = UrsusSolrRecord.model_validate(data)
            assert record.architect_sim == ["Arch1"]

        def test_computed_field_missing_in_input(self) -> None:
            # If computed field is missing in input, should not raise
            data = MINIMAL_RECORD | {
                "architect_tesim": [],
            }
            record = UrsusSolrRecord.model_validate(data)
            assert record.architect_sim is None

        def test_computed_field_with_empty_string(self) -> None:
            # If computed field is empty string but computed is None, should raise
            data = MINIMAL_RECORD | {
                "architect_tesim": [],
                "architect_sim": "",
            }

            with pytest.raises(ValueError) as excinfo:
                UrsusSolrRecord.model_validate(data)

            assert "architect_sim" in str(excinfo.value)

        def test_computed_field_with_extra_fields(self) -> None:
            # Extra unrelated fields should not affect validation
            data = MINIMAL_RECORD | {
                "architect_tesim": ["Arch1"],
                "some_unrelated_field": "foo",
            }
            record = UrsusSolrRecord.model_validate(data)
            assert record.architect_sim == ["Arch1"]

    @pytest.mark.parametrize(
        ["bad_data"],
        [
            ({"visibility_ssi": "sinai"},),
            ({"latitude_tesim": None, "longitude_tesim": ["-118.847769"]},),
            (
                {
                    "related_record_ssm": ["ARK:/21198/zz002jgs66"],
                    "human_readable_related_record_title_ssm": None,
                },
            ),
        ],
    )
    def test_less_strict(self, bad_data: dict):
        record = {
            **MINIMAL_RECORD,
            **bad_data,
        }

        with pytest.raises(ValidationError):
            UrsusSolrRecord.model_validate(record)

        UrsusSolrRecord.less_strict().model_validate(record)
