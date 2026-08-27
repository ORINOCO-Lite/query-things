# query_things/common/linking.py
from collections.abc import Callable, Iterable, Sequence
from typing import Any

PID_KEY = 'object'


def iter_link_pids(value: Any, key: str = PID_KEY) -> Iterable[str]:
    """
    Normalize a Things linkage property into an iterable of PIDs.

    Supports:
      "abc"
      ["abc", "def"]
      {"object": "abc"}
      [{"object": "abc"}, {"object": "def"}]
      ["abc", {"object": "def"}]
    """
    if value is None:
        return

    if isinstance(value, (list, tuple)):
        for item in value:
            yield from iter_link_pids(item, key=key)
        return

    if isinstance(value, dict):
        pid = value.get(key)
        if pid is not None:
            yield pid
        return

    yield value


def record_has_link(
    rec: dict | None,
    prop: str,
    target_pid: str,
    resolver: Callable[[str], dict | None] | None = None,
    *,
    recursive: bool = False,
    visited: frozenset[str] | None = None,
) -> bool:
    """
    Return True if rec has a link to target_pid via prop.

    If recursive=True and resolver is provided, follow linked PIDs.
    """
    if rec is None:
        return False

    if prop not in rec:
        return False

    if visited is None:
        visited = frozenset()

    for pid in iter_link_pids(rec.get(prop)):
        if pid == target_pid:
            return True

        if recursive and resolver is not None and pid not in visited:
            linked_rec = resolver(pid)
            if record_has_link(
                linked_rec,
                prop,
                target_pid,
                resolver=resolver,
                recursive=True,
                visited=visited | {pid},
            ):
                return True

    return False


def all_records_have_links(
    rec: dict | None,
    links: Sequence[tuple[str, str]],
    resolver: Callable[[str], dict | None] | None = None,
    *,
    recursive: bool = False,
) -> bool:
    return all(
        record_has_link(
            rec,
            prop,
            pid,
            resolver=resolver,
            recursive=recursive,
        )
        for prop, pid in links
    )


def record_has_link_any(
    rec: dict | None,
    prop: str,
    target_pids: Iterable[str],
    resolver: Callable[[str], dict | None] | None = None,
    *,
    recursive: bool = False,
    visited: frozenset[str] | None = None,
) -> bool:
    """
    Return True if rec has a link to any target PID via prop.

    If recursive=True and resolver is provided, follow linked PIDs.
    """
    if rec is None:
        return False

    if prop not in rec:
        return False

    targets = set(target_pids)
    if not targets:
        return False

    if visited is None:
        visited = frozenset()

    for pid in iter_link_pids(rec.get(prop)):
        if isinstance(pid, str) and pid in targets:
            return True

        if (
            recursive
            and resolver is not None
            and isinstance(pid, str)
            and pid not in visited
        ):
            linked_rec = resolver(pid)
            if record_has_link_any(
                linked_rec,
                prop,
                targets,
                resolver=resolver,
                recursive=True,
                visited=visited | {pid},
            ):
                return True

    return False
