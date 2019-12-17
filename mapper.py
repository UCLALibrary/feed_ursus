# -*- coding: utf-8 -*-
"""Mapping logic for UCLA CSV->Blacklight conversion."""

import typing
import urllib.parse


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


def iiif_manifest_url(row: typing.Mapping[str, str]) -> str:
    """A URL containing the IIIF manifest, constructed using the IIIF serivce
    URL and the item ARK. A manifest does not need to be present at this
    URL - though of course if one is not, then UV will fail to load in Ursus
    until a manifest is submitted.

    Args:
        row: An input CSV record.

    Returns:
        IIIF Manifest URL.
    """
    iiif_identifier = urllib.parse.quote_plus(ark(row))
    return f"https://iiif.library.ucla.edu/{iiif_identifier}/manifest"


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


def thumbnail_url(row: typing.Mapping[str, str]) -> typing.Optional[str]:
    """A thumbnail URL.

    Args:
        row: An input CSV record.

    Returns:
        The thumbnail URL.
    """
    if row.get("IIIF Access URL"):
        return row["IIIF Access URL"] + "/full/!200,200/0/default.jpg"
    return None


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
    "author_tesim": "Author",
    "binding_note_tesim": ["Binding note", "Description.binding"],
    "caption_tesim": "Description.caption",
    "collation_ssi": "Collation",
    "composer_tesim": "Name.composer",
    "condition_note_tesim": ["Condition note", "Description.condition"],
    "date_created_tesim": "Date.creation",
    "description_tesim": "Description.note",
    "dimensions_tesim": "Format.dimensions",
    "dlcs_collection_name_tesim": "Relation.isPartOf",
    "extent_tesim": "Format.extent",
    "foliation_ssi": ["Foliation note", "Foliation"],
    "funding_note_tesim": "Description.fundingNote",
    "genre_tesim": "Type.genre",
    "has_model_ssim": object_type,
    "iiif_manifest_url_ssi": iiif_manifest_url,
    "iiif_range_ssi": "IIIF Range",
    "iiif_text_direction_ssi": "Text direction",
    "iiif_viewing_hint_ssi": "viewingHint",
    "illuminator_tesim": ["Illuminator", "Name.illuminator"],
    "illustrations_note_tesim": ["Illustrations note", "Description.illustrations"],
    "language_tesim": "Language",
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
    "medium_tesim": "Format.medium",
    "named_subject_tesim": [
        "Name.subject",
        "Personal or Corporate Name.subject",
        "Subject.corporateName",
        "Subject.personalName",
    ],
    "normalized_date_tesim": "Date.normalized",
    "page_layout_ssim": "Page layout",
    "photographer_tesim": [
        "Name.photographer",
        "Personal or Corporate Name.photographer",
    ],
    "place_of_origin_tesim": "Place of origin",
    "preservation_copy_ssi": "File Name",
    "provenance_tesim": ["Provenance", "Description.history"],
    "publisher_tesim": "Publisher.publisherName",
    "repository_tesim": ["Name.repository", "Personal or Corporate Name.repository",],
    "resource_type_tesim": "Type.typeOfResource",
    "rights_country_tesim": "Rights.countryCreation",
    "rights_holder_tesim": [
        "Personal or Corporate Name.copyrightHolder",
        "Rights.rightsHolderContact",
    ],
    "rights_statement_tesim": "Rights.copyrightStatus",
    "scribe_tesim": "Name.scribe",
    "services_contact_ssm": "Rights.servicesContact",
    "subject_tesim": "Subject",
    "subject_topic_tesim": [
        "Subject topic",
        "Subject.conceptTopic",
        "Subject.descriptiveTopic",
    ],
    "summary_tesim": ["Summary", "Description.abstract", "Description.contents"],
    "support_tesim": "Support",
    "thumbnail_url_ss": thumbnail_url,
    "title_tesim": "Title",
    "toc_tesim": ["Table of Contents", "Description.tableOfContents"],
    "uniform_title_tesim": "AltTitle.uniform",
    # Set permissive values for blacklight_access_control
    "discover_access_group_ssim": lambda x: ["public"],
    "read_access_group_ssim": lambda x: ["public"],
    "download_access_person_ssim": lambda x: ["public"],
}
