from collections.abc import Iterable, Iterator

from query_things.common import (
    RecordCache,
    try_parse_record,
)


def cache_records(lines: Iterable[str], cache: RecordCache) -> Iterator[str]:
    """Store JSON records from `lines` in `cache`, passing them through.

    Lines that are not JSON objects with a string `pid` property are
    silently ignored by the cache, but are still yielded.
    """
    for line in lines:
        rec = try_parse_record(line)
        if rec is not None:
            cache[rec['pid']] = rec
        yield line
