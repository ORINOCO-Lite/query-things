import click
from dump_things_pyclient.communicate import (
    collection_read_record_with_pid,
)

from query_things.common import (
    iter_json_objects,
    iter_link_pids,
    stdargs,
)


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
    property: str,  # noqa: A002
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
    linked_pids = set(iter_link_pids(ref.get(property)))
    for line, rec in iter_json_objects():
        if rec['pid'] in linked_pids:
            click.echo(line, nl=False)
