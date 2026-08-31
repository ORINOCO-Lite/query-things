from pathlib import Path

import click

from .api import (  # noqa: TID252
    make_record_resolver,
)
from .cache import (  # noqa: TID252
    RecordCache,
    _handle_record_cache,
)
from .io import iter_json_objects  # noqa: TID252
from .jsonl import parse_json_objects, try_parse_record  # noqa: TID252
from .linking import (  # noqa: TID252
    all_records_have_links,
    iter_link_pids,
    record_has_link,
    record_has_link_any,
)
from .records import homogenize_annotations  # noqa: TID252

__all__ = [
    'RecordCache',
    'all_records_have_links',
    'homogenize_annotations',
    'iter_json_objects',
    'iter_link_pids',
    'make_record_resolver',
    'parse_json_objects',
    'record_has_link',
    'record_has_link_any',
    'stdargs',
    'try_parse_record',
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
