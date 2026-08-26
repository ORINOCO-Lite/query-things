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
@click.option('--record-cache', **stdargs['--record-cache'])  # type: ignore[arg-type]
def cli(
    record_cache: dict,
    pid: tuple[str, ...] | None = None,
    cls: tuple[str, ...] | None = None,
):
    """List records stored in the cache

    By default reports all records in the cache in JSON-lines format.
    The report can be constrained by record PIDs or class(es).
    """
    if pid:
        results = []
        missing = []

        for p in pid:
            rec = record_cache.get(p)
            if rec is None:
                missing.append(p)
            else:
                results.append(rec)

        if missing:
            raise click.ClickException(
                'No record(s) in cache: ' + ', '.join(repr(p) for p in missing)
            )

        for rec in results:
            click.echo(json.dumps(rec), nl=True)
        return

    # for all other scenarios we need to loop over all records
    for rec in record_cache.values():
        if rec is None:
            continue
        if cls and rec.get('schema_type') not in cls:
            continue
        click.echo(json.dumps(rec), nl=True)
