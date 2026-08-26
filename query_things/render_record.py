import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click
import yaml
from jinja2 import (
    Environment,
    FileSystemLoader,
)
from query_things import iter_json_objects

default_inlineblock_delims = default = ('{', '}')
default_statement_marker = '%'
default_comment_marker = '#'


def toyaml(obj):
    """Custom filter to convert an object to a YAML string"""
    return yaml.safe_dump(
        obj,
        sort_keys=False,
        default_flow_style=False,
    )


def homogenize_annotations(rec):
    annotations = rec.get('annotations')
    if not isinstance(annotations, dict):
        return

    rec['annotations'] = {
        k: (
            v['annotation_value']
            if isinstance(v, dict) and 'annotation_value' in v
            else v
        )
        for k, v in annotations.items()
    }


@click.command('render-record')
@click.argument(
    'template',
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        path_type=Path,
    ),
)
@click.argument(
    'output-filename-template',
    required=True,
    nargs=-1,
)
@click.option(
    '--jinja-block-delims',
    metavar='<START> <END>',
    default=default_inlineblock_delims,
    nargs=2,
)
@click.option('--jinja-statement-marker', default=default_statement_marker)
@click.option('--jinja-comment-marker', default=default_comment_marker)
def cli(
    template: Path,
    output_filename_template: tuple[str, ...],
    jinja_block_delims: tuple[str, str] = default_inlineblock_delims,
    jinja_statement_marker: str = default_statement_marker,
    jinja_comment_marker: str = default_comment_marker,
):
    """Render records with a Jinja template

    This is a generic helper with no understanding of the nature of the
    provided Jinja2 template.

    The values corresponding to all top-level keys of a record are made
    available as direct variables for template rendering using the
    respective as a variable name. In addition, the following variables
    are also provided:

    \b
    __datetime: Python's `datetime` (`from datatime import datetime`)
    __datetime_now: `datetime.now()`,
    __pid_curie_reference: the non-prefix part of a CURIE-type record PID
    __rec: the entire record as a single object

    A `toyaml` filter is provided in addition to the standard Jinja filters.
    It can be used to convert any object to a YAML-compliant string.

    Two command takes two mandatory arguments: 1) a path to the template
    to render, and 2) a template-string to construct the output filename
    for an individual record. This template-string is parameterized with
    same variables as the template itself.

    More than one output file name template-string can be given. In this
    case, they will be tried in order, and the first one to successfully
    instantiate will be used. The following example shows how a particular
    annotation tag can be used to determine a path, and fall back on a
    generic default, if that does not work, because the annotation tag is
    not present.

    \b
      qri render-record <template> \\
          'content/{annotations[target_id]}/_index.md' \\
          'content/{__pid_curie_reference}/_index.md'
    """
    template_dir = template.parent or Path.cwd()
    jinja_env = Environment(
        loader=FileSystemLoader(template_dir),
        block_start_string=f'{jinja_block_delims[0]}{jinja_statement_marker}',
        block_end_string=f'{jinja_statement_marker}{jinja_block_delims[1]}',
        variable_start_string=f'{jinja_block_delims[0]}{jinja_block_delims[0]}',
        variable_end_string=f'{jinja_block_delims[1]}{jinja_block_delims[1]}',
        comment_start_string=f'{jinja_block_delims[0]}{jinja_comment_marker}',
        comment_end_string=f'{jinja_comment_marker}{jinja_block_delims[1]}',
        # TODO: this feature seems useful, add support
        # line_statement_prefix = f'',
        # line_comment_prefix = f'',
    )

    # register filter to become available within a template
    jinja_env.filters['toyaml'] = toyaml

    tmpl = jinja_env.get_template(template.name)
    for _, rec in iter_json_objects():
        _proc_rec(
            rec,
            tmpl,
            output_filename_template=output_filename_template,
        )


def _proc_rec(
    rec: dict[str, Any],
    template,
    *,
    output_filename_template: tuple[str, ...],
):
    homogenize_annotations(rec)
    props = dict(rec)
    props.update({
        '__datetime': datetime,
        '__datetime_now': datetime.now(),  # noqa: DTZ005
        '__pid_curie_reference': rec['pid'].split(':', maxsplit=1)[1],
        '__rec': rec,
    })
    output_filepath = None
    for ofnt in output_filename_template:
        try:
            output_filepath = Path(ofnt.format(**props))
            break
        except Exception as e:  # noqa: BLE001
            print(e, file=sys.stderr)  # noqa: T201
    if output_filepath is None:
        msg = 'All given output filename templates errored on record'
        raise ValueError(msg)
    output_filepath.parent.mkdir(parents=True, exist_ok=True)
    rendered_rec = template.render(**props)
    output_filepath.write_text(rendered_rec)
