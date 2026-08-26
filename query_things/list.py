import json

import click
from click_option_group import MutuallyExclusiveOptionGroup, optgroup

from query_things import (
    stdargs,
)


@click.command('list')
@optgroup.group('Filters', cls=MutuallyExclusiveOptionGroup, help='Subselect records')
@optgroup.option(
    '--pid',
    metavar='IDENTIFER',
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
@click.option('--record-cache', **stdargs['--record-cache'])
def cli(
    record_cache: dict,
    pid: str | None = None,
    cls: str | None = None,
):
    """List records stored in the cache

    By default reports all records in the cache in JSON-lines format.
    The report can be constrained by record PIDs or class(es).
    """
    if pid:
        for p in pid:
            try:
                click.echo(json.dumps(record_cache[p]), nl=True)
            except KeyError as e:
                msg = f'No record with PID {p!r} in the cache'
                raise ValueError(msg) from e
        return

    # for all other scenarios we need to loop over all records
    for rec in record_cache.values():
        if rec is None:
            continue
        if cls and rec.get('schema_type') not in cls:
            continue
        click.echo(json.dumps(rec), nl=True)
