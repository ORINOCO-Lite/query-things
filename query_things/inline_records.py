import json
import sys

import click

from query_things import (
    _get_rec_from_any_collection,
    stdargs,
)


def _resolve_records(
    property: str,
    rec: dict,
    api_url: str,
    token: str,
    collections: tuple[str],
    cache: dict,
    pid_prop: str = 'object',
) -> None:
    prop_in = rec.get(property)
    if prop_in is None:
        # nothing to do, doesn't exist
        return rec

    scalar = not isinstance(prop_in, (list, tuple))
    prop_out = []
    for prop in [prop_in] if scalar else prop_in:
        pid = prop.get(pid_prop) if isinstance(prop, dict) else prop
        if pid is None:
            continue

        def _proc_pid(pid):
            resolved = _get_rec_from_any_collection(
                api_url,
                collections,
                pid,
                cache,
                token=token,
            )
            return resolved if resolved is not None else pid

        inlined = (
            [_proc_pid(pi) for pi in pid] if isinstance(pid, list) else _proc_pid(pid)
        )

        if isinstance(prop, dict):
            po = prop.copy()
            po[pid_prop] = inlined
        else:
            po = inlined
        prop_out.append(po)
    rec[property] = prop_out[0] if scalar else prop_out
    return None


@click.command('inline-records')
@click.option(
    '-p',
    '--property',
    multiple=True,
    help="""\
Property to inline records for. Can be given multiple times.
When the property value is an object, the PID is assumed to be
available under an "object" key. If another field should be
used, it can be given with a `::<key>` suffix (e.g.,
`--property delegated_by::roles`). The PID field can be
multivalued.
""",
)
@click.option('--api-url', **stdargs['--api-url'])
@click.option('--token', **stdargs['--token'])
@click.option('--record-cache', **stdargs['--record-cache'])
@click.option(
    '-c',
    '--collection',
    multiple=True,
    help='Collection to query. Can be given multiple times.',
    default=('public',),
    **stdargs['collection'],
)
def cli(
    property: tuple[str],
    api_url: str,
    token: str,
    record_cache: dict,
    collection=('public',),
):
    """DEPRECATED: use `inline-things`"""
    for line in sys.stdin:
        rec = json.loads(line)
        for prop in property:
            parent_prop = prop.split('::', maxsplit=1)
            _resolve_records(
                parent_prop[0],
                rec,
                api_url,
                token,
                collection,
                record_cache,
                pid_prop=parent_prop[1] if len(parent_prop) > 1 else 'object',
            )
        click.echo(json.dumps(rec), nl=True)
