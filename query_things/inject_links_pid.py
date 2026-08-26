import json
from typing import Any

import click
from dump_things_pyclient.communicate import (  # type: ignore[import-untyped]
    collection_read_records_of_class,
)

from query_things.common import (
    iter_json_objects,
    stdargs,
)


@click.command('inject-links-pid')
@click.argument('inject')
@click.option(
    '--link',
    help='Linking property. Can be given multiple times.',
    metavar='<PROPERTY>',
    multiple=True,
    required=True,
)
@click.option(
    '--class',
    '-C',
    'class_name',
    help='Constrain injected objects to this class',
)
@click.option('--api-url', **stdargs['--api-url'])  # type: ignore[arg-type]
@click.option('--token', **stdargs['--token'])  # type: ignore[arg-type]
@click.option('--record-cache', **stdargs['--record-cache'])  # type: ignore[arg-type]
@click.option(
    '-c',
    '--collection',
    multiple=True,
    help='Collection to query. Can be given multiple times.',
    default=('public',),
    **stdargs['collection'],  # type: ignore[arg-type]
)
def cli(
    inject: str,
    link: tuple[str, ...],
    class_name: str | None,
    api_url: str,
    token: str | None,
    record_cache: dict,  # noqa: ARG001
    collection: tuple[str, ...] = ('public',),
):
    """Inject records that link to each input record"""
    for _, rec in iter_json_objects():
        _proc_record(
            rec,
            inject=inject,
            collections=collection,
            link=link,
            class_name=class_name,
            api_url=api_url,
            token=token,
        )
        click.echo(
            json.dumps(rec, ensure_ascii=True, separators=(',', ':')),
        )


def _proc_record(
    rec: dict[str, Any],
    *,
    inject: str,
    collections: tuple[str, ...],
    link: tuple[str, ...],
    api_url: str,
    class_name: str | None = None,
    token: str | None = None,
) -> None:
    linkers = []
    for col in collections:
        linkers.extend(
            get_any_thing_that_links_pid_via_x(
                link,
                class_name,
                api_url,
                col,
                rec['pid'],
                token=token,
            )
        )
    target = rec.get(inject)
    if target is None:
        rec[inject] = linkers
    elif isinstance(target, list):
        target.extend(linkers)
        rec[inject] = target
    else:
        linkers.insert(0, target)
        rec[inject] = linkers


def get_any_thing_that_links_pid_via_x(
    link: tuple[str, ...],
    class_name: str | None,
    api_url: str,
    collection: str,
    pid: str,
    token: str | None = None,
):
    def _pid_match(val: str | dict, pid: str, via: str):  # noqa: ARG001
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

        return any(_pid_match(val, target_pid, via) for val in prop)

    return [
        res[0]
        for res in collection_read_records_of_class(
            api_url,
            collection,
            class_name if class_name else 'Thing',
            matching=pid,
            token=token,
        )
        if any(_does_link(res[0], pid, prop_id) for prop_id in link)
    ]
