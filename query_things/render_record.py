from collections.abc import (
    Iterable,
    Sequence,
)
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jinja2 import (
    Environment,
    FileSystemLoader,
    select_autoescape,
)

from query_things.common import (
    homogenize_annotations,
    parse_json_objects,
)

default_inlineblock_delims = ('{', '}')
default_statement_marker = '%'
default_comment_marker = '#'


def toyaml(obj):
    """Custom filter to convert an object to a YAML string"""
    return yaml.safe_dump(
        obj,
        sort_keys=False,
        default_flow_style=False,
    )


def make_jinja_env(
    template_dir: Path,
    *,
    block_delims: tuple[str, str] = default_inlineblock_delims,
    statement_marker: str = default_statement_marker,
    comment_marker: str = default_comment_marker,
) -> Environment:
    """Create the Jinja environment used to render record templates."""
    jinja_env = Environment(
        loader=FileSystemLoader(template_dir),
        block_start_string=f'{block_delims[0]}{statement_marker}',
        block_end_string=f'{statement_marker}{block_delims[1]}',
        variable_start_string=f'{block_delims[0]}{block_delims[0]}',
        variable_end_string=f'{block_delims[1]}{block_delims[1]}',
        comment_start_string=f'{block_delims[0]}{comment_marker}',
        comment_end_string=f'{comment_marker}{block_delims[1]}',
        # TODO: this feature seems useful, add support
        # line_statement_prefix = f'',
        # line_comment_prefix = f'',
        autoescape=select_autoescape(['html', 'htm', 'xml']),
    )

    # register filter to become available within a template
    jinja_env.filters['toyaml'] = toyaml
    return jinja_env


def render_records(
    lines: Iterable[str],
    template,
    *,
    output_filename_template: Sequence[str],
) -> None:
    """Render each input record with `template`, writing output files."""
    for _, rec in parse_json_objects(lines):
        _proc_rec(
            rec,
            template,
            output_filename_template=tuple(output_filename_template),
        )


def _proc_rec(
    rec: dict[str, Any],
    template,
    *,
    output_filename_template: tuple[str, ...],
):
    homogenize_annotations(rec)
    props = dict(rec)
    props.update(
        {
            '__datetime': datetime,
            '__datetime_now': datetime.now(),  # noqa: DTZ005
            '__pid_curie_reference': rec['pid'].split(':', maxsplit=1)[1],
            '__rec': rec,
        }
    )
    output_filepath = None
    for ofnt in output_filename_template:
        try:
            output_filepath = Path(ofnt.format(**props))
            break
        except (KeyError, IndexError, ValueError):
            pass
    if output_filepath is None:
        msg = 'All given output filename templates errored on record'
        raise ValueError(msg)
    output_filepath.parent.mkdir(parents=True, exist_ok=True)
    rendered_rec = template.render(**props)
    output_filepath.write_text(rendered_rec)
