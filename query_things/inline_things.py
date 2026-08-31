import json
from collections.abc import (
    Callable,
    Iterable,
    Iterator,
    Sequence,
)
from typing import Any

from query_things.common import (
    parse_json_objects,
)


def is_pid_like(value: object) -> bool:
    return isinstance(value, str) and bool(value) and ':' in value


def inline_value(
    value: Any,
    get_obj: Callable[[str], dict[str, Any] | None],
) -> Any:
    if isinstance(value, str):
        if is_pid_like(value):
            resolved = get_obj(value)
            if resolved is not None:
                return resolved
        return value

    if isinstance(value, list):
        return [inline_value(item, get_obj) for item in value]

    return value


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

        if len(path) == 1:
            container[key] = inline_value(value, get_obj)
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


def inline_things(
    lines: Iterable[str],
    paths: Sequence[Sequence[str]],
    resolver: Callable[[str], dict | None],
) -> Iterator[str]:
    """Yield input records with PID references inlined at the given paths."""
    for _, rec in parse_json_objects(lines):
        inline_json_objects(rec, paths, resolver)
        yield json.dumps(rec)
