import sys

import click

from query_things.cli._options import stdargs
from query_things.common import (
    RecordCache,
    jsonl_from_record,
    parse_json_objects,
)
from query_things.inject_links_pid import inject_linking_records


@click.command('inject-links-pid')
@click.argument('inject')
@click.option(
    '--link',
    help='Linking property. Can be given multiple times.',
    metavar='<PROPERTY>',
    multiple=True,
    required=True,
)
@click.option(
    '--class',
    '-C',
    'class_name',
    help='Constrain injected objects to this class',
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
    **stdargs['collection'],  # type: ignore[arg-type]
)
def cli(
    inject: str,
    link: tuple[str, ...],
    class_name: str | None,
    api_url: str,
    token: str | None,
    record_cache: RecordCache,  # noqa: ARG001
    collection: tuple[str, ...] = ('public',),
):
    """Inject records that link to each input record"""
    for _, rec in parse_json_objects(sys.stdin):
        inject_linking_records(
            rec,
            inject=inject,
            link=link,
            api_url=api_url,
            collections=collection,
            class_name=class_name,
            token=token,
        )
        click.echo(jsonl_from_record(rec))
