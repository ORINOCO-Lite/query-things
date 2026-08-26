import click

from query_things.common import (
    RecordCache,
    all_records_have_links,
    iter_json_objects,
    make_record_resolver,
    stdargs,
)


@click.command('filter-links-pid')
@click.option(
    '--link',
    help='Linkage target, linking property and target PID',
    metavar='<PROPERTY> <PID>',
    multiple=True,
    nargs=2,
    required=True,
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
    recursive: bool,  # noqa: FBT001
    api_url: str,
    token: str | None,
    record_cache: RecordCache,
    collection: tuple[str, ...] = ('public',),
):
    """Filter records by links to a specific PID"""

    resolver = make_record_resolver(
        api_url=api_url,
        collections=collection,
        cache=record_cache,
        token=token,
    )

    for line, rec in iter_json_objects():
        if all_records_have_links(
            rec,
            link,
            resolver=resolver,
            recursive=recursive,
        ):
            click.echo(line, nl=False)
