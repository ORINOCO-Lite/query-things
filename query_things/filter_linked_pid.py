import json
import sys

import click
from dump_things_pyclient.communicate import (
    collection_read_record_with_pid,
)

from query_things import stdargs


@click.command('filter-linked-pid')
# TODO: maybe later to invert the filter
# @click.option('--ex
@click.argument('collection', **stdargs['collection'])
@click.argument('pid')
@click.argument('property')
@click.option('--api-url', **stdargs['--api-url'])
@click.option('--token', **stdargs['--token'])
def cli(
    collection: str,
    pid: str,
    property: str,
    api_url: str,
    token: str | None = None,
):
    """Keep records linked from a reference

    Incoming records are tested whether their `pid` appears
    in the property of another record. Properties with
    individual values, lists of values, or lists of association
    class instances are equally supported.

    Example use cases:

    \b
    - Match person records that are associated with a particular project
    - Match topics a particular publication is about
    """
    ref = collection_read_record_with_pid(
        service_url=api_url,
        collection=collection,
        pid=pid,
        token=token,
    )
    ref_prop = ref[property]
    # normalize to a structure that matches association classes.
    # this will make it easier to extend the matching (ie. with
    # time windows) later on
    linked = [
        lnk if isinstance(lnk, dict) else {'object': lnk}
        for lnk in (ref_prop if isinstance(ref_prop, list) else [ref_prop])
    ]
    for line in sys.stdin:
        rec = json.loads(line)
        if any(lnk['object'] == rec['pid'] for lnk in linked):
            click.echo(line, nl=False)
