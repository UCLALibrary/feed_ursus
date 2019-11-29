#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert UCLA Library CSV files for Ursus, our Blacklight installation."""

import collections
import urllib.parse
import typing

import click
import pandas  # type: ignore
from pysolr import Solr  # type: ignore

import mapper


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

    first_row = True

    if not solr_client:
        print("[", end="")

    for _, row in data_frame.iterrows():
        if first_row:
            first_row = False
        elif not solr_client:
            print(", ")

        mapped_record = map_record(row)
        if solr_client:
            solr_client.add([mapped_record])
        else:
            print(mapped_record, end="")

    if not solr_client:
        print("]")


def map_field_name(field_name: str) -> str:
    """Map a CSV column name to an Ursus solr field.

    Args:
        field_name: The name of the field in input CSV.

    Returns:
        The field name as expected by Ursus.
    """
    return mapper.FIELDS[field_name]


def map_field_value(field_name: str, value: str) -> typing.Any:
    """Map value from a CSV cell to an object that will be passed to solr.

    If the 'mapper' module defines a function map_[SOLR_FIELD_NAME]
    (e.g. map_ark_ssi), then that function is called with a single argument,
    [value]. Otherwise value is assumed to be a list of terms separated by the
    MARC code '|~|'.

    Args:
        field_name: The field name as it appears in CSV.
        value: the value from the CSV cell.

    Returns:
        A value to be submitted to solr. By default this is a list of strings,
        however map_[SOLR_FIELD_NAME] functions can return other types.

    """
    function_name = "map_" + map_field_name(field_name)
    if hasattr(mapper, function_name):
        return getattr(mapper, function_name)(value)
    if value is None:
        return []
    return value.split("|~|")


def map_record(record: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
    """Maps a metadata record from CSV to Ursus Solr.

    Args:
        record: A mapping representing the CSV record.

    Returns:
        A mapping representing the record to submit to Solr.

    """
    new_record: typing.Dict[str, typing.Any] = collections.defaultdict(list)
    new_record.update(
        {
            map_field_name(key): map_field_value(key, value)
            for key, value in record.items()
            if key in mapper.FIELDS.keys() and value
        }
    )

    new_record["id"] = new_record["ark_ssi"]

    if record.get("IIIF Access URL"):
        new_record["thumbnail_url_ss"] = (
            record["IIIF Access URL"] + "/full/!200,200/0/default.jpg"
        )

    new_record["discover_access_group_ssim"] = ["public"]
    new_record["read_access_group_ssim"] = ["public"]
    new_record["download_access_person_ssim"] = ["public"]
    new_record[
        "iiif_manifest_url_ssi"
    ] = f'https://iiif.library.ucla.edu/{urllib.parse.quote_plus(record["Item ARK"])}/manifest'

    # facet fields
    new_record["genre_sim"].extend(new_record["genre_tesim"])
    new_record["human_readable_language_sim"].extend(new_record["language_tesim"])
    new_record["human_readable_resource_type_sim"].extend(
        new_record["resource_type_tesim"]
    )
    new_record["location_sim"].extend(new_record["location_tesim"])
    new_record["member_of_collections_ssim"].extend(
        new_record["dlcs_collection_name_tesim"]
    )
    new_record["named_subject_sim"].extend(new_record["named_subject_tesim"])
    new_record["subject_sim"].extend(new_record["subject_tesim"])
    new_record["year_isim"].extend(new_record["year_tesim"])

    return new_record


if __name__ == "__main__":
    load_csv()  # pylint: disable=no-value-for-parameter
