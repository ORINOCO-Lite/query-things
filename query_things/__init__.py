import json
import sys
from pathlib import Path

import click
from dump_things_pyclient.communicate import (
    collection_read_record_with_pid,
)


def _handle_record_cache(ctx, _, value) -> dict:
    if value is None:
        # we return a cache, but it will be in-memory only
        return {}

    try:
        with value.open('r') as fp:
            cache = json.load(fp)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        # ok if it doesn't exist yet. If it doesn't load, we ignore it
        cache = {}

    # protect against invalid cache content
    if not isinstance(cache, dict):
        cache = {}

    @ctx.call_on_close
    def dump_cache():
        if not cache:
            # do not write an empty cache
            return
        with value.open('w') as fp:
            json.dump(cache, fp)

    return cache


# this collection cannot contain the help strings.
# they are hard to write generic and still be fitting.
# also, arguments do not have help.
stdargs = {
    '--api-url': {
        'envvar': 'DUMPTHINGS_APIURL',
        'show_envvar': True,
        'required': True,
    },
    'collection': {},
    '--token': {
        'envvar': 'DUMPTHINGS_TOKEN',
        'show_envvar': True,
    },
    '--record-cache': {
        'envvar': 'QRI_RECORD_CACHE',
        'callback': _handle_record_cache,
        'type': click.Path(
            file_okay=True, dir_okay=False, writable=True, readable=True, path_type=Path
        ),
        'show_envvar': True,
    },
}


def _get_rec_from_any_collection(
    api_url: str,
    collections: tuple[str],
    pid: str,
    cache: dict,
    token: str | None = None,
):
    for col in collections:
        rec = cache.get(pid) or collection_read_record_with_pid(
            api_url,
            col,
            pid,
            token=token,
        )
        if rec is not None:
            cache[pid] = rec
            return rec

    # yes, also cache that we asked and nothing was there
    cache[pid] = None
    return None


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
