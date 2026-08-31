import sys

import click

from query_things.cache import cache_records
from query_things.cli._options import stdargs
from query_things.common import RecordCache


@click.command('cache')
@click.option('--record-cache', **stdargs['--record-cache'])  # type: ignore[arg-type]
def cli(
    record_cache: RecordCache,
):
    """Cache JSON records and pass them through

    When a record cache is configured, this command stores any records
    read from STDIN in it. Input that fails to JSON-load, or does not
    have a `pid` property is silently ignore and not put into the cache.

    Any input lines, regardless of cache configuration and validity are
    copied to STDOUT.
    """
    for line in cache_records(sys.stdin, record_cache):
        click.echo(line, nl=False)
