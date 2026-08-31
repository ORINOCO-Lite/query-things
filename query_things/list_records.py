from collections.abc import Iterator

from query_things.common import RecordCache


def list_records(
    cache: RecordCache,
    *,
    pid: tuple[str, ...] = (),
    cls: tuple[str, ...] = (),
) -> Iterator[dict]:
    """Yield records from `cache`, optionally constrained by PIDs or classes.

    When PIDs are given, they take precedence over classes. A KeyError is
    raised if any of the given PIDs are not present in the cache; nothing
    is yielded in that case. Otherwise all cached records are yielded,
    constrained to the given classes via `schema_type`, if any are given.
    """
    if pid:
        missing = [p for p in pid if cache.get(p) is None]
        if missing:
            raise KeyError(missing)
        for p in pid:
            yield cache.get(p)
        return

    for rec in cache.values():
        if rec is None:
            continue
        if cls and rec.get('schema_type') not in cls:
            continue
        yield rec
