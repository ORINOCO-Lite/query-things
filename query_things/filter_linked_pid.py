from collections.abc import Set as AbstractSet

from dump_things_pyclient.communicate import (  # type: ignore[import-untyped]
    collection_read_record_with_pid,
)

from query_things.common import (
    Record,
    iter_link_pids,
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


def record_matches_pids(
    record: Record,
    pids: AbstractSet[str],
) -> bool:
    """Returns whether the record's `pid` is contained in `pids`."""
    return record['pid'] in pids
