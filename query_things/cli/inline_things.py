import json
import sys

import click

from query_things.cli._options import stdargs
from query_things.common import (
    RecordCache,
    make_record_resolver,
    parse_json_objects,
)
from query_things.inline_things import inline_records


@click.command('inline-things')
@click.option(
    '-p',
    '--path',
    multiple=True,
    help="""\
Path to thing (identifier) to inline. Can be given multiple times.  Paths can
point to keys inside nested objects, and inlining multiple levels of nested
intermediate objects is possible. Keys spanning nesting levels must be given
`::` separated (e.g., `influenced_by::object::name`).  Fields identified by a
path (including intermediate levels) may be multivalued.
""",
)
@click.option('--api-url', **stdargs['--api-url'])  # type: ignore[arg-type]
@click.option('--token', **stdargs['--token'])  # type: ignore[arg-type]
@click.option('--record-cache', **stdargs['--record-cache'])  # type: ignore[arg-type]
@click.option(
    '-c',
    '--collection',
    multiple=True,
    help='Collection to query. Can be given multiple times.',
    default=('public',),
    show_default=True,
    **stdargs['collection'],  # type: ignore[arg-type]
)
def cli(
    path: tuple[str, ...],
    api_url: str,
    token: str | None,
    record_cache: RecordCache,
    collection=('public',),
):
    """Inline nested Things PID references

    Read JSON records from stdin, resolve PID references at the given
    field paths, and write the updated records to stdout.

    Use `::` to traverse nested fields. If a value at any matched path
    is a PID string, such as `collection:123`, it is replaced with the
    full record fetched from the API.

    Examples:

    \b
    query-things inline-things -p influenced_by::object::name
    query-things inline-things -p author -p references::items
    """
    resolver = make_record_resolver(
        api_url=api_url,
        collections=collection,
        cache=record_cache,
        token=token,
    )

    paths = [tuple(p.split('::')) for p in path]

    for _, rec in parse_json_objects(sys.stdin):
        inline_records(rec, paths, resolver)
        click.echo(
            json.dumps(
                rec,
                ensure_ascii=True,
                separators=(',', ':'),
            )
        )
