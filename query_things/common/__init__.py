from pathlib import Path

import click

from .api import (
    make_record_resolver,
)
from .cache import (  # noqa: TID252
    _handle_record_cache,
    RecordCache,
)
from .io import iter_json_objects  # noqa: TID252
from .linking import (
    all_records_have_links,
    iter_link_pids,
    record_has_link,
)
from .records import homogenize_annotations  # noqa: TID252

__all__ = [
    '_handle_record_cache',
    'RecordCache',
    'all_records_have_links',
    'iter_json_objects',
    'iter_link_pids',
    'homogenize_annotations',
    'make_record_resolver',
    'record_has_link',
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
