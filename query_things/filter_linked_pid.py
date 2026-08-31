from collections.abc import Iterable, Iterator
from collections.abc import Set as AbstractSet

from dump_things_pyclient.communicate import (  # type: ignore[import-untyped]
    collection_read_record_with_pid,
)

from query_things.common import (
    iter_link_pids,
    parse_json_objects,
)


def get_reference_linked_pids(
    collection: str,
    pid: str,
    property: str,  # noqa: A002
    api_url: str,
    token: str | None = None,
) -> frozenset[str]:
    """Collect all PIDs linked via `property` by the referenced record."""
    ref = collection_read_record_with_pid(
        service_url=api_url,
        collection=collection,
        pid=pid,
        token=token,
    )
    return frozenset(iter_link_pids(ref.get(property)))


def filter_linked_pid(
    lines: Iterable[str],
    linked_pids: AbstractSet[str],
) -> Iterator[str]:
    """Yield only records whose `pid` is contained in `linked_pids`."""
    for line, rec in parse_json_objects(lines):
        if rec['pid'] in linked_pids:
            yield line
