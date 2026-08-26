from collections.abc import (
    Callable,
    Sequence,
)

from dump_things_pyclient.communicate import (  # type: ignore[import-untyped]
    collection_read_record_with_pid,
)

from query_things.common.cache import RecordCache


def make_record_resolver(
    api_url: str,
    collections: Sequence[str],
    cache: RecordCache,
    token: str | None = None,
) -> Callable[[str], dict | None]:
    def resolver(pid: str) -> dict | None:
        return _get_rec_from_any_collection(
            api_url=api_url,
            collections=collections,
            pid=pid,
            cache=cache,
            token=token,
        )

    return resolver


def _get_rec_from_any_collection(
    api_url: str,
    collections: Sequence[str],
    pid: str,
    cache: RecordCache,
    token: str | None = None,
):
    for col in collections:
        rec = cache.get(pid) or collection_read_record_with_pid(
            api_url,
            col,
            pid,
            token=token,
        )
        if rec is not None:
            cache[pid] = rec
            return rec

    # yes, also cache that we asked and nothing was there
    cache[pid] = None
    return None
