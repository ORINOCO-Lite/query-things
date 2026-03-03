
import click
import json
import sys

from dump_things_pyclient.communicate import (
    collection_read_records_of_class,
)

from query_rse_group import (
    stdargs,
    _get_rec_from_any_collection,
)


@click.command('inject-links-pid')
@click.argument('inject')
@click.option(
    '--link',
    help='Linkage target, linking property and target PID',
    metavar='<PROPERTY>',
    multiple=True,
)
@click.option(
    '--class', '-C', 'class_name',
    help='Constrain injected objects to this class',
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
    inject: str,
    link: tuple[str],
    class_name: str,
    api_url: str,
    token: str,
    record_cache: dict,
    collection=('public',),
):
    """Inject records that link an object via a given property
    """
    for line in sys.stdin:
        rec = json.loads(line)
        linkers = []
        for col in collection:
            linkers.extend(get_any_thing_that_links_pid_via_x(
                link,
                class_name,
                api_url,
                col,
                rec['pid'],
                token=token,
            ))
        target = rec.get(inject)
        if target is None:
            rec[inject] = linkers
        elif isinstance(target, list):
            target.extend(linkers)
            rec[inject] = target
        else:
            linkers.insert(0, target)
            rec[inject] = linkers
        click.echo(
            json.dumps(rec, ensure_ascii=True, separators=(',', ':')),
        )


def get_any_thing_that_links_pid_via_x(
    link: tuple[tuple[str, str]],
    class_name: str,
    api_url: str,
    collection: str,
    pid: str,
    token: str | None = None,
):
    def _pid_match(val: str | dict, pid: str, via: str):
        if isinstance(val, dict):
            val = val['object']
        return pid == val

    def _does_link(
        rec: dict,
        target_pid: str,
        via: str,
    ) -> bool:
        if via not in rec:
            # no chance
            return False

        prop = rec[via]
        if not isinstance(prop, (list, tuple)):
            prop = [prop]

        return any(
            _pid_match(val, target_pid, via)
            for val in prop
        )

    return [
        res[0]
        for res in collection_read_records_of_class(
            api_url,
            collection,
            class_name if class_name else 'Thing',
            matching=pid,
            token=token,
        )
        if any(
            _does_link(res[0], pid, prop_id)
            for prop_id in link
        )
    ]
