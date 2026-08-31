from pathlib import Path

import click

from query_things.common import RecordCache


def _handle_record_cache(ctx, _, value) -> RecordCache:
    cache = RecordCache.load(value)

    @ctx.call_on_close
    def dump_cache():
        cache.save()

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
