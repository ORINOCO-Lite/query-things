import click
from copy import deepcopy
import json
import sys

from dump_things_pyclient.communicate import collection_read_record_with_pid

from query_rse_group import stdargs


def _resolve_record(
    rec: dict,
    api_url: str,
    token: str,
    collection: tuple[str],
) -> dict:
    rules = []
    for r in rec.get('rules', []):
        resolved = None
        for col in collection:
            resolved = collection_read_record_with_pid(
                api_url,
                col,
                r,
                token=token,
            )
            if resolved is not None:
                break
        rules.append(resolved if resolved is not None else r)
    out = deepcopy(rec)
    out['rules'] = rules
    return out


@click.command('resolve-datasets')
@click.option('--api-url', **stdargs['--api-url'])
@click.option('--token', **stdargs['--token'])
@click.option('--collection', multiple=True, **stdargs['collection'])
def cli(api_url: str, token: str, collection=('public',)):
    """Resolve and inline metadata linked to dataset records.
    """
    for line in sys.stdin:
        rec = _resolve_record(json.loads(line), api_url, token, collection)
        click.echo(json.dumps(rec), nl=True)
