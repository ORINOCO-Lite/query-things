import json
from collections.abc import Iterable, Iterator
from typing import Any

from dump_things_pyclient.communicate import (  # type: ignore[import-untyped]
    collection_read_records_of_class,
)

from query_things.common import (
    parse_json_objects,
    record_has_link,
)


def inject_links_pid(
    lines: Iterable[str],
    *,
    inject: str,
    link: tuple[str, ...],
    api_url: str,
    collections: tuple[str, ...] = ('public',),
    class_name: str | None = None,
    token: str | None = None,
) -> Iterator[str]:
    """Yield input records with linking records injected at `inject`.

    For each input record, records from the given collections are looked
    up that link to the record via any of the given `link` properties.
    Those records are added to the value of the `inject` property: the
    property is created if absent, extended if it is a list, or promoted
    to a list if it holds a single value.
    """
    for _, rec in parse_json_objects(lines):
        _proc_record(
            rec,
            inject=inject,
            collections=collections,
            link=link,
            class_name=class_name,
            api_url=api_url,
            token=token,
        )
        yield json.dumps(rec, ensure_ascii=True, separators=(',', ':'))


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
    return [
        res[0]
        for res in collection_read_records_of_class(
            api_url,
            collection,
            class_name if class_name else 'Thing',
            matching=pid,
            token=token,
        )
        if any(record_has_link(res[0], prop_id, pid) for prop_id in link)
    ]
