# pyright: standard

import re
from collections.abc import Iterable
from copy import deepcopy
from enum import Enum
from typing import Any

from deepdiff import DeepDiff
from deepdiff.helper import COLORED_VIEW

from feed_ursus.controlled_fields import (
    ResourceType,
    RightsStatement,
    TextDirection,
    ViewingHint,
)
from feed_ursus.less_strict_solr_record import LessStrictSolrRecord
from feed_ursus.util import deduplicate, parse_marc


class UnexplainedChangesError(ValueError):
    pass


#
#   Core reindexing logic
#


def reindex_record(record: Any) -> dict[str, Any]:  # noqa: ANN401 (any-type)
    fixed = fix_for_reindex(deepcopy(record))
    validated = LessStrictSolrRecord.model_validate(fixed).model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )

    if normalized_diff := get_record_diff(fixed, validated):
        # rich.print(Rule(title=get_handle(record)))
        # print(normalized_diff)
        raise UnexplainedChangesError(normalized_diff)

    return validated


#
#   Fixes for existing data issues
#


def fix_for_reindex(record: Any) -> dict[str, Any]:  # noqa: ANN401 (any-type)
    if not (
        isinstance(record, dict)
        and all(isinstance(fieldname, str) for fieldname in record)
    ):
        raise ValueError("record must be of type dict[str, Any]")

    # Remove solr internal stuff
    record.pop("_version_", None)

    # In some instances we find metadata in what we now treat as a computed field, but not in field it gets sourced from
    for base_field, computed_field, enum_cls in [
        (
            "human_readable_rights_statement_tesim",
            "rights_statement_tesim",
            RightsStatement,
        ),
        (
            "human_readable_resource_type_tesim",
            "resource_type_tesim",
            ResourceType,
        ),
        (
            "human_readable_iiif_viewing_hint_ssi",
            "iiif_viewing_hint_ssi",
            ViewingHint,
        ),
        (
            "human_readable_iiif_text_direction_ssi",
            "iiif_text_direction_ssi",
            TextDirection,
        ),
    ]:
        record = relocate_computed_field(
            record,
            base_field,
            computed_field,
            enum_cls,
        )

    if "collation_ssi" in record and "collation_tesim" not in record:
        record["collation_tesim"] = [record.pop("collation_ssi")]

    if "foliation_ssi" in record and "foliation_tesim" not in record:
        record["foliation_tesim"] = [record.pop("foliation_ssi")]

    # use list(dict.fromkeys().keys()) to get deduplicated list/ordered set
    if local_ids := deduplicate(
        record.pop("local_identifier_ssim", []),
        record.pop("local_identifier_ssm", []),
        record.pop("local_identifier_sim", []),
    ):
        record["local_identifier_ssim"] = local_ids

    return record


def relocate_computed_field(
    record: dict[str, Any],
    base_field: str,
    computed_field: str,
    enum_cls: type[Enum] | None,
) -> dict[str, Any]:
    cf_value = record.pop(computed_field, None)

    if base_field in record or not cf_value:
        return record

    if not enum_cls:
        record[base_field] = cf_value
    elif isinstance(cf_value, str):
        record[base_field] = (
            enum_cls[cf_value].value if cf_value in enum_cls.__members__ else cf_value
        )
    elif isinstance(cf_value, list):
        record[base_field] = [
            enum_cls[item].value if item in enum_cls.__members__ else item
            for item in cf_value
        ]
    else:
        record[base_field] = cf_value

    return record


#
#   Analysis to detect unanticipated changes to the data
#


def get_record_diff(
    original_record: dict[Any, Any],
    new_record: dict[Any, Any],
) -> DeepDiff:
    remove_access = {"registered"}
    if original_record.get("visibility_ssi") == "sinai":
        remove_access.add("public")

    for field in original_record:
        if (
            isinstance(field, str)
            and field.endswith(("_access_group_ssim", "_access_person_ssim"))
            and isinstance(original_record[field], list)
        ):
            original_record[field] = list(
                {
                    value
                    for value in original_record[field]
                    if value not in remove_access
                }
            )

    exclude_paths = [
        "resource_type_sim",  # computed from human_readable; sometimes label replaced with id
        "accessControl_ssim",  # hyrax stuff
        "admin_set_sim",  # hyrax stuff
        "admin_set_tesim",  # hyrax stuff
        "archival_collection_tesi",  # computed field that was done badly in some of our existing data
        "collection_sim",  # should be member_of_collections_ssim
        "collection_ssi",  # should be member_of_collections_ssim
        "collection_type_gid_ssim",  # hyrax stuff
        "combined_names_ssim",  # not finding this used in Ursus or Sinai, but I think it was a Sinai field at one point?
        "date_dtsim",  # derived from normalized_date_tesim; a lot of issues with past implementation
        "date_dtsort",  # derived from normalized_date_tesim; a lot of issues with past implementation
        "date_modified_dtsi",  # hyrax stuff
        "date_uploaded_dtsi",  # hyrax stuff
        "depositor_ssim",  # hyrax stuff
        "depositor_tesim",  # hyrax stuff
        "discover_access_group_ssim",  # derivation from "visibility" looks good - errors are bad data
        "discover_access_person_ssim",  # should be _group
        "dlcs_collection_name_sim",  # outdated: use member_of_collections_ssim
        "dlcs_collection_name_ssm",  # outdated: use member_of_collections_ssim
        "download_access_group_ssim",  # derivation from "visibility" looks good - errors are bad data
        "download_access_person_ssim",  # should be _group
        "edit_access_group_ssim",  # hyrax stuff
        "edit_access_person_ssim",  # hyrax stuff
        "file_set_ids_ssim",  # hyrax stuff
        "generic_type_sim",  # related to (unused) blacklight user accounts - only non-spec Ursus use at https://github.com/UCLALibrary/ursus/blob/6293d19686ca27de3549e1c2a04885c6e71544e4/app/controllers/catalog_controller.rb#L173
        "hashed_id_ssi",  # hyrax stuff
        "hasRelatedImage_ssim",  # hyrax stuff
        "hasRelatedMediaFragment_ssim",  # hyrax stuff
        "human_readable_type_sim",  # hyrax stuff - duplicate of has_model_ssim
        "human_readable_type_tesim",  # hyrax stuff - duplicate of has_model_ssim
        "isPartOf_ssim",  # hyrax stuff
        "keywords_sim",  # sinai
        "keywords_tesim",  # sinai
        "member_ids_ssim",  # hyrax stuff
        "nesting_collection__ancestors_ssim",  # hyrax stuff
        "nesting_collection__deepest_nested_depth_isi",  # hyrax stuff
        "nesting_collection__parent_ids_ssim",  # hyrax stuff
        "nesting_collection__pathnames_ssim",  # hyrax stuff
        "read_access_group_ssim",  # derivation from "visibility" looks good - errors are bad data
        "read_access_person_ssim",  # should be _group
        "recalculate_size_bsi",  # Californica-specific
        "record_origin_ssi",  # discontinued from feed_ursus/californica changeover
        "references_sim",  # sinai
        "references_tesim",  # sinai
        "reindex_timestamp_dtsi",  # vauge memory of using this in a californica reindex?
        "score",  # solr internal
        "sort_title_ssort",  # not stored
        "sort_year_isi",  # outdated - use sort_year_dtsort
        "suppressed_bsi",  # hyrax stuff?
        "thumbnail_link_ssi",  # sinai only - ursus uses thumbnail_url_ss
        "thumbnail_path_ss",  # outdated - use thumbnail_url_ss
        "timestamp",  # solr internal
        "title_sim",  # not stored
        "ursus_id_ssi",  # outdated – use just plain 'id'
        "year_isim",  # derived from normalized_date_tesim; a lot of issues with past implementation
    ]

    # if a language code is in language_tesim, it should get deleted from the human_readable_language fields
    for language in original_record.get("language_tesim", []):
        for field in ("human_readable_language_tesim", "human_readable_language_sim"):
            original_record.pop(field, None)

    diff = DeepDiff(
        normalize_record(original_record),
        normalize_record(new_record),
        ignore_order=True,
        exclude_paths=exclude_paths,
        view=COLORED_VIEW,
    )

    # removing these will prevent them from making the diff truthy,
    # but they'll still show up in print(diff)
    diff.pop("dictionary_item_added", None)
    diff.pop("iterable_item_added", None)

    return diff


def normalize_record(record: Any) -> Any:  # noqa: ANN401 (any-type)
    if not isinstance(record, dict):
        return record

    if "access_copy_ssi" in record:
        record["access_copy_ssi"] = record["access_copy_ssi"].replace("{}", "%7B%7D")

    # remove falsy values and return
    return {
        key: normalize_value(value, key)
        for key, value in record.items()
        if normalize_value(value, key) not in (None, [], "")
    }


TIME_PORTION_REGEX = re.compile(r"T\d\d:\d\d:\d\dZ")
QUICK_FIXES: dict[tuple[str, str], str] = {
    (
        "rights_statement_tesim",
        "unknown",
    ): "http://vocabs.library.ucla.edu/rights/unknown",
    (
        "rights_statement_tesim",
        "copyrighted",
    ): "http://vocabs.library.ucla.edu/rights/copyrighted",
    (
        "iiif_viewing_hint_ssi",
        "individuals",
    ): "http://iiif.io/api/presentation/2#individualsHint",
    (
        "rights_statement_tesim",
        "public domain",
    ): "http://vocabs.library.ucla.edu/rights/publicDomain",
}


def normalize_value(value: Any, field_name: str = "") -> Any:  # noqa: ANN401 (any-type)
    match field_name, value:
        case "date_dtsim" | "date_dtsort", str():
            # ignore the time portion of timestamps
            return TIME_PORTION_REGEX.sub("", value)
        case _, str():
            # if (field_name, value) in QUICK_FIXES:
            #     return QUICK_FIXES[(field_name, value)]

            result = parse_marc(
                value,
                marc_symbol_replacement="--" if ("subject" in field_name) else " ",
            )
            return result.strip() if result else None
        case _, Iterable():
            # Make sure to handle Iterable *after* str – strings are also Iterables
            return [
                normalize_value(item, field_name)
                for item in value
                if normalize_value(item, field_name)
            ]
        case _, _:
            return value
