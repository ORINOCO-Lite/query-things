from typing import cast

import click
from click_option_group import MutuallyExclusiveOptionGroup, optgroup

from query_things.cli._options import stdargs
from query_things.common import (
    RecordCache,
    jsonl_from_record,
)
from query_things.list_records import list_records


@click.command('list')
@optgroup.group('Filters', cls=MutuallyExclusiveOptionGroup, help='Subselect records')
@optgroup.option(
    '--pid',
    metavar='IDENTIFIER',
    multiple=True,
    help='Identifier of a particular record to list. Errors if not such record is found. Can be given multiple times.',
)
@optgroup.option(
    '--class',
    'cls',
    metavar='IDENTIFIER',
    multiple=True,
    help='Identifier of a class for which to list all records. Can be given multiple times.',
)
@click.option('--record-cache', **stdargs['--record-cache'])  # type: ignore[arg-type]
def cli(
    record_cache: RecordCache,
    pid: tuple[str, ...] | None = None,
    cls: tuple[str, ...] | None = None,
):
    """List records stored in the cache

    By default reports all records in the cache in JSON-lines format.
    The report can be constrained by record PIDs or class(es).
    """
    try:
        records = list(list_records(record_cache, pid=pid or (), cls=cls or ()))
    except KeyError as e:
        missing = cast('list[str]', e.args[0])
        raise click.ClickException(
            'No record(s) in cache: ' + ', '.join(repr(p) for p in missing)
        ) from e

    for rec in records:
        click.echo(jsonl_from_record(rec), nl=True)
