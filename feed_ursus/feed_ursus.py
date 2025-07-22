#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert UCLA Library CSV files for Ursus, our Blacklight installation."""

import asyncio
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
@click.option(
    "--mapping",
    default="dlp",
    help="'sinai' or 'dlp'. Deterines the metadata field mapping",
)
@click.version_option(version=importlib.metadata.version("feed_ursus"))
@click.pass_context
def feed_ursus(ctx, solr_url: str, mapping: str):
    """CLI for managing a Solr index for Ursus."""

    ctx.ensure_object(dict)
    ctx.obj["importer"] = Importer(solr_url=solr_url, mapper_name=mapping)


@feed_ursus.command("load")
@click.argument("filenames", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--async/--not-async",
    "use_async",
    default=False,
    help="Enable or disable batch mode.",
)
@click.option(
    "--batch/--not-batch",
    default=True,
    help="Enable or disable batch mode (only applies if --async is False).",
)
@click.option(
    "--batch_size",
    default=1000,
    type=int,
    help="number of records per POST request to solr (only applies if --async is True).",
)
@click.pass_context
def load_csv(
    ctx, filenames: typing.List[str], use_async: bool, batch: bool, batch_size: int
):
    """Load data from a csv.

    Args:
        filenames: A list of CSV filenames.
    """

    if use_async:
        asyncio.run(
            ctx.obj["importer"].load_csv_async(
                filenames=filenames, batch_size=batch_size
            )
        )
    else:
        ctx.obj["importer"].load_csv(filenames=filenames, batch=batch)


@feed_ursus.command()
@click.argument("items", nargs=-1, type=str)
@click.option(
    "--yes/--no", is_flag=True, default=False, help="Skip confirmation prompts."
)
@click.pass_context
def delete(ctx, items: typing.List[str], yes: bool):
    """Delete records from a Solr index.

    Args:
        solr_url: URL of a solr instance.
        items: List of items to delete. Can be ARKs, Solr IDs, or csv filenames.
               If a csv filename is provided, all ARKs in the file will be deleted.
    """
    ctx.obj["importer"].delete(items=items, yes=yes)


if __name__ == "__main__":
    print("feed_ursus() executing, running from main()")
    feed_ursus()  # pylint: disable=no-value-for-parameter
