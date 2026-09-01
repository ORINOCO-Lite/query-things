from typing import (
    Any,
    TypeAlias,
)

from .api import make_record_resolver  # noqa: TID252
from .cache import RecordCache  # noqa: TID252
from .jsonl import parse_json_objects, try_parse_record  # noqa: TID252
from .linking import (  # noqa: TID252
    all_records_have_links,
    iter_link_pids,
    record_has_link,
    record_has_link_any,
)
from .records import homogenize_annotations  # noqa: TID252

# standard type to use anywhere a record goes
Record: TypeAlias = dict[str, Any]


__all__ = [
    'Record',
    'RecordCache',
    'all_records_have_links',
    'homogenize_annotations',
    'iter_link_pids',
    'make_record_resolver',
    'parse_json_objects',
    'record_has_link',
    'record_has_link_any',
    'try_parse_record',
]
