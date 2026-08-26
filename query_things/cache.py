import json
import sys
from contextlib import suppress

import click

from query_things import (
    stdargs,
)


@click.command('cache')
@click.option('--record-cache', **stdargs['--record-cache'])
def cli(
    record_cache: dict,
):
    """Cache JSON records and pass them through

    When a record cache is configured, this command stores any records
    read from STDIN in it. Input that fails to JSON-load, or does not
    have a `pid` property is silently ignore and not put into the cache.

    Any input lines, regardless of cache configuration and validity are
    copied to STDOUT.
    """
    for line in sys.stdin:
        try:
            rec = json.loads(line)
            with suppress(KeyError):
                # silently ignore a record without a PID
                record_cache[rec['pid']] = rec
        except ValueError:
            # silently ignore non-JSON input
            pass
        click.echo(line, nl=False)
