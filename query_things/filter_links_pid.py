from collections.abc import (
    Callable,
    Sequence,
)
from pathlib import Path

from query_things.common import (
    Record,
    record_has_link,
    record_has_link_any,
)


def read_pids(path: Path | str) -> frozenset[str]:
    """Read PIDs from a file, one PID per line. Blank lines are ignored."""
    path = Path(path)
    with path.open('r', encoding='utf-8') as fp:
        return frozenset(line.strip() for line in fp if line.strip())


def record_links_pid(
    rec: Record,
    links: Sequence[tuple[str, str]] = (),
    file_links: Sequence[tuple[str, frozenset[str]]] = (),
    resolver: Callable[[str], dict | None] | None = None,
    *,
    recursive: bool = False,
) -> bool:
    """Return if record has all the given links.

    For each `links` entry, the record must link to the given target PID
    via the given property. For each `file_links` entry, the record must
    link to any of the given target PIDs via the given property.
    """
    return all(
        record_has_link(
            rec,
            prop,
            pid,
            resolver=resolver,
            recursive=recursive,
        )
        for prop, pid in links
    ) and all(
        record_has_link_any(
            rec,
            prop,
            pids,
            resolver=resolver,
            recursive=recursive,
        )
        for prop, pids in file_links
    )
