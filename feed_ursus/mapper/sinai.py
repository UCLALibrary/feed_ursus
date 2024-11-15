# -*- coding: utf-8 -*-
"""Mapping logic for UCLA CSV->Blacklight conversion."""

import typing

# import urllib.parse


def ark(row: typing.Mapping[str, str]) -> str:
    """The item ARK (Archival Resource Key)

    Args:
        row: An input CSV record.

    Returns:
        The item ARK.
    """
    ark_prefix = "ark:/"
    if row["Item ARK"].startswith(ark_prefix, 0):
        return row["Item ARK"]
    return ark_prefix + row["Item ARK"]


def object_type(row: typing.Mapping[str, str]) -> str:
    """Object Type. Defaults to "Work", can also be 'ChildWork', or 'Collection'.

    Args:
        row: An input CSV record.

    Returns:
        Object type.
    """
    if "Object Type" not in row:
        return "Work"

    synonyms = {
        "Manuscript": "Work",
        "Page": "ChildWork",
    }

    if row["Object Type"] in synonyms:
        return synonyms[row["Object Type"]]

    return row["Object Type"]


def preservation_copy(row: typing.Mapping[str, str]) -> typing.Optional[str]:
    """A path to the original digital asset in the 'Masters/' netapp mount.

    If the File Name starts with "Masters/", it will be used as is. Otherwise,
    it will be prepended with "Masters/dlmasters/", in order to match the
    content of DLCS exports.

    Args:
        row: An input CSV record.

    Returns:
        String representing a path, or None.
    """

    file_path = row.get("File Name")
    if not file_path:
        return None
    if not str(file_path).startswith("Masters/"):
        return f"Masters/{file_path}"
    return file_path


def thumbnail_url(row: typing.Mapping[str, str]) -> typing.Optional[str]:
    """A thumbnail URL.

    Args:
        row: An input CSV record.

    Returns:
        The thumbnail URL.
    """
    if row.get("Thumbnail URL"):
        return row["Thumbnail URL"]

    if row.get("IIIF Access URL"):
        return row["IIIF Access URL"] + "/full/!200,200/0/default.jpg"

    return None


def visibility(row: typing.Mapping[str, str]) -> typing.Optional[str]:
    """Object visibility.

    A single-value field that must contain one of the allowed values.

    This field is not required. If leave the value blank, it will default to
    `public` visibility. If you omit the column, this will trigger a more
    complicated procedure to determine the visibility of DLCS imports (see
    below).

    Allowed values:
    - `public` - All users can view the record
    - `authenticated` - Logged in users can view the record
    - `sinai` - For Sinai Library items. All californica users can vsiew the
       metadata, but not the files. Hidden from the public-facing site as of
       Nov 2019.
    - `discovery` - A synonym of `sinai`. Not recommended for new data.
    - `private` - Only admin users or users who have been granted special
       permission may view the record

    If there is no column with the header "Visibility", then the importer will
    look for the field "Item Status". Visibility will be made `public` if the
    status is "Completed" or
    "Completed with minimal metadata", or (by default) if the column cannot be
    found or is blank for a row.

    "Item Status" is *only* used if "Visiblity" is completely omitted from the
    csv. If the column is included but left blank, then a default of `public`
    will be applied to a row regardless of any "Item Status" value.

    Args:
        row: An input CSV record.

    Returns:
        The visibility value.
    """

    visibility_mapping = {
        "authenticated": "authenticated",
        "discovery": "sinai",
        "open": "open",
        "private": "restricted",
        "public": "open",
        "registered": "authenticated",
        "restricted": "restricted",
        "sinai": "sinai",
        "ucla": "authenticated",
    }

    if "Visibility" in row:
        value_from_csv = row["Visibility"].strip().lower()
        return visibility_mapping[value_from_csv]

    if row.get("Item Status") in ["Completed", "Completed with minimal metadata"]:
        return "open"

    return "restricted"


MappigDictValue = typing.Union[None, typing.Callable, str, typing.List[str]]
MappingDict = typing.Dict[str, MappigDictValue]

FIELD_MAPPING: MappingDict = {
    "id": ark,
    "access_copy_ssi": ["IIIF Access URL", "access_copy"],
    "alternative_title_tesim": [
        "AltTitle.other",
        "AltTitle.parallel",
        "AltTitle.translated",
        "Alternate Title.creator",
        "Alternate Title.descriptive",
        "Alternate Title.inscribed",
        "AltTitle.descriptive",
        "Alternate Title.other",
    ],
    "architect_tesim": "Name.architect",
    "ark_ssi": ark,
    "associated_name_tesim": "Associated Name",
    "author_tesim": "Author",
    "binding_note_tesim": ["Binding note", "Description.binding"],
    "binding_condition_tesim": "Binding condition",
    "caption_tesim": "Description.caption",
    "collation_tesim": "Collation",
    "collection_ssi": "Collection",
    "colophon_tesim": "Colophon",
    "composer_tesim": "Name.composer",
    "condition_note_tesim": ["Condition note", "Description.condition"],
    "contents_tesim": "Contents",
    "contents_note_tesim": "Contents note",
    "contributor_tesim": ["Contributors"],
    "date_created_tesim": "Date.creation",
    "delivery_tesim": "delivery",
    "description_tesim": "Description.note",
    "descriptive_title_tesim": "Descriptive title",
    "dlcs_collection_name_tesim": "Relation.isPartOf",
    "explicit_tesim": "Explicit",
    "extent_tesim": "Format.extent",
    "featured_image_ssi": ["Featured image"],
    "features_tesim": "Features",
    "foliation_tesim": ["Foliation note", "Foliation"],
    "folio_dimensions_ss": ["Folio dimensions", "Folio Dimensions"],
    "form_tesim": "Form",
    "format_extent_tesim": ["Format.extent", "Format.dimensions", "Format.weight"],
    "funding_note_tesim": "Description.fundingNote",
    "genre_tesim": ["Type.genre", "Genre"],
    "hand_note_tesim": "Hand note",
    "has_model_ssim": object_type,
    "human_readable_language_tesim": "Language",
    "human_readable_rights_statement_tesim": "Rights.copyrightStatus",
    "iiif_manifest_url_ssi": "IIIF Manifest URL",
    "iiif_range_ssi": "IIIF Range",
    "iiif_text_direction_ssi": "Text direction",
    "iiif_viewing_hint_ssi": "viewingHint",
    "illuminator_tesim": ["Illuminator", "Name.illuminator"],
    "illustrations_note_tesim": ["Illustrations note", "Description.illustrations"],
    "image_count_ssi": "image count",
    "incipit_tesim": "Incipit",
    "ink_color_tesim": ["Ink Color", "Ink color"],
    "inscription_tesim": "Inscription",
    "latitude_tesim": "Description.latitude",
    "local_identifier_ssm": [
        "Alternate Identifier.local",
        "AltIdentifier.callNo",
        "AltIdentifier.local",
        "Alt ID.local",
    ],
    "local_rights_statement_ssim": "Rights.statementLocal",
    "location_tesim": "Coverage.geographic",
    "longitude_tesim": "Description.longitude",
    "lyricist_tesim": "Name.lyricist",
    "masthead_parameters_ssi": "Masthead",
    "medium_tesim": "Format.medium",
    "named_subject_tesim": [
        "Name.subject",
        "Personal or Corporate Name.subject",
        "Subject.corporateName",
        "Subject.personalName",
    ],
    "normalized_date_tesim": "Date.normalized",
    "other_versions_tesim": "Other version(s)",
    "overtext_manuscript_ssm": "Overtext manuscript",
    "page_layout_ssim": "Page layout",
    "photographer_tesim": [
        "Name.photographer",
        "Personal or Corporate Name.photographer",
    ],
    "place_of_origin_tesim": ["Place of origin", "Publisher.placeOfOrigin"],
    "preservation_copy_ssi": preservation_copy,
    "provenance_tesim": ["Provenance", "Description.history"],
    "publisher_tesim": "Publisher.publisherName",
    "references_tesim": "References",
    "related_tesim": "Related",
    "repository_tesim": [
        "Repository",
        "repository",
        "Name.repository",
        "Personal or Corporate Name.repository",
    ],
    "representative_image_ssi": ["Representative image"],
    "resource_type_tesim": "Type.typeOfResource",
    "rights_country_tesim": "Rights.countryCreation",
    "rights_holder_tesim": [
        "Personal or Corporate Name.copyrightHolder",
        "Rights.rightsHolderContact",
        "Rights.rightsHolderName",
    ],
    "rights_statement_tesim": "Rights.copyrightStatus",
    "scribe_tesim": "Scribe",
    "script_tesim": "Script",
    "script_note_tesim": ["Script note", "Script Note"],
    "sequence_isi": "Item Sequence",
    "services_contact_ssm": "Rights.servicesContact",
    "shelfmark_ssi": "Shelfmark",
    "subject_tesim": "Subject",
    "subject_topic_tesim": [
        "Subject topic",
        "Subject.conceptTopic",
        "Subject.descriptiveTopic",
    ],
    "summary_tesim": ["Summary", "Description.abstract"],
    "support_tesim": "Support",
    "tagline_ssi": ["Tagline"],
    "thumbnail_url_ss": thumbnail_url,
    "title_tesim": "Title",
    "toc_tesim": ["Table of Contents", "Description.tableOfContents"],
    "translator_tesim": ["Translator"],
    "undertext_objects_ssim": "Undertext Objects",
    "uniform_title_tesim": "AltTitle.uniform",
    "viscodex_ssi": "Viscodex",
    "visibility_ssi": "Visibility",
    "writing_system_tesim": "Writing system",
    # Set permissive values for blacklight_access_control
    "discover_access_group_ssim": lambda x: ["public"],
    "read_access_group_ssim": lambda x: ["public"],
    "download_access_person_ssim": lambda x: ["public"],
}
