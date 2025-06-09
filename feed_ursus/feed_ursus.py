#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert UCLA Library CSV files for Ursus, our Blacklight installation."""

import importlib.metadata
import typing

import click

from feed_ursus.importer import Importer


@click.group()
@click.option(
    "--solr_url",
    default="http://localhost:8983/solr/californica",
    help="URL of a solr instance, e.g. http://localhost:8983/solr/californica",
)
@click.version_option(version=importlib.metadata.version("feed_ursus"))
@click.pass_context
def feed_ursus(ctx, solr_url: str):
    """CLI for managing a Solr index for Ursus."""

    ctx.ensure_object(dict)
    ctx.obj["importer"] = Importer(solr_url=solr_url)


@feed_ursus.command("load")
@click.argument("filenames", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def load_csv(ctx, filenames: typing.List[str]):
    """Load data from a csv.

    Args:
        filenames: A list of CSV filenames.
    """

    importer: Importer = ctx.obj["importer"]
    importer.load_csvs(filenames)


@feed_ursus.command()
@click.argument("items", nargs=-1, type=str)
@click.option(
    "--yes/--no", is_flag=True, default=False, help="Skip confirmation prompts."
)
@click.pass_context
def delete(ctx, items: typing.List[str], yes: bool):
    """Delete records from a Solr index.

    Args:
        items: List of items to delete. Can be ARKs, Solr IDs, or csv filenames.
               If a csv filename is provided, all ARKs in the file will be deleted.
    """

    importer: Importer = ctx.obj["importer"]
    importer.delete(items, skip_confirmation=yes)


if __name__ == "__main__":
    feed_ursus()  # pylint: disable=no-value-for-parameter
