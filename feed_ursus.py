#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert UCLA Library CSV files for Ursus, our Blacklight installation."""

import os
import re
import typing
import yaml

import click
import pandas  # type: ignore
from pysolr import Solr  # type: ignore
import requests

import mapper
import year_parser
import date_parser

# Custom Types

DLCSRecord = typing.Dict[str, typing.Any]
UrsusRecord = typing.Dict[str, typing.Any]


@click.command()
@click.argument("filename")
@click.option(
    "--solr_url",
    default=None,
    help="URL of a solr instance, e.g. http://localhost:6983/solr/californica",
)
def load_csv(filename: str, solr_url: typing.Optional[str]):
    """Load data from a csv.

    Args:
        filename: A CSV file.
        solr_url: URL of a solr instance.
    """

    solr_client = Solr(solr_url, always_commit=True) if solr_url else None

    data_frame = pandas.read_csv(filename)
    data_frame = data_frame.where(data_frame.notnull(), None)
    collection_rows = data_frame[data_frame["Object Type"] == "Collection"]

    config = {
        "collection_names": {
            row["Item ARK"]: row["Title"] for _, row in collection_rows.iterrows()
        },
        "controlled_fields": load_field_config("./fields"),
        "data_frame": data_frame,
    }

    if not solr_client:
        print("[", end="")

    first_row = True
    for _, row in data_frame.iterrows():
        if row["Object Type"] in ("ChildWork", "Page"):
            continue

        if first_row:
            first_row = False
        elif not solr_client:
            print(", ")

        mapped_record = map_record(row, solr_client, config=config)
        if solr_client:
            solr_client.add([mapped_record])
        else:
            print(mapped_record, end="")

    if not solr_client:
        print("]")


def load_field_config(base_path: str = "./fields") -> typing.Dict:
    """Load configuration of controlled metadata fields.

    Args:
        base_path: Path to a directory containing [field].yml files.

    Returns:
        A dict with field configuration.
    """
    field_config: typing.Dict = {}
    for path, _, files in os.walk(base_path):
        for file_name in files:
            field_name = os.path.splitext(file_name)[0]
            with open(os.path.join(path, file_name), "r") as stream:
                field_config[field_name] = yaml.safe_load(stream)
            field_config[field_name]["terms"] = {
                t["id"]: t["term"] for t in field_config[field_name]["terms"]
            }
    return field_config


# pylint: disable=bad-continuation
def map_field_value(
    row: DLCSRecord, field_name: str, config: typing.Dict
) -> typing.Any:
    """Map value from a CSV cell to an object that will be passed to solr.

    Mapping logic is defined by the FIELD_MAPPING dict, defined in mappery.py.
    Keys of FIELD_MAPPING are output field names as used in Ursus. Values can
    vary, and the behavior of map_field_value() will depend on that value.

    If FIELD_MAPPING[field_name] is a string, then it will be interpreted as
    the title of a CSV column to map. The value of that column will be split
    using the MARC delimiter '|~|', and a list of one or more strings will be
    returned (or an empty list, if the CSV column was empty).

    If FIELD_MAPPING[field_name] is a list of strings, then they will all be
    interpreted as CSV column names to be mapped. Each column will be processed
    as above, and the resulting lists will be concatenated.

    Finally, FIELD_MAPPING[field_name] can be a function, most likely defined
    in mappery.py. If this is the case, that function will be called with the
    input row (as a dict) as its only argument. That function should return a
    type that matches the type of the solr field. This is the only way to
    map to types other than lists of strings.

    Args:
        row: An input row containing a DLCS record.
        field_name: The name of the Ursus/Solr field to map.

    Returns:
        A value to be submitted to solr. By default this is a list of strings,
        however map_[SOLR_FIELD_NAME] functions can return other types.
    """
    mapping: mapper.MappigDictValue = mapper.FIELD_MAPPING[field_name]

    if mapping is None:
        return None

    if callable(mapping):
        return mapping(row)

    if isinstance(mapping, str):
        mapping = [mapping]

    if not isinstance(mapping, typing.Collection):
        raise TypeError(
            f"FIELD_MAPPING[field_name] must be iterable, unless it is None, Callable, or a string."
        )

    output: typing.List[str] = []
    for csv_field in mapping:
        input_value = row.get(csv_field)
        if input_value:
            if isinstance(input_value, str):
                output.extend(input_value.split("|~|"))
            else:
                output.append(input_value)

    bare_field_name = get_bare_field_name(field_name)
    if bare_field_name in config.get("controlled_fields", {}):
        terms = config["controlled_fields"][bare_field_name]["terms"]
        output = [terms.get(value, value) for value in output]

    return [value for value in output if value]  # remove untruthy values like ''


def get_bare_field_name(field_name: str) -> str:
    """Strips the solr suffix and initial 'human_readable_' from a field name."""

    return re.sub(r"_[^_]+$", "", field_name).replace("human_readable_", "")

def solr_transformed_dates(solr_client: Solr, parsed_dates: typing.List):
    """ the dates  in sorted list are transformed to solr format  """
    return [solr_client._from_python(date) for date in parsed_dates] # pylint: disable=protected-access

# pylint: disable=bad-continuation
def map_record(row: DLCSRecord, solr_client: Solr, config: typing.Dict) -> UrsusRecord:
    """Maps a metadata record from CSV to Ursus Solr.

    Args:
        record: A mapping representing the CSV record.

    Returns:
        A mapping representing the record to submit to Solr.

    """
    record: UrsusRecord = {
        field_name: map_field_value(row, field_name, config=config)
        for field_name in mapper.FIELD_MAPPING
    }

    # THUMBNAIL
    record["thumbnail_url_ss"] = (
        record.get("thumbnail_url_ss")
        or thumbnail_from_child(record, config=config)
        or thumbnail_from_manifest(record)
    )

    # COLLECTION NAME
    if "Parent ARK" in row and row["Parent ARK"] in config["collection_names"]:
        dlcs_collection_name = config["collection_names"][row["Parent ARK"]]
        record["dlcs_collection_name_tesim"] = [dlcs_collection_name]

    # FACET FIELDS
    # Item Overview
    record["uniform_title_sim"] = record.get("uniform_title_tesim")
    record["architect_sim"] = record.get("architect_tesim")
    record["author_sim"] = record.get("author_tesim")
    record["illuminator_sim"] = record.get("illuminator_tesim")
    record["scribe_sim"] = record.get("scribe_tesim")
    record["rubricator_sim"] = record.get("rubricator_tesim")
    record["commentator_sim"] = record.get("commentator_tesim")
    record["translator_sim"] = record.get("translator_tesim")
    record["lyricist_sim"] = record.get("lyricist_tesim")
    record["composer_sim"] = record.get("composer_tesim")
    record["illustrator_sim"] = record.get("illustrator_tesim")
    record["editor_sim"] = record.get("editor_tesim")
    record["calligrapher_sim"] = record.get("calligrapher_tesim")
    record["engraver_sim"] = record.get("engraver_tesim")
    record["printmaker_sim"] = record.get("printmaker_tesim")
    record["human_readable_language_sim"] = record.get("human_readable_language_tesim")
    record["names_sim"] = name_fields(record)
    #Keywords
    record["keywords_sim"] = keywords_fields(record)
    # explicit
    record["features_sim"] = record.get("features_tesim")
    # incipit
    # inscription
    record["script_sim"] = record.get("script_tesim")
    record["writing_system_sim"] = record.get("writing_system_tesim")
    record["year_isim"] = year_parser.integer_years(record.get("normalized_date_tesim"))
    record["date_dtsim"] = solr_transformed_dates(solr_client,
    (date_parser.get_dates(record.get("normalized_date_tesim"))))
    record["place_of_origin_sim"] = record.get("place_of_origin_tesim")
    record["associated_name_sim"] = record.get("associated_name_tesim")

    # Physical Description
    record["form_sim"] = record.get("form_ssi")
    record["support_sim"] = record.get("support_tesim")

    # Keywords
    record["genre_sim"] = record.get("genre_tesim")
    record["subject_sim"] = record.get("subject_tesim")
    record["location_sim"] = record.get("location_tesim")
    record["named_subject_sim"] = record.get("named_subject_tesim")

    # Find This Item

    # Access Condition
    record["human_readable_resource_type_sim"] = record.get("resource_type_tesim")
    record["member_of_collections_ssim"] = record.get("dlcs_collection_name_tesim")

    # Searchable but not Viewable

    # SORT FIELDS
    titles = record.get("title_tesim")
    if isinstance(titles, typing.Sequence) and len(titles) >= 1:
        record["sort_title_ssort"] = titles[0]

    # used a solr copyfield for shelfmark sorting
    # shelfmarks = record.get("shelfmark_ssi")
    # print(shelfmarks)
    # if isinstance(shelfmarks, typing.Sequence) and len(shelfmarks) >= 1:
        # print(shelfmarks[0])
        # record["shelfmark_aplha_numeric_ssort"] = shelfmarks[0]

    # SINAI INDEX
    record["header_index_tesim"] = header_fields(record)
    record["name_fields_index_tesim"] = name_fields_index(record)

# -----------------------------------------------------------------------
    years = record.get("year_isim")
    if isinstance(years, typing.Sequence) and len(years) >= 1:
        record["sort_year_isi"] = min(years)

    dates = record.get("date_dtsim")
    if isinstance(dates, typing.Sequence) and len(dates) >= 1:
        record["date_dtsort"] = dates[0]
    return record

def name_fields(record):
    """combine fields for the names facet"""
    record["names_sim"] = record.get("author_tesim")
    if record.get("author_tesim") is not None:
        if record.get("names_sim") is not None:
            record["names_sim"] = record["names_sim"] + record.get("author_tesim")
        else:
            record["names_sim"] = record.get("author_tesim")

    if record.get("scribe_tesim") is not None:
        if record.get("names_sim") is not None:
            record["names_sim"] = record["names_sim"] + record.get("scribe_tesim")
        else:
            record["names_sim"] = record.get("scribe_tesim")

    if record.get("associated_name_tesim") is not None:
        if record.get("names_sim") is not None:
            record["names_sim"] = record["names_sim"] + record.get("associated_name_tesim")
        else:
            record["names_sim"] = record.get("associated_name_tesim")

    if record.get("translator_tesim") is not None:
        if record.get("names_sim") is not None:
            record["names_sim"] = record["names_sim"] + record.get("translator_tesim")
        else:
            record["names_sim"] = record.get("translator_tesim")
    return record["names_sim"]

# Sinai Index Page
# record.get returns the default of en empty array if there is no record

# combine fields for the header value

def header_fields(record):
    """Header: shelfmark_ssi: 'Shelfmark' && extent_tesim: 'Format'"""
    shelfmark = record.get("shelfmark_ssi", [])
    extent = record.get("extent_tesim", [])
    return shelfmark + extent

# Sinai Item Page
# record.get returns the default of en empty array if there is no record

# combine fields for the keywords value

def keywords_fields(record):
    """Keywords: genre_tesim: 'Genre' && features_tesim: 'Features' &&
    place_of_origin_tesim: 'Place of Origin' && support_tesim: 'Support' &&
    form_ssi: 'Form'
    """
    genre = record.get("genre_tesim", [])
    features = record.get("features_tesim", [])
    place_of_origin = record.get("place_of_origin_tesim", [])
    support = record.get("support_tesim", [])
    form = record.get("form_ssi", [])
    record["keywords_tesim"] = genre + features + place_of_origin + support + form
    return record["keywords_tesim"]

# TITLE: uniform_title_one | uniform_title_two | descriptive_title_one | descriptive_title_two

# combine fields for the names value in the Name facet & for the index page
# Name: author_tesim && associated_name_tesim && scribe_tesim

def name_fields_index(record):
    """NAME: author_one| author_two | associated_one | associated_two | scribe_one"""
    author = record.get("author_tesim", [])
    associated_name = record.get("associated_name_tesim", [])
    scribe = record.get("scribe_tesim", [])
    name_fields_combined = author + associated_name + scribe
    return name_fields_combined

def thumbnail_from_child(
    record: UrsusRecord, config: typing.Dict
) -> typing.Optional[str]:
    """Picks a thumbnail by looking for child rows in the CSV.

    Tries the following strategies in order, returning the first that succeeds:
    - Thumbnail of a child record titled "f. 001r"
    - Thumbnail of the first child record
    - None

    Args:
        record: A mapping representing the CSV record.
        config: A config object.

    Returns:
        A string containing the thumbnail URL
    """

    if "data_frame" not in config:
        return None

    ark = record["ark_ssi"]
    data = config["data_frame"]
    children = data[data["Parent ARK"] == ark]
    representative = children[children["Title"] == "f. 001r"]
    if representative.shape[0] == 0:
        representative = children

    for _, row in representative.iterrows():
        thumb = mapper.thumbnail_url(row)
        if thumb:
            return thumb
    return None

def thumbnail_from_manifest(record: UrsusRecord) -> typing.Optional[str]:
    """Picks a thumbnail downloading the IIIF manifest.

    Args:
        record: A mapping representing the CSV record.

    Returns:
        A string containing the thumbnail URL
    """

    try:
        manifest_url = record.get("iiif_manifest_url_ssi")
        if not isinstance(manifest_url, str):
            return None
        response = requests.get(manifest_url)
        manifest = response.json()

        canvases = {
            c["label"]: c["images"][0]["resource"]["service"]["@id"]
            for seq in manifest["sequences"]
            for c in seq["canvases"]
        }

        return (
            canvases.get("f. 001r") or list(canvases.values())[0]
        ) + "/full/!200,200/0/default.jpg"

    except:  # pylint: disable=bare-except
        return None

if __name__ == "__main__":
    load_csv()  # pylint: disable=no-value-for-parameter
