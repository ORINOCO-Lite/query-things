import click
import json
import sys

from dump_things_pyclient.communicate import collection_read_record_with_pid

from query_rse_group import stdargs


def _get_rec_from_any_collection(
    api_url: str,
    collections: tuple[str],
    pid: str,
    cache: dict,
    token: str | None = None,
):
    for col in collections:
        rec = cache.get(pid) or collection_read_record_with_pid(
            api_url,
            col,
            pid,
            token=token,
        )
        if rec is not None:
            cache[pid] = rec
            return rec

    # yes, also cache that we asked and nothing was there
    cache[pid] = None
    return None


def _resolve_records(
    property: str,
    rec: dict,
    api_url: str,
    token: str,
    collections: tuple[str],
    cache: dict,
) -> None:
    prop_in = rec.get(property)
    if prop_in is None:
        # nothing to do, doesn't exist
        return rec

    scalar = not isinstance(prop_in, (list, tuple))
    prop_out = []
    for p in ([prop_in] if scalar else prop_in):
        pid = p['object'] if isinstance(p, dict) else p
        resolved = _get_rec_from_any_collection(
            api_url,
            collections,
            pid,
            cache,
            token=token,
        )
        if resolved is None:
            po = p
        elif isinstance(p, dict):
            po = p.copy()
            po['object'] = resolved
        else:
            po = resolved
        prop_out.append(po)
    rec[property] = prop_out[0] if scalar else prop_out


@click.command('inline-records')
@click.option(
    '-p', '--property',
    multiple=True,
    help='Property to inline records for. Can be given multiple times.',
)
@click.option('--api-url', **stdargs['--api-url'])
@click.option('--token', **stdargs['--token'])
@click.option(
    '-c', '--collection',
    multiple=True,
    help='Collection to query. Can be given multiple times.',
    default=('public',),
    **stdargs['collection'],
)
def cli(
    property: tuple[str],
    api_url: str,
    token: str,
    collection=('public',),
):
    """Resolve and inline metadata linked to dataset records.
    """
    rec_cache = {}
    for line in sys.stdin:
        rec = json.loads(line)
        for prop in property:
            _resolve_records(
                prop,
                rec,
                api_url, token, collection,
                rec_cache,
            )
        click.echo(json.dumps(rec), nl=True)
