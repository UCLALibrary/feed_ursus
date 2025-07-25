#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert UCLA Library CSV files for Ursus, our Blacklight installation."""

import asyncio
import csv
from collections import defaultdict
from datetime import datetime, timezone
from getpass import getuser
from importlib import import_module
import importlib.metadata
import os
import re
from types import ModuleType
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Collection,
    Dict,
    List,
    Optional,
    Sequence,
)
import yaml

import click
import httpx

from pysolr import Solr, SolrError  # type: ignore
import requests
import rich.progress

from . import year_parser
from . import date_parser


# Custom Types

DLCSRecord = Dict[str, Any]
UrsusRecord = Dict[str, Any]


def collate_child_works(csv_data: dict[str, DLCSRecord]) -> defaultdict[str, list]:
    # link pages to their parent works
    child_works = defaultdict(list)
    for row in csv_data.values():
        if row["Object Type"] in ("ChildWork", "Page"):
            child_works[row["Parent ARK"]].append(row)
    return child_works


def load_field_config(base_path: str = "./fields") -> Dict:
    """Load configuration of controlled metadata fields.

    Args:
        base_path: Path to a directory containing [field].yml files.

    Returns:
        A dict with field configuration.
    """
    field_config: Dict = {}
    for path, _, files in os.walk(base_path):
        for file_name in files:
            if not file_name.endswith(".yml") or file_name.endswith(".yaml"):
                continue

            field_name = os.path.splitext(file_name)[0]
            with open(os.path.join(path, file_name), "r") as stream:
                field_config[field_name] = yaml.safe_load(stream)
            field_config[field_name]["terms"] = {
                t["id"]: t["term"] for t in field_config[field_name]["terms"]
            }
    return field_config


def get_bare_field_name(field_name: str) -> str:
    """Strips the solr suffix and initial 'human_readable_' from a field name."""

    return re.sub(r"_[^_]+$", "", field_name).replace("human_readable_", "")


def solr_transformed_dates(solr_client: Solr, parsed_dates: List):
    """the dates  in sorted list are transformed to solr format"""
    return [
        solr_client._from_python(date) for date in parsed_dates
    ]  # pylint: disable=protected-access


class Importer:
    solr_url: str
    solr_client: Solr
    async_client: httpx.AsyncClient
    mapper: ModuleType

    ingest_id: str  # for sync load_csv
    collection_names: dict
    child_works: defaultdict[str, list]
    controlled_fields: dict

    connection_pool = asyncio.Semaphore(3)

    def __init__(self, solr_url, mapper_name):
        self.solr_url = solr_url
        self.solr_client = Solr(solr_url, always_commit=True)
        self.async_client = httpx.AsyncClient()
        self.mapper = import_module(f"feed_ursus.mapper.{mapper_name}")

        self.ingest_id = f"{datetime.now(timezone.utc).isoformat()}-{getuser()}"
        self.collection_names = dict()
        self.child_works = defaultdict(list)
        self.controlled_fields = load_field_config("./mapper/fields")

    def load_csv(self, filenames: List[str], batch: bool):
        """Load data from a csv.

        Args:
            filenames: A list of CSV filenames.
        """

        csv_data = {
            row["Item ARK"]: row
            for filename in rich.progress.track(
                filenames, description=f"loading {len(filenames)} files..."
            )
            for row in csv.DictReader(open(filename, encoding="utf-8"))
        }

        self.ingest_id = f"{datetime.now(timezone.utc).isoformat()}-{getuser()}"
        self.collection_names = {
            row["Item ARK"].replace("ark:/", "").replace("/", "-")[::-1]: row["Title"]
            for row in csv_data.values()
            if row.get("Object Type") == "Collection"
        }
        self.controlled_fields = load_field_config("./mapper/fields")
        self.child_works = collate_child_works(csv_data)

        mapped_records = [
            {
                "id": self.ingest_id,
                "is_ingest_bsi": True,
                "feed_ursus_version_ssi": importlib.metadata.version("feed_ursus"),
                "ingest_user_ssi": getuser(),
                # Hack, until a decision made on better logging
                # "csv_files_ss": json.dumps(
                #     {
                #         filename: open(filename, encoding="utf-8").read()
                #         for filename in rich.progress.track(
                #             filenames, description=f"loading {len(filenames)} files..."
                #         )
                #     }
                # ),
            }
        ]
        for row in rich.progress.track(
            csv_data.values(), description=f"Importing {len(csv_data)} records..."
        ):
            if row.get("Object Type") not in ("ChildWork", "Page"):
                mapped_records.append(self.map_record(row))

        if batch:
            print("Submitting records in batch mode...")
            try:
                self.solr_client.add(mapped_records)
            except SolrError as e:
                print(f"Error adding records in batch mode: {e}")

        else:
            print("Submitting records one by one...")
            for mapped_record in mapped_records:
                self.add_record(mapped_record)

    def add_record(self, mapped_record: UrsusRecord):
        """Add a single record to the Solr index."""

        try:
            self.solr_client.add(mapped_record)
            print(f"Added record {mapped_record['id']}")

        except SolrError as e:
            print(f"Error adding record {mapped_record['id']}: {e}")

    async def load_csv_async(self, filenames: List[str], batch_size: int = 1000):
        """Load data from a csv.

        Args:
            filenames: A list of CSV filenames.
        """

        batch: list[UrsusRecord] = [
            {
                "id": self.ingest_id,
                "is_ingest_bsi": True,
                "feed_ursus_version_ssi": importlib.metadata.version("feed_ursus"),
                "ingest_user_ssi": getuser(),
                # Hack, until a decision made on better logging
                # "csv_files_ss": json.dumps(
                #     {
                #         filename: open(filename, encoding="utf-8").read()
                #         for filename in rich.progress.track(
                #             filenames, description=f"loading {len(filenames)} files..."
                #         )
                #     }
                # ),
            }
        ]
        posts: list[Awaitable] = list()

        for filename in rich.progress.track(
            filenames, description=f"loading {len(filenames)} files..."
        ):
            for row in csv.DictReader(open(filename, encoding="utf-8")):
                if row.get("Object Type") == "Collection":
                    id = row["Item ARK"].replace("ark:/", "").replace("/", "-")[::-1]
                    self.collection_names[id] = row["Title"]

                if row.get("Object Type") in ("Page", "ChildWork"):
                    continue

                batch.append(self.map_record(row))

                if len(batch) >= batch_size:
                    posts.append(self.add_to_solr(batch))
                    batch = list()

        if len(batch) > 0:
            posts.append(self.add_to_solr(batch))

        await asyncio.gather(*posts)

    async def add_to_solr(self, records: Sequence[UrsusRecord]) -> None:
        async with self.connection_pool:
            response = await self.async_client.post(
                f"{self.solr_url}/update?commit=true", json=records
            )

        if response.is_error:
            if len(records) == 1:
                print(
                    f"Error adding record {records[0]['id']}: {response.json().get('error').get('msg')}"
                )
            else:
                mid = int(len(records) / 2)
                await asyncio.gather(
                    self.add_to_solr(records[:mid]), self.add_to_solr(records[mid:])
                )

    def delete(self, items: List[str], yes: bool):
        """Delete records from a Solr index.

        Args:
            solr_url: URL of a solr instance.
            items: List of items to delete. Can be ARKs, Solr IDs, or csv filenames.
                If a csv filename is provided, all ARKs in the file will be deleted.
        """

        delete_ids: list[str] = []
        for item in items:
            if item.endswith(".csv"):
                with open(item, "r", encoding="utf-8") as stream:
                    csv_data = csv.DictReader(stream)
                    delete_ids.extend(
                        row["Item ARK"].replace("ark:/", "").replace("/", "-")[::-1]
                        for row in csv_data
                    )
            elif item.startswith("ark:/"):
                delete_ids.append(item.replace("ark:/", "").replace("/", "-")[::-1])
            else:
                delete_ids.append(item)

        delete_work_ids, delete_collections = [], []
        for record in (
            requests.get(
                f"{self.solr_client.url}/get?ids={','.join(delete_ids)}", timeout=10
            )
            .json()
            .get("response", {})
            .get("docs", [])
        ):
            print(record, record["has_model_ssim"], record["has_model_ssim"][0])
            if record["has_model_ssim"][0] == "Collection":
                delete_collections.append(record)
            else:
                delete_work_ids.append(record["id"])

        try:
            n_total_works = self.solr_client.search(
                "has_model_ssim:Work", fq="ark_ssi:*", defType="lucene", rows=0
            ).hits
        except SolrError:
            n_total_works = "[unknown]"

        if yes or click.confirm(
            f"Delete {len(delete_work_ids)} of {n_total_works} Works?"
        ):
            self.solr_client.delete(id=delete_work_ids)

        for collection in delete_collections:
            n_children = self.solr_client.search(
                f"member_of_collection_ids_ssim:{collection['id']}",
                fq="ark_ssi:*",
                defType="lucene",
                rows=0,
            ).hits
            if yes or click.confirm(
                f"Delete {n_children} collection {collection['title_tesim']}? {n_children} {'child record' if n_children==1 else 'child records'} will also be deleted."
            ):
                self.solr_client.delete(
                    q=f"id:{collection['id']} OR member_of_collection_ids_ssim:{collection['id']}"
                )

    # pylint: disable=bad-continuation
    def map_field_value(self, row: DLCSRecord, field_name: str) -> Any:
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
        mapping: dict = self.mapper.FIELD_MAPPING[field_name]

        if mapping is None:
            return None

        if callable(mapping):
            return mapping(row)

        if isinstance(mapping, str):
            mapping = [mapping]

        if not isinstance(mapping, Collection):
            raise TypeError(
                f"FIELD_MAPPING[field_name] must be iterable, unless it is None, Callable, or a string."
            )

        output: List[str] = []
        for csv_field in mapping:
            input_value = row.get(csv_field)
            if input_value:
                if isinstance(input_value, str):
                    output.extend(input_value.split("|~|"))
                else:
                    output.append(input_value)

        bare_field_name = get_bare_field_name(field_name)
        if bare_field_name in self.controlled_fields:
            terms = self.controlled_fields[bare_field_name]["terms"]
            output = [terms.get(value, value) for value in output]

        if field_name.endswith("m"):
            return [
                value for value in output if value
            ]  # remove untruthy values like '' or None
        else:
            return output[0] if len(output) >= 1 else None

    # pylint: disable=bad-continuation
    def map_record(
        self, row: DLCSRecord
    ) -> UrsusRecord:  # pylint: disable=too-many-statements
        """Maps a metadata record from CSV to Ursus Solr.

        Args:
            record: A mapping representing the CSV record.

        Returns:
            A mapping representing the record to submit to Solr.

        """
        record: UrsusRecord = {
            field_name: self.map_field_value(row, field_name)
            for field_name in self.mapper.FIELD_MAPPING
        }

        record["record_origin_ssi"] = "feed_ursus"
        record["ingest_id_ssi"] = self.ingest_id

        # THUMBNAIL
        record["thumbnail_url_ss"] = (
            record.get("thumbnail_url_ss")
            or self.thumbnail_from_child(record)
            or self.thumbnail_from_manifest(record)
        )

        # COLLECTIONS
        record["member_of_collections_ssim"] = [
            self.collection_names[id]
            for id in record.get("member_of_collection_ids_ssim", [])
        ]

        # FIELDS
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
        record["human_readable_language_sim"] = record.get(
            "human_readable_language_tesim"
        )
        record["names_sim"] = self.name_fields(record)
        record["keywords_sim"] = self.keywords_fields(record)
        record["collection_sim"] = record.get("collection_ssi")
        # explicit
        record["features_sim"] = record.get("features_tesim")
        # incipit
        # inscription
        record["script_sim"] = record.get("script_tesim")
        record["writing_system_sim"] = record.get("writing_system_tesim")
        record["year_isim"] = year_parser.integer_years(
            record.get("normalized_date_tesim")
        )
        record["date_dtsim"] = solr_transformed_dates(
            self.solr_client,
            (date_parser.get_dates(record.get("normalized_date_tesim"))),
        )
        record["place_of_origin_sim"] = record.get("place_of_origin_tesim")
        record["associated_name_sim"] = record.get("associated_name_tesim")
        record["form_sim"] = record.get("form_tesim")
        record["support_sim"] = record.get("support_tesim")
        record["genre_sim"] = record.get("genre_tesim")
        record["subject_sim"] = record.get("subject_tesim")
        record["location_sim"] = record.get("location_tesim")
        record["named_subject_sim"] = record.get("named_subject_tesim")
        record["human_readable_resource_type_sim"] = record.get("resource_type_tesim")

        record["combined_subject_ssim"] = [
            *record.get("named_subject_tesim", []),
            *record.get("subject_tesim", []),
            *record.get("subject_topic_tesim", []),
            *record.get("subject_geographic_tesim", []),
            *record.get("subject_temporal_tesim", []),
        ]

        # SINAI INDEX
        record["header_index_tesim"] = self.header_fields(record)
        record["name_fields_index_tesim"] = self.name_fields_index(record)

        # SORT FIELDS
        titles = record.get("title_tesim")
        if isinstance(titles, Sequence) and len(titles) >= 1:
            record["sort_title_ssort"] = titles[0]

        # used a solr copyfield for shelfmark sorting
        # shelfmarks = record.get("shelfmark_ssi")
        # print(shelfmarks)
        # if isinstance(shelfmarks, Sequence) and len(shelfmarks) >= 1:
        # print(shelfmarks[0])
        # record["shelfmark_aplha_numeric_ssort"] = shelfmarks[0]

        # -----------------------------------------------------------------------
        years = record.get("year_isim")
        if isinstance(years, Sequence) and len(years) >= 1:
            record["sort_year_isi"] = min(years)

        dates = record.get("date_dtsim")
        if isinstance(dates, Sequence) and len(dates) >= 1:
            record["date_dtsort"] = dates[0]
        return record

    def name_fields(self, record):
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
                record["names_sim"] = record["names_sim"] + record.get(
                    "associated_name_tesim"
                )
            else:
                record["names_sim"] = record.get("associated_name_tesim")

        if record.get("translator_tesim") is not None:
            if record.get("names_sim") is not None:
                record["names_sim"] = record["names_sim"] + record.get(
                    "translator_tesim"
                )
            else:
                record["names_sim"] = record.get("translator_tesim")
        return record["names_sim"]

    # Sinai Index Page
    # record.get returns the default of en empty array if there is no record

    # combine fields for the header value

    def header_fields(self, record):
        """Header: shelfmark_ssi: 'Shelfmark' && extent_tesim: 'Format'"""
        shelfmark = [record["shelfmark_ssi"]] if "shelfmark_ssi" in record else []
        extent = record.get("extent_tesim", [])
        return shelfmark + extent

    # Sinai Item Page
    # record.get returns the default of en empty array if there is no record

    # combine fields for the keywords value

    def keywords_fields(self, record):
        """Keywords: genre_tesim: 'Genre' && features_tesim: 'Features' &&
        place_of_origin_tesim: 'Place of Origin' && support_tesim: 'Support' &&
        form_ssi: 'Form'
        """
        genre = record.get("genre_tesim", [])
        features = record.get("features_tesim", [])
        place_of_origin = record.get("place_of_origin_tesim", [])
        support = record.get("support_tesim", [])
        form = [record["form_ssi"]] if "form_ssi" in record else []

        record["keywords_tesim"] = genre + features + place_of_origin + support + form
        return record["keywords_tesim"]

    # TITLE: uniform_title_one | uniform_title_two | descriptive_title_one | descriptive_title_two

    # combine fields for the names value in the Name facet & for the index page
    # Name: author_tesim && associated_name_tesim && scribe_tesim

    def name_fields_index(self, record):
        """NAME: author_one| author_two | associated_one | associated_two | scribe_one"""
        author = record.get("author_tesim", [])
        associated_name = record.get("associated_name_tesim", [])
        scribe = record.get("scribe_tesim", [])
        name_fields_combined = author + associated_name + scribe
        return name_fields_combined

    def thumbnail_from_child(self, record: UrsusRecord) -> Optional[str]:
        """Picks a thumbnail by looking for child rows in the CSV.

        Tries the following strategies in order, returning the first that succeeds:
        - Thumbnail of a child record titled "f. 001r"
        - Thumbnail of the first child record
        - None

        Args:
            record: A mapping representing the CSV record.

        Returns:
            A string containing the thumbnail URL
        """

        ark = record.get("ark_ssi")

        if not ark:
            return None

        children: list = self.child_works[ark]

        def sort_key(row: dict) -> str:
            if row["Title"].startswith("f. "):
                return (
                    "a" + row["Title"]
                )  # prefer records of this form, in alphanumeric sort order
            else:
                return "z" + row["Title"]

        children.sort(key=sort_key)

        for row in children:
            thumb = self.mapper.thumbnail_url(row)
            if thumb:
                print(row["Title"])
                return thumb

        return None

    def thumbnail_from_manifest(self, record: UrsusRecord) -> Optional[str]:
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
