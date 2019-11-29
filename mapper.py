# -*- coding: utf-8 -*-
"""Mapping logic for UCLA CSV->Blacklight conversion."""


def map_ark_ssi(ark):
    """Mapping for "Item ARK". Ensures it is a single-valued field.

    Args:
        ark: Input CSV cell.

    Returns:
        A string containing the ARK. Not an array, since this is not a multi-
        valued field.
    """
    return ark


FIELDS = {
    "Alternate Identifier.local": "local_identifier_ssm",
    "AltTitle.other": "alternative_title_tesim",
    "AltTitle.uniform": "uniform_title_tesim",
    "Author": "author_tesim",
    "Binding note": "binding_note_tesim",
    "Collation": "collation_ssi",
    "Condition note": "condition_note_tesim",
    "Coverage.geographic": "location_tesim",
    "Date.creation": "date_created_tesim",
    "Date.normalized": "normalized_date_tesim",
    "Description.caption": "caption_tesim",
    "Description.fundingNote": "funding_note_tesim",
    "Description.latitude": "latitude_tesim",
    "Description.longitude": "longitude_tesim",
    "Description.note": "description_tesim",
    "File Name": "preservation_copy_ssi",
    "Foliation note": "foliation_ssi",
    "Format.dimensions": "dimensions_tesim",
    "Format.extent": "extent_tesim",
    "Format.medium": "medium_tesim",
    "IIIF Access URL": "access_copy_ssi",
    "IIIF Range": "iiif_range",
    "Illuminator": "illuminator_tesim",
    "Illustrations note": "illustrations_note_tesim",
    "Item ARK": "ark_ssi",
    "Language": "language_tesim",
    "Name.architect": "architect_tesim",
    "Name.composer": "composer_tesim",
    "Name.lyricist": "lyricist_tesim",
    "Name.photographer": "photographer_tesim",
    "Name.repository": "repository_tesim",
    "Name.scribe": "scribe_tesim",
    "Name.subject": "named_subject_tesim",
    "Object Type": "has_model_ssim",
    "Page layout": "page_layout_ssim",
    "Personal or Corporate Name.copyrightHolder": "rights_holder_tesim",
    "Place of origin": "place_of_origin_tesim",
    "Provenance": "provenance_tesim",
    "Publisher.publisherName": "publisher_tesim",
    "Relation.isPartOf": "dlcs_collection_name_tesim",
    "Rights.copyrightStatus": "rights_statement_tesim",
    "Rights.countryCreation": "rights_country_tesim",
    "Rights.servicesContact": "services_contact_ssm",
    # "Rights.statementLocal": "# local_rights_statement",
    "Subject topic": "subject_topic_tesim",
    "Subject": "subject_tesim",
    "Summary": "summary_tesim",
    "Support": "support_tesim",
    "Table of Contents": "toc_tesim",
    # "Text direction": "iiif_text_direction",
    "Title": "title_tesim",
    "Type.genre": "genre_tesim",
    "Type.typeOfResource": "resource_type_tesim",
    # "viewingHint": "iiif_viewing_hint",
}
