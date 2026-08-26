import json
from collections.abc import Callable, Sequence
from functools import partial
from typing import Any

import click

from query_things.common import (
    _get_rec_from_any_collection,
    RecordCache,
    iter_json_objects,
    stdargs,
)


def walk(
    container: Any,
    path: tuple[str, ...],
    get_obj: Callable[[str], dict[str, Any] | None],
) -> None:
    """
    Recursively walk a ``container`` following the given path.

    The given container may not actually be one.
    """
    if not path:
        return

    key = path[0]

    if isinstance(container, dict) and key in container:
        value = container[key]

        if isinstance(value, str) and ':' in value:
            resolved = get_obj(pid=value)
            if resolved is not None:
                container[key] = resolved
                value = resolved

        if len(path) == 1:
            return

        if isinstance(value, dict):
            walk(value, path[1:], get_obj)
        elif isinstance(value, list):
            for item in value:
                walk(item, path[1:], get_obj)

    elif isinstance(container, list):
        for item in container:
            walk(item, path, get_obj)


def inline_json_objects(
    obj: dict[str, Any],
    paths: Sequence[Sequence[str]],
    get_obj: Callable[[str], dict[str, Any] | None],
) -> None:
    """Mutate a JSON-like object in place by resolving object PID references.

    For each key path in ``paths``, this function walks the input object. When
    it finds a string value containing a colon (``:``), it calls ``get_obj()``
    with that string. If ``get_obj()`` returns a non-None value, the string is
    replaced with the returned object and traversal continues recursively from
    there using the remaining path.
    """
    for spec in paths:
        walk(obj, tuple(spec), get_obj)


@click.command('inline-things')
@click.option(
    '-p',
    '--path',
    multiple=True,
    help="""\
Path to thing (identifier) to inline. Can be given multiple times.  Paths can
point to keys inside nested objects, and inlining multiple levels of nested
intermediate objects is possible. Keys spanning nesting levels must be given
`::` separated (e.g., `influenced_by::object::name`).  Fields identified by a
path (including intermediate levels) may be multivalued.
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
    show_default=True,
    **stdargs['collection'],
)
def cli(
    path: tuple[str, ...],
    api_url: str,
    token: str | None,
    record_cache: RecordCache,
    collection=('public',),
):
    """Inline nested Things PID references

    Read JSON records from stdin, resolve PID references at the given
    field paths, and write the updated records to stdout.

    Use `::` to traverse nested fields. If a value at any matched path
    is a PID string, such as `collection:123`, it is replaced with the
    full record fetched from the API.

    Examples:

    \b
    query-things inline-things -p influenced_by::object::name
    query-things inline-things -p author -p references::items
    """

    get_obj = partial(
        _get_rec_from_any_collection,
        api_url=api_url,
        collections=collection,
        cache=record_cache,
        token=token,
    )

    paths = [tuple(p.split('::')) for p in path]

    for _, rec in iter_json_objects():
        inline_json_objects(rec, paths, get_obj)
        click.echo(json.dumps(rec), nl=True)
