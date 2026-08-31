import sys
from pathlib import Path

import click

from query_things.cli._options import stdargs
from query_things.common import RecordCache, make_record_resolver
from query_things.filter_links_pid import (
    filter_links_pid,
    read_pids,
)


@click.command('filter-links-pid')
@click.option(
    '--link',
    help=(
        'Linking property and target PID. Can be given multiple times. '
        'At least one of --link or --link-from-file is required.'
    ),
    metavar='<PROPERTY> <PID>',
    multiple=True,
    nargs=2,
)
@click.option(
    '--link-from-file',
    'link_from_file',
    help=(
        'Linking property and file with target PIDs, one PID per line. '
        'A record matches this option if it links to any PID in the file '
        'via the property. Can be given multiple times.'
    ),
    metavar='<PROPERTY> <FILE>',
    multiple=True,
    nargs=2,
    type=(
        click.STRING,
        click.Path(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            path_type=Path,
        ),
    ),
)
@click.option(
    '--recursive',
    help='Also consider indirect linkage via recursion',
    is_flag=True,
)
@click.option('--api-url', **stdargs['--api-url'])  # type: ignore[arg-type]
@click.option('--token', **stdargs['--token'])  # type: ignore[arg-type]
@click.option('--record-cache', **stdargs['--record-cache'])  # type: ignore[arg-type]
@click.option(
    '-c',
    '--collection',
    multiple=True,
    help='Collection to query. Can be given multiple times.',
    **stdargs['collection'],  # type: ignore[arg-type]
)
def cli(
    link: tuple[tuple[str, str], ...],
    link_from_file: tuple[tuple[str, Path], ...],
    recursive: bool,
    api_url: str,
    token: str | None,
    record_cache: RecordCache,
    collection: tuple[str, ...] = ('public',),
):
    """Filter records by links to a specific PID or PIDs in a file

    The linkage is constrained by a given property for each --link declaration.
    When more than one --link or --link-from-file option is given, a record
    has to have a matching link for each one of them.
    """
    if not link and not link_from_file:
        msg = 'At least one of --link or --link-from-file must be provided.'
        raise click.UsageError(msg)

    resolver = make_record_resolver(
        api_url=api_url,
        collections=collection,
        cache=record_cache,
        token=token,
    )

    file_links = [(prop, read_pids(path)) for prop, path in link_from_file]

    for line in filter_links_pid(
        sys.stdin,
        links=link,
        file_links=file_links,
        resolver=resolver,
        recursive=recursive,
    ):
        click.echo(line, nl=False)
