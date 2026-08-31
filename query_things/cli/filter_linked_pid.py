import sys

import click

from query_things.cli._options import stdargs
from query_things.filter_linked_pid import (
    filter_linked_pid,
    get_reference_linked_pids,
)


@click.command('filter-linked-pid')
# TODO: maybe later to invert the filter
# @click.option('--ex
@click.argument('collection', **stdargs['collection'])  # type: ignore[arg-type]
@click.argument('pid')
@click.argument('property')
@click.option('--api-url', **stdargs['--api-url'])  # type: ignore[arg-type]
@click.option('--token', **stdargs['--token'])  # type: ignore[arg-type]
def cli(
    collection: str,
    pid: str,
    property: str,  # noqa: A002
    api_url: str,
    token: str | None = None,
):
    """Keep records linked from a reference

    Incoming records are tested whether their `pid` appears
    in the property of another record. Properties with
    individual values, lists of values, or lists of association
    class instances are equally supported.

    Example use cases:

    \b
    - Match person records that are associated with a particular project
    - Match topics a particular publication is about
    """
    linked_pids = get_reference_linked_pids(
        collection,
        pid,
        property,
        api_url,
        token=token,
    )

    for line in filter_linked_pid(sys.stdin, linked_pids):
        click.echo(line, nl=False)
