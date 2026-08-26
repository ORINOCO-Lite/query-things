from dump_things_pyclient.communicate import (
    collection_read_record_with_pid,
)

from query_things.common.cache import RecordCache


def _get_rec_from_any_collection(
    api_url: str,
    collections: tuple[str, ...],
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
