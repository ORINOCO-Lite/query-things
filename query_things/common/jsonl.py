import json
from collections.abc import Iterable, Iterator


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


def try_parse_record(line: str) -> dict | None:
    """Parse a single line as a JSON record.

    Returns None for any input that is not a JSON object with a
    string `pid` property.
    """
    try:
        rec = json.loads(line)
    except ValueError:
        return None

    if not isinstance(rec, dict):
        return None

    pid = rec.get('pid')
    if not isinstance(pid, str):
        return None

    return rec
