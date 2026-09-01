import json
from collections.abc import Iterable, Iterator
from typing import Any


def parse_json_objects(lines: Iterable[str]) -> Iterator[tuple[str, dict]]:
    """Yield (line, record) pairs for valid JSON-object input lines.

    Blank lines are skipped. A ValueError is raised for lines that are
    not valid JSON objects with a string `pid` property.
    """
    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue

        try:
            rec = json.loads(stripped)
        except json.JSONDecodeError as e:
            msg = f'Invalid JSON on line {lineno}: {e}'
            raise ValueError(msg) from e

        if not isinstance(rec, dict):
            msg = f'Line {lineno} must be a JSON object'
            raise ValueError(msg)  # noqa: TRY004

        pid = rec.get('pid')
        if not isinstance(pid, str):
            msg = f"Line {lineno} must have a string 'pid'"
            raise ValueError(msg)  # noqa: TRY004

        yield line, rec


def jsonl_from_record(record: dict[str, Any]) -> str:
    """Render `record` as a JSON line string"""
    return json.dumps(
        record,
        ensure_ascii=True,
        separators=(',', ':'),
    )
