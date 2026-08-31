import sys
from pathlib import Path

import click

from query_things.render_record import (
    default_comment_marker,
    default_inlineblock_delims,
    default_statement_marker,
    make_jinja_env,
    render_records,
)


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
    __datetime: Python's `datetime` (`from datetime import datetime`)
    __datetime_now: `datetime.now()`,
    __pid_curie_reference: the non-prefix part of a CURIE-type record PID
    __rec: the entire record as a single object

    A `toyaml` filter is provided in addition to the standard Jinja filters.
    It can be used to convert any object to a YAML-compliant string.

    This command takes two mandatory arguments: 1) a path to the template
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
    jinja_env = make_jinja_env(
        template_dir,
        block_delims=jinja_block_delims,
        statement_marker=jinja_statement_marker,
        comment_marker=jinja_comment_marker,
    )

    tmpl = jinja_env.get_template(template.name)
    render_records(
        sys.stdin,
        tmpl,
        output_filename_template=output_filename_template,
    )
