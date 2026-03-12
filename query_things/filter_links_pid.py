import click
import json
import sys

from query_things import (
    stdargs,
    _get_rec_from_any_collection,
)


@click.command('filter-links-pid')
@click.option(
    '--link',
    help='Linkage target, linking property and target PID',
    metavar='<PROPERTY> <PID>',
    multiple=True,
    nargs=2,
)
@click.option(
    '--recursive',
    help='Also consider indirect linkage via recursion',
    type=bool,
    is_flag=True,
)
@click.option('--api-url', **stdargs['--api-url'])
@click.option('--token', **stdargs['--token'])
@click.option('--record-cache', **stdargs['--record-cache'])
@click.option(
    '-c', '--collection',
    multiple=True,
    help='Collection to query. Can be given multiple times.',
    default=('public',),
    **stdargs['collection'],
)
def cli(
    link: tuple[tuple[str, str]],
    recursive: bool,
    api_url: str,
    token: str,
    record_cache: dict,
    collection=('public',),
):
    """Filter records that link a specific object via a given property
    """
    def _pid_match(val: str | dict, pid: str, recursive: bool, via: str):
        if isinstance(val, dict):
            val = val['object']

        if pid == val:
            return True

        if recursive:
            rec = _get_rec_from_any_collection(
                api_url,
                collection,
                val,
                record_cache,
                token=token,
            )
            return _does_link(
                rec,
                pid,
                via,
                recursive=True,
            )

        return False

    def _does_link(
        rec: dict,
        target_pid: str,
        via: str,
        recursive: bool,
    ) -> bool:
        if via not in rec:
            # no chance
            return False

        prop = rec[via]
        if not isinstance(prop, (list, tuple)):
            prop = [prop]

        return any(
            _pid_match(val, target_pid, recursive, via)
            for val in prop
        )

    for line in sys.stdin:
        rec = json.loads(line)
        report = True
        for prop_id, pid in link:
            if not _does_link(rec, pid, prop_id, recursive):
                report = False
                break
        if not report:
            continue
        click.echo(line, nl=False)
