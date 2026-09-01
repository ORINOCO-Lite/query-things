import sys

import click

from query_things.cache import cache_record
from query_things.cli._options import stdargs
from query_things.common import (
    RecordCache,
    parse_json_objects,
)


@click.command('cache')
@click.option('--record-cache', **stdargs['--record-cache'])  # type: ignore[arg-type]
def cli(
    record_cache: RecordCache,
):
    """Cache JSON records and pass them through

    When a record cache is configured, this command stores any records
    read from STDIN in it. Input that fails to JSON-load, or does not
    have a `pid` property cause an error exit.

    Any input lines, regardless of cache configuration are copied to STDOUT.
    """
    for line, rec in parse_json_objects(sys.stdin):
        cache_record(rec, record_cache)
        click.echo(line, nl=False)
