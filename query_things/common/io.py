import json
import sys

import click


def iter_json_objects():
    for lineno, line in enumerate(sys.stdin, 1):
        stripped = line.strip()
        if not stripped:
            continue

        try:
            rec = json.loads(stripped)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON on line {lineno}: {e}"
            raise click.ClickException(msg) from e

        if not isinstance(rec, dict):
            msg = f"Line {lineno} must be a JSON object"
            raise click.ClickException(msg)

        pid = rec.get('pid')
        if not isinstance(pid, str):
            msg = f"Line {lineno} must have a string 'pid'"
            raise click.ClickException(msg)

        yield line, rec
