import json
from collections.abc import (
    Iterator,
    KeysView,
    ValuesView,
)
from pathlib import Path
from typing import Any


class RecordCache:
    def __init__(
        self,
        path: Path | None = None,
        data: dict[str, Any] | None = None,
    ):
        self._path = path
        self._data = data if data is not None else {}

    @classmethod
    def load(cls, path: Path | None) -> 'RecordCache':
        if path is None:
            return cls(path=None)

        try:
            with path.open('r') as fp:
                data = json.load(fp)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        if not isinstance(data, dict):
            data = {}

        return cls(path=path, data=data)

    def get(self, pid: str, default: Any = None) -> Any:
        return self._data.get(pid, default)

    def keys(self) -> KeysView[str]:
        return self._data.keys()

    def values(self) -> ValuesView[dict | None]:
        return self._data.values()

    def __getitem__(self, pid: str) -> dict | None:
        return self._data[pid]

    def __contains__(self, pid: str) -> bool:
        return pid in self._data

    def __setitem__(self, pid: str, rec: dict | None) -> None:
        self._data[pid] = rec

    def __delitem__(self, pid: str) -> None:
        del self._data[pid]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def save(self) -> None:
        if self._path is None:
            return

        if not self._data:
            return

        with self._path.open('w') as fp:
            json.dump(self._data, fp)


def _handle_record_cache(ctx, _, value) -> RecordCache:
    cache = RecordCache.load(value)

    @ctx.call_on_close
    def dump_cache():
        cache.save()

    return cache
