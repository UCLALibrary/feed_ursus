#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Convert UCLA Library CSV files for Ursus, our Blacklight installation."""

import csv
import importlib.metadata
import logging
import sys
import typing
from datetime import datetime, timezone
from getpass import getuser
from math import inf
from pathlib import Path

import click
import pydantic
import requests
import rich.progress
from pysolr import Solr, SolrError  # type: ignore
from rich.console import Console
from rich.table import Table

from feed_ursus.controlled_fields import ResourceType
from feed_ursus.ursus_solr_record import (
    IngestSolrRecord,
    UrsusSolrRecord,
)
from feed_ursus.util import Ark, Empty, MARCList, UnknownItemError, UrsusId


class Importer:
    solr_url: str
    show_progress: bool
    solr_client: Solr

    ingest_id: str  # for sync load_csv
    titles: dict[Ark, str]

    def __init__(self, solr_url: str, show_progress=True):
        self.solr_url = solr_url
        self.show_progress = show_progress

        self.solr_client = Solr(solr_url, always_commit=True)

        self.ingest_id = f"{datetime.now(timezone.utc).isoformat()}-{getuser()}"
        self.titles = {}

        self.titles_from_solr()

    T = typing.TypeVar("T")

    def maybe_progress(
        self,
        iter: typing.Iterable[T],
        description: str,
    ) -> typing.Iterable[T]:
        if self.show_progress:
            return rich.progress.track(iter, description=description)
        else:
            return iter

    def get_ingest_record(self, filenames: list[str]) -> IngestSolrRecord:
        return IngestSolrRecord(
            id=self.ingest_id,
            is_ingest_bsi=True,
            ingest_filenames_ssim=filenames,
            feed_ursus_version_ssi=importlib.metadata.version("feed_ursus"),
            ingest_user_ssi=getuser(),
            csv_files_tsm=[
                Path(filename).read_text(encoding="utf-8")
                for filename in self.maybe_progress(
                    filenames, description=f"saving {len(filenames)} files"
                )
            ],
        )

    def load_csv(self, filenames: list[str], batch: bool):
        """Load data from a csv.

        Args:
            filenames: A list of CSV filenames.
        """

        csv_data = {
            row["Item ARK"]: row
            for filename in self.maybe_progress(
                filenames,
                description=f"loading {len(filenames)} files...",
            )
            for row in csv.DictReader(open(filename, encoding="utf-8"))
        }

        self.ingest_id = f"{datetime.now(timezone.utc).isoformat()}-{getuser()}"
        self.titles.update({row["Item ARK"]: row["Title"] for row in csv_data.values()})

        mapped_records: list[IngestSolrRecord | UrsusSolrRecord] = [
            self.get_ingest_record(
                filenames,
            )
        ]

        for row in self.maybe_progress(
            csv_data.values(),
            description=f"Importing {len(csv_data)} records...",
        ):
            try:
                if row.get("Object Type") not in ("ChildWork", "Page"):
                    mapped_records.append(self.map_record(row))
            except (pydantic.ValidationError, UnknownItemError) as e:
                row_handle = row.get("Item ARK") or row.get("Item Title") or row

                # Note: using "\r" overwrites what would otherwise be a duplicated progress bar
                rich.print(f"\rCould not import row {row_handle}:")
                rich.print(e)
                rich.print("\n")

        if batch:
            print("Submitting records in batch mode...")
            try:
                self.solr_client.add(  # pyright: ignore[reportUnknownMemberType]
                    [record.model_dump(mode="json") for record in mapped_records]
                )
            except SolrError as e:
                print(f"Error adding records in batch mode: {e}")

        else:
            print("Submitting records one by one...")
            for mapped_record in mapped_records:
                try:
                    self.solr_client.add(mapped_record.model_dump(mode="json"))  # pyright: ignore[reportUnknownMemberType]

                except SolrError as e:
                    print(f"Error adding record {mapped_record.solr_id}: {e}")

    def delete(self, items: list[str], yes: bool):
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
                        pydantic.TypeAdapter(UrsusId).validate_python(row["Item ARK"])
                        for row in csv_data
                    )
            elif item.startswith("ark:/"):
                delete_ids.append(pydantic.TypeAdapter(UrsusId).validate_python(item))
            else:
                delete_ids.append(item)

        delete_work_ids: list[UrsusId] = []
        delete_collections: list[UrsusId] = []
        for record in (
            requests.get(
                f"{self.solr_client.url}/get?ids={','.join(delete_ids)}", timeout=10
            )
            .json()
            .get("response", {})
            .get("docs", [])
        ):
            if record["has_model_ssim"][0] == "Collection":
                delete_collections.append(record["id"])
            else:
                delete_work_ids.append(record["id"])

        try:
            n_total_works = self.solr_client.search(
                "has_model_ssim:Work", fq="ark_ssi:*", defType="lucene", rows=0
            ).hits
        except SolrError:
            n_total_works = "[unknown]"

        if len(delete_work_ids):
            if yes or click.confirm(
                f"Delete {len(delete_work_ids)} of {n_total_works} Works?"
            ):
                self.solr_client.delete(id=delete_work_ids)

        for collection_id in delete_collections:
            n_children = self.solr_client.search(
                f"member_of_collection_ids_ssim:{collection_id}",
                fq="ark_ssi:*",
                defType="lucene",
                rows=0,
            ).hits
            if yes or click.confirm(
                f"Delete collection {self.titles['collection_id']}? {n_children} {'child record' if n_children == 1 else 'child records'} will also be deleted."
            ):
                self.solr_client.delete(
                    q=f"id:{collection_id} OR member_of_collection_ids_ssim:{collection_id}"
                )

    def reindex(self, max_errors: int | float = inf) -> None:
        hits = int(self.solr_client.search("ark_ssi:*", rows=0).hits)
        rows = 1000
        n_errors = 0
        Validator = UrsusSolrRecord.less_strict()

        # # Using the looser validation will result in
        # warnings.filterwarnings("ignore", module="pydantic")

        for start in self.maybe_progress(
            range(0, hits, rows), description=f"Reindexing {hits} records..."
        ):
            results = self.solr_client.search(
                "ark_ssi:*",
                start=start,
                rows=rows,
            )
            hits = results.hits
            for raw_doc in results:
                try:
                    Validator.model_validate(raw_doc).model_dump(mode="json")
                except pydantic.ValidationError as e:
                    record_handle = (
                        raw_doc.get("ark_ssi")
                        or raw_doc.get("title_tesim")
                        or raw_doc.get("id")
                        or str(raw_doc)
                    )
                    rich.print(
                        f"\n{record_handle}",
                        e,
                        sep="\n",
                    )

                    n_errors += 1
                    if n_errors >= (max_errors or inf):
                        raise click.ClickException(
                            f"Reindex cancelled: reached {max_errors} {'errors' if max_errors and max_errors > 1 else 'error'}"
                        )

    def dump(self, output: typing.TextIO = sys.stdout) -> None:
        hits = int(self.solr_client.search("*:*", rows=0).hits)
        rows = 250

        for start in range(0, hits, rows):
            results = self.solr_client.search(
                "*:*",
                start=start,
                rows=rows,
            )
            hits = results.hits
            for raw_doc in results:
                self.save_record(raw_doc, output)

    def save_record(
        self,
        record: dict[str, typing.Any],
        output: typing.TextIO = sys.stdout,
    ):
        adapter: pydantic.TypeAdapter[UrsusSolrRecord | IngestSolrRecord] = (
            pydantic.TypeAdapter(UrsusSolrRecord | IngestSolrRecord)
        )
        try:
            doc = adapter.validate_python(record)

            output.write(
                doc.model_dump_json(
                    by_alias=True,
                    exclude_none=True,
                )
                + "\n"
            )

        except pydantic.ValidationError as e:
            logging.warning(f"Could not export {record.get('id', record)}: {e}")

    def map_record(self, record: dict[str, str]) -> UrsusSolrRecord:
        related_record_links = [
            f"<a href='/catalog/{ark}'>{title}</a>"
            for ark, title in zip(
                ark_list_validator.validate_python(record.get("Related Records")) or [],
                self.get_titles(record, "Related Records") or [],
            )
        ] or None

        mapped_record = UrsusSolrRecord.model_validate(
            {
                **record,
                "member_of_collections_ssim": self.get_titles(record, "Parent ARK"),
                "human_readable_related_record_title_ssm": related_record_links,
            }
        )

        if not mapped_record.thumbnail_url_ss and not {
            ResourceType("moving image"),
            ResourceType("sound recording"),
            ResourceType("sound recording-musical"),
            ResourceType("sound recording-nonmusical"),
        }.intersection(mapped_record.human_readable_resource_type_tesim or []):
            mapped_record.thumbnail_url_ss = self.thumbnail_from_access_copy(
                mapped_record
            ) or self.thumbnail_from_manifest(mapped_record)

        return mapped_record

    def get_titles(self, row: dict[str, str], ark_field_name: str) -> list[str] | None:
        arks = ark_list_validator.validate_python(row.get(ark_field_name))

        if not arks:
            return None

        unknown_ids = [
            id_validator.validate_python(ark) for ark in arks if ark not in self.titles
        ]

        if unknown_ids:
            docs = (
                requests.get(
                    f"{self.solr_client.url}/get?ids={','.join(unknown_ids)}&fl=ark_ssi,title_tesim",
                    timeout=10,
                )
                .json()
                .get("response", {})
                .get("docs", [])
            )
            self.titles.update({doc["ark_ssi"]: doc["title_tesim"][0] for doc in docs})

        if still_unknown := [ark for ark in arks if ark not in self.titles]:
            raise UnknownItemError(
                f"Title unknown for item{'s' if len(still_unknown) > 1 else ''} {', '.join(still_unknown)}"
            )

        return [self.titles[ark] for ark in arks]

    def thumbnail_from_access_copy(self, record: UrsusSolrRecord) -> str | None:
        # Cast None to "", so we ensure string methods
        access_copy = str(record.access_copy_ssi)

        if (not record.thumbnail_url_ss) and "/iiif/" in access_copy:
            return UrsusSolrRecord.ensure_thumbnail_iiif_suffix(access_copy)
        else:
            return None

    def thumbnail_from_manifest(self, record: UrsusSolrRecord) -> str | None:
        """Picks a thumbnail downloading the IIIF manifest.

        Args:
            record: A mapping representing the CSV record.

        Returns:
            A string containing the thumbnail URL
        """

        try:
            manifest_url = record.iiif_manifest_url_ssi
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

        except Exception:
            # ruff: noqa: E722
            return None

    def titles_from_solr(self) -> None:
        """Get a mapping of collection IDs to collection names.

        Returns:
            A dict mapping collection IDs to collection names.
        """
        try:
            for doc in self.solr_client.search(
                "has_model_ssim:Collection",
                defType="lucene",
                fl="ark_ssi,title_tesim",
                rows=1000,
            ):
                match doc:
                    case {"ark_ssi": str(ark), "title_tesim": [title, *_]}:
                        self.titles[ark] = title
                    case _:
                        rich.print(f"Can't load title for collection", doc)

        except SolrError as e:
            print(f"Error querying records: {e}")

    def get_log(self):  # -> list[IngestLogRecord]:
        ingest_records = [
            IngestLogRecordReturned.model_validate(x)
            for x in self.solr_client.search("is_ingest_bsi:true").docs
        ]

        ingest_id_facets = (
            self.solr_client.search(
                "*:*",
                **{
                    "facet": "on",
                    "facet.field": "ingest_id_ssi",  # weird **{...} syntax allows "facet.field"
                    "rows": 0,
                },
            )
            .facets.get("facet_fields", {})
            .get("ingest_id_ssi", [])
        )
        ingest_counts = {}
        for i in range(0, len(ingest_id_facets), 2):
            ingest_counts[ingest_id_facets[i]] = ingest_id_facets[i + 1]

        return [
            IngestLogRecord(
                id=record.id,
                feed_ursus_version_ssi=record.feed_ursus_version_ssi,
                ingest_user_ssi=record.ingest_user_ssi,
                ingest_filenames_ssim=record.ingest_filenames_ssim,
                timestamp=record.timestamp,
                count=ingest_counts.get(record.id, 0),
            )
            for record in ingest_records
        ]

    def print_log(self):
        table = Table(title="Ingests")

        table_spec: list[
            tuple[
                str,
                typing.Callable[[IngestLogRecord], str],
            ]
        ] = [
            ("id", lambda row: row.id),
            ("user", lambda row: row.ingest_user_ssi),
            ("filename(s)", lambda row: ", ".join(row.ingest_filenames_ssim)),
            ("feed_ursus version", lambda row: row.feed_ursus_version_ssi),
            ("count", lambda row: str(row.count)),
        ]

        for title, _getter in table_spec:
            table.add_column(title)

        for row in self.get_log():
            table.add_row(*[getter(row) for _title, getter in table_spec])

        console = Console()
        console.print(table)


class IngestLogRecordWrite(pydantic.BaseModel):
    """Record of a given ingest, as submitted to solr."""

    id: str
    is_ingest_bsi: typing.Literal[True] = True
    ingest_filenames_ssim: list[str] = []
    feed_ursus_version_ssi: str
    ingest_user_ssi: str


class IngestLogRecordReturned(IngestLogRecordWrite):
    """Record of a given ingest, as returned by solr.

    Includes fields auto-generated by solr.
    """

    hashed_id_ssi: str
    _version_: int
    timestamp: datetime
    score: float


class IngestLogRecord(IngestLogRecordWrite):
    """Ingest log record, as used for reporting.

    Includes the solr-generated 'timestamp' field plus a 'count' field that must be obtained separately with a facet query on the field
    """

    timestamp: datetime
    count: int


id_validator: pydantic.TypeAdapter[UrsusId] = pydantic.TypeAdapter(UrsusId)
ark_list_validator: pydantic.TypeAdapter[MARCList[Ark] | Empty] = pydantic.TypeAdapter(
    MARCList[Ark] | Empty
)
