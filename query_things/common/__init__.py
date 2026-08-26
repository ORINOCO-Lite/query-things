from pathlib import Path

import click

from .api import _get_rec_from_any_collection  # noqa: TID252
from .cache import _handle_record_cache  # noqa: TID252
from .io import iter_json_objects  # noqa: TID252

__all__ = [
    '_get_rec_from_any_collection',
    '_handle_record_cache',
    'iter_json_objects',
    'stdargs',
]

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
