import json
from collections.abc import Mapping
from copy import deepcopy
from typing import Any


def make_record(pid: str, **fields: Any) -> dict[str, Any]:
    record = {'pid': pid}
    # deepcopy input to keep the complexity in the helper
    # and let the tests more freely feed information into
    # a record
    record.update({k: deepcopy(v) for k, v in fields.items()})
    return record


def jsonl_lines(*items: Any) -> str:
    """Build a JSON-lines string.

    Items may be dicts, in which case they are JSON-serialized, or raw
    strings, in which case they are treated as already-formed input lines.
    """
    lines = []
    for item in items:
        if isinstance(item, str):
            lines.append(item)
        else:
            lines.append(json.dumps(item))
    return ''.join(f'{line}\n' for line in lines)


def output_records(output: str) -> list[dict[str, Any]]:
    """Parse JSON-lines output into records."""
    return [json.loads(line) for line in output.splitlines() if line.strip()]


def cache_as_dict(cache: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize RecordCache or dict-like cache content for assertions."""
    return dict(zip(cache.keys(), cache.values(), strict=False))
