#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert UCLA Library CSV files for Ursus, our Blacklight installation."""

import asyncio
import importlib.metadata

import click

from feed_sinai.sinai_json_importer import SinaiJsonImporter


@click.group()
@click.version_option(version=importlib.metadata.version("feed_ursus"))
def sinai() -> None:
    """CLI for managing a Solr index for Ursus."""
    pass


@sinai.command("export")
@click.argument(
    "base_path",
    nargs=1,
    default=".",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
)
def export(base_path: str) -> None:
    importer = SinaiJsonImporter(base_path=base_path)
    importer.save_merged_records()


@sinai.command("load")
@click.argument(
    "base_path",
    nargs=1,
    default=".",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
)
@click.argument(
    "solr_url",
    nargs=1,
    default="http://localhost:8983/solr/californica",
    # help="URL of a solr instance, e.g. http://localhost:8983/solr/californica",
)
def load(base_path: str, solr_url: str) -> None:
    importer = SinaiJsonImporter(base_path=base_path, solr_url=solr_url)
    asyncio.run(importer.load_to_solr())


@sinai.command("wipe")
@click.argument(
    "solr_url",
    nargs=1,
    default="http://localhost:8983/solr/californica",
    # help="URL of a solr instance, e.g. http://localhost:8983/solr/californica",
)
def wipe(solr_url: str) -> None:
    importer = SinaiJsonImporter(solr_url=solr_url)
    importer.wipe_solr_records()


@sinai.command("save_solr_records")
@click.argument(
    "base_path",
    nargs=1,
    default=".",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
)
def save_solr_records(base_path: str) -> None:
    importer = SinaiJsonImporter(base_path=base_path)
    importer.save_solr_records()


if __name__ == "__main__":
    sinai()  # pylint: disable=no-value-for-parameter
