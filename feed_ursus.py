#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert UCLA Library CSV files for Ursus, our Blacklight installation."""

import typing

import click
import pandas  # type: ignore
from pysolr import Solr  # type: ignore

import mapper


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
    collection_names = {
        row["Item ARK"]: row["Title"] for _, row in collection_rows.iterrows()
    }

    if not solr_client:
        print("[", end="")

    first_row = True
    for _, row in data_frame.iterrows():
        if first_row:
            first_row = False
        elif not solr_client:
            print(", ")

        mapped_record = map_record(row, collection_names)
        if solr_client:
            solr_client.add([mapped_record])
        else:
            print(mapped_record, end="")

    if not solr_client:
        print("]")


def map_field_value(row: DLCSRecord, field_name: str) -> typing.Any:
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
            output.extend(input_value.split("|~|"))

    return [value for value in output if value]  # remove untruthy values like ''


# pylint: disable=bad-continuation
def map_record(row: DLCSRecord, collection_names: typing.Dict[str, str]) -> UrsusRecord:
    """Maps a metadata record from CSV to Ursus Solr.

    Args:
        record: A mapping representing the CSV record.

    Returns:
        A mapping representing the record to submit to Solr.

    """
    record: UrsusRecord = {
        field_name: map_field_value(row, field_name)
        for field_name in mapper.FIELD_MAPPING
    }

    # collection name
    if "Parent ARK" in row and row["Parent ARK"] in collection_names:
        dlcs_collection_name = collection_names[row["Parent ARK"]]
        record["dlcs_collection_name_tesim"] = [dlcs_collection_name]

    # facet fields
    record["genre_sim"] = record.get("genre_tesim")
    record["human_readable_language_sim"] = record.get("language_tesim")
    record["human_readable_resource_type_sim"] = record.get("resource_type_tesim")
    record["location_sim"] = record.get("location_tesim")
    record["member_of_collections_ssim"] = record.get("dlcs_collection_name_tesim")
    record["named_subject_sim"] = record.get("named_subject_tesim")
    record["subject_sim"] = record.get("subject_tesim")
    record["year_isim"] = record.get("year_tesim")

    return record


if __name__ == "__main__":
    load_csv()  # pylint: disable=no-value-for-parameter
