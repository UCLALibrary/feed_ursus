# -*- coding: utf-8 -*-
"""Mapping logic for UCLA CSV->Blacklight conversion."""

import typing

# import urllib.parse


def archival_collection(row: typing.Mapping[str, str]) -> str:
    return (
        row["Archival Collection Title"]
        if "Archival Collection Title" in row
        else (
            "" + f" ({row['Archival Collection Number']})"
            if "Archival Collection Number" in row
            else (
                "" + f", Box {row['Box']}"
                if "Box" in row
                else "" + f", Folder {row['Folder']}" if "Folder" in row else ""
            )
        )
    )


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


def coordinates(row: typing.Mapping[str, str]) -> typing.List[str]:
    """Geographic coordinates.

    Args:
        row: An input CSV record.

    Returns:
        A tuple of (latitude, longitude).
    """
    if "Latitude" not in row or "Longitude" not in row:
        return []

    return (row["Latitude"], row["Longitude"])


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
        return visibility_mapping.get(value_from_csv)

    if row.get("Item Status") in ["Completed", "Completed with minimal metadata"]:
        return "open"

    return "restricted"


def access_group(row: typing.Mapping[str, str]) -> typing.List[str]:
    """Access group.

    Args:
        row: An input CSV record.

    Returns:
        ["public"] if metadata will should viewable by all users, though there
        might still be restrictions on viewing the media itself. Otherwise, []
        which will render an item invisible in the public site.

        (note: should we just not bother pushing these to solr?).
    """
    return ["public"] if visibility(row) in ["open", "sinai"] else []


MappigDictValue = typing.Union[None, typing.Callable, str, typing.List[str]]
MappingDict = typing.Dict[str, MappigDictValue]

FIELD_MAPPING: MappingDict = {
    "id": lambda x: x["Item ARK"].replace("ark:/", "").replace("/", "-")[::-1],
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
    "archival_collection_box_ssi": "Box",
    "archival_collection_folder_ssi": "Folder",
    "archival_collection_number_ssi": "Archival Collection Number",
    "archival_collection_tesi": archival_collection,
    "archival_collection_title_ssi": "Archival Collection Title",
    "ark_ssi": ark,
    "artist_tesim": ["Artist", "Name.artist"],
    "artist_sim": ["Artist", "Name.artist"],
    "associated_name_tesim": "Associated Name",
    "author_tesim": "Author",
    "binding_note_tesim": [
        "Binding note",
        "Description.binding",
    ],  # Sinaimanuscripts uses _tesim
    "binding_note_ssi": [
        "Binding note",
        "Description.binding",
    ],  # Californica uses _ssi; Ursus wants _ssi AND _tesim (but _tesim is unpopulated)
    "binding_condition_tesim": "Binding condition",
    "calligrapher_tesim": ["Calligrapher", "Name.calligrapher"],
    "caption_tesim": "Description.caption",
    "cartographer_sim": ["Cartographer", "Name.cartographer"],
    "cartographer_tesim": ["Cartographer", "Name.cartographer"],
    "citation_source_tesim": ["References"],
    "collation_tesim": "Collation",
    "collection_ssi": "Collection",
    "colophon_tesim": ["Colophon", "Description.colophon"],
    "commentator_tesim": ["Commentator", "Name.commentator"],
    "composer_tesim": "Name.composer",
    "condition_note_tesim": ["Condition note", "Description.condition"],  # Sinai
    "condition_note_ssi": ["Condition note", "Description.condition"],  # Californica
    "content_disclaimer_ssm": "Content disclaimer",
    "contents_tesim": "Contents",
    "contents_note_tesim": "Contents note",
    "contributor_tesim": ["Contributors"],
    "creator_sim": ["Name.creator", "Creator"],
    "creator_tesim": ["Name.creator", "Creator"],
    "date_created_tesim": ["Date.creation", "Date.created"],
    "delivery_tesim": "delivery",
    "description_tesim": "Description.note",
    "descriptive_title_tesim": "Descriptive title",
    "dimensions_sim": "Format.dimensions",
    "dimensions_tesim": "Format.dimensions",
    "director_sim": ["Director", "Name.director"],
    "director_tesim": ["Director", "Name.director"],
    # "dlcs_collection_name_tesim": "",  # feed_ursus.py gets from "Parent ARK"
    "edition_ssm": "Edition",
    "editor_tesim": ["Editor", "Name.editor"],
    "electronic_locator_ss": ["External item record", "View Record"],
    "engraver_tesim": ["Engraver", "Name.engraver"],
    "explicit_tesim": "Explicit",
    "extent_tesim": "Format.extent",
    "extent_sim": "Format.extent",
    "featured_image_ssi": ["Featured image"],
    "features_tesim": "Features",
    "finding_aid_url_ssm": ["Finding Aid URL", "Alt ID.url"],
    "foliation_tesim": ["Foliation note", "Foliation"],
    "folio_dimensions_ss": ["Folio dimensions", "Folio Dimensions"],
    "form_tesim": "Form",
    "format_book_tesim": ["Format"],  # Defined in californica, not being used?
    "format_extent_tesim": ["Format.extent", "Format.dimensions", "Format.weight"],
    "funding_note_tesim": "Description.fundingNote",
    "genre_tesim": ["Type.genre", "Genre"],
    "geographic_coordinates_ssim": coordinates,
    "hand_note_tesim": "Hand note",
    "has_model_ssim": object_type,
    "history": ["History"],  # Defined in californica, not being used?
    "host_sim": ["Host", "Name.host"],
    "host_tesim": ["Host", "Name.host"],
    "human_readable_iiif_text_direction_ssi": "Text direction",
    "human_readable_iiif_viewing_hint_ssi": "viewingHint",
    "human_readable_language_tesim": "Language",
    "human_readable_related_record_title_ssm": ["Related Records"],
    "human_readable_resource_type_tesim": "Type.typeOfResource",
    "human_readable_rights_statement_tesim": "Rights.copyrightStatus",
    "identifier_tesim": [
        "Identifier"
    ],  # In the ursus code but idk if we use it, cf ark / local_identifier
    "iiif_manifest_url_ssi": "IIIF Manifest URL",
    "iiif_range_ssi": "IIIF Range",
    "iiif_text_direction_ssi": "Text direction",
    "iiif_viewing_hint_ssi": "viewingHint",
    "illuminator_tesim": ["Illuminator", "Name.illuminator"],
    "illustrations_note_tesim": ["Illustrations note", "Description.illustrations"],
    "illustrator_tesim": ["Illustrator", "Name.illustrator"],
    "image_count_ssi": "image count",
    "incipit_tesim": "Incipit",
    "interviewee_sim": ["Interviewee", "Name.interviewee"],
    "interviewee_tesim": ["Interviewee", "Name.interviewee"],
    "interviewer_sim": ["Interviewer", "Name.interviewer"],
    "interviewer_tesim": ["Interviewer", "Name.interviewer"],
    "ink_color_tesim": ["Ink Color", "Ink color"],
    "inscription_tesim": "Inscription",
    "language_sim": "Language",
    "language_tesim": "Language",
    "latitude_tesim": "Description.latitude",
    "license_tesim": "License",
    "local_identifier_sim": [
        "Alternate Identifier.local",
        "AltIdentifier.callNo",
        "AltIdentifier.local",
        "Alt ID.local",
    ],
    "local_identifier_ssim": [
        "Alternate Identifier.local",
        "AltIdentifier.callNo",
        "AltIdentifier.local",
        "Alt ID.local",
    ],
    "local_identifier_ssm": [
        "Alternate Identifier.local",
        "AltIdentifier.callNo",
        "AltIdentifier.local",
        "Alt ID.local",
    ],
    "local_rights_statement_ssim": "Rights.statementLocal",  # sinai
    "local_rights_statement_ssm": "Rights.statementLocal",  # californica (":displayable")
    "location_tesim": "Coverage.geographic",
    "longitude_tesim": "Description.longitude",
    "lyricist_tesim": "Name.lyricist",
    "masthead_parameters_ssi": "Masthead",
    "medium_tesim": "Format.medium",
    "medium_sim": "Format.medium",
    "member_of_collection_ids_ssim": lambda x: [
        ark.replace("ark:/", "").replace("/", "-")[::-1]
        for ark in x.get("Parent ARK", "").split("|~|")
        if ark  # Skip empty values like ''
    ],
    "musician_sim": ["Musician", "Name.musician"],
    "musician_tesim": ["Musician", "Name.musician"],
    "named_subject_tesim": [
        "Name.subject",
        "Personal or Corporate Name.subject",
        "Subject.corporateName",
        "Subject.personalName",
    ],
    "normalized_date_sim": "Date.normalized",
    "normalized_date_tesim": "Date.normalized",
    "note_tesim": ["Note"],
    "note_admin_tesim": ["AdminNote", "Description.adminnote", "Note.admin"],
    "oai_set_ssim": "oai_set",
    "opac_url_ssi": ["Opac url", "Description.opac"],
    "other_versions_tesim": "Other version(s)",
    "overtext_manuscript_ssm": "Overtext manuscript",
    "page_layout_ssim": "Page layout",
    "photographer_sim": [
        "Name.photographer",
        "Personal or Corporate Name.photographer",
    ],
    "photographer_tesim": [
        "Name.photographer",
        "Personal or Corporate Name.photographer",
    ],
    "place_of_origin_tesim": ["Place of origin", "Publisher.placeOfOrigin"],
    "preservation_copy_ssi": preservation_copy,
    "printer_sim": ["Printer", "Name.printer"],
    "printer_tesim": ["Printer", "Name.printer"],
    "printmaker_tesim": ["Printmaker", "Name.printmaker"],
    "producer_sim": ["Producer", "Name.producer"],
    "producer_tesim": ["Producer", "Name.producer"],
    "program_sim": "Program",
    "program_tesim": "Program",
    "provenance_tesim": ["Provenance", "Description.history"],
    "publisher_sim": "Publisher.publisherName",
    "publisher_tesim": "Publisher.publisherName",
    "recipient_sim": ["Recipient", "Name.recipient"],
    "recipient_tesim": ["Recipient", "Name.recipient"],
    "references_tesim": "References",
    "related_tesim": "Related",  # sinai
    "related_record_ssm": ["Related Records"],  # californica
    "related_to_ssm": ["Related Items"],  # californica
    "repository_tesim": [
        "Repository",
        "repository",
        "Name.repository",
        "Personal or Corporate Name.repository",
    ],
    "repository_sim": [
        "Repository",
        "repository",
        "Name.repository",
        "Personal or Corporate Name.repository",
    ],
    "representative_image_ssi": ["Representative image"],
    "researcher_sim": ["Researcher", "Name.researcher"],
    "researcher_tesim": ["Researcher", "Name.researcher"],
    "resource_type_tesim": "Type.typeOfResource",
    "resource_type_sim": "Type.typeOfResource",
    "resp_statement_tesim": "Statement of Responsibility",
    "rights_country_tesim": "Rights.countryCreation",
    "rights_holder_tesim": [
        "Personal or Corporate Name.copyrightHolder",
        "Rights.rightsHolderContact",
        "Rights.rightsHolderName",
    ],
    "rights_statement_tesim": "Rights.copyrightStatus",
    "rubricator_tesim": ["Rubricator", "Name.rubricator"],
    "scribe_tesim": "Scribe",
    "script_tesim": "Script",
    "script_note_tesim": ["Script note", "Script Note"],
    "series_sim": "Series",
    "series_tesim": "Series",
    "sequence_isi": "Item Sequence",
    "services_contact_ssm": "Rights.servicesContact",
    "shelfmark_ssi": "Shelfmark",
    "subject_cultural_object_sim": "Subject.culturalObject",
    "subject_cultural_object_tesim": "Subject.culturalObject",
    "subject_domain_topic_sim": "Subject.domainTopic",
    "subject_domain_topic_tesim": "Subject.domainTopic",
    "subject_geographic_sim": ["Subject geographic", "Subject place"],
    "subject_geographic_tesim": ["Subject geographic", "Subject place"],
    "subject_tesim": "Subject",
    "subject_temporal_sim": "Subject temporal",
    "subject_temporal_tesim": "Subject temporal",
    "subject_tesim": "Subject",
    "subject_topic_tesim": [
        "Subject topic",
        "Subject.conceptTopic",
        "Subject.descriptiveTopic",
    ],
    "subject_topic_sim": [
        "Subject topic",
        "Subject.conceptTopic",
        "Subject.descriptiveTopic",
    ],
    "summary_tesim": ["Summary", "Description.abstract"],
    "support_tesim": "Support",
    "tagline_ssi": ["Tagline"],
    "thumbnail_url_ss": thumbnail_url,
    "title_tesim": "Title",
    "title_sim": "Title",
    "toc_tesim": ["Table of Contents", "Description.tableOfContents"],
    "translator_tesim": ["Translator"],
    "undertext_objects_ssim": "Undertext Objects",
    "uniform_title_tesim": "AltTitle.uniform",
    "viscodex_ssi": "Viscodex",
    "visibility_ssi": "Visibility",
    "writing_system_tesim": "Writing system",
    # Set permissive values for blacklight_access_control
    "discover_access_group_ssim": access_group,
    "read_access_group_ssim": access_group,
    "download_access_person_ssim": access_group,
}
