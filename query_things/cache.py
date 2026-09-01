from query_things.common import (
    Record,
    RecordCache,
)


def cache_record(record: Record, cache: RecordCache) -> Record:
    """Store JSON record in `cache`, passing it through.

    A record that does not have a 'pid' key is silently ignored
    by the cache, but is still returned.
    """
    if 'pid' in record:
        cache[record['pid']] = record
    return record
