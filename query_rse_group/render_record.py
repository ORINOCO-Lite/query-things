import click
from datetime import datetime
from jinja2 import (
    Environment,
    FileSystemLoader,
)
import json
from pathlib import Path
import sys

default_inlineblock_delims = default=('{', '}')
default_statement_marker = '%'
default_comment_marker = '#'


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
    output_filename_template: str,
    jinja_block_delims: tuple[str, str] = default_inlineblock_delims,
    jinja_statement_marker: str = default_statement_marker,
    jinja_comment_marker: str = default_comment_marker,
):
    """Render a template with a metadata record as input

    This is a generic helper with no understanding of the nature of the
    provided Jinja2 template.
    """
    template_dir = template.parent if template.parents else Path.cwd()
    jinja_env = Environment(
        loader=FileSystemLoader(template_dir),
        block_start_string=f'{jinja_block_delims[0]}{jinja_statement_marker}',
        block_end_string=f'{jinja_statement_marker}{jinja_block_delims[1]}',
        variable_start_string=f'{jinja_block_delims[0]}{jinja_block_delims[0]}',
        variable_end_string=f'{jinja_block_delims[1]}{jinja_block_delims[1]}',
        comment_start_string=f'{jinja_block_delims[0]}{jinja_comment_marker}',
        comment_end_string=f'{jinja_comment_marker}{jinja_block_delims[1]}',
        # TODO this feature seems useful, add support
        #line_statement_prefix = f'',
        #line_comment_prefix = f'',
    )
    template = jinja_env.get_template(template.name)
    for line in sys.stdin:
        rec = json.loads(line)
        rec.update(
            __datetime=datetime,
            __datetime_now=datetime.now(),
        )
        props = {
            '__pid_curie_reference': rec['pid'].split(':', maxsplit=1)[1],
        }
        props.update(rec)
        output_filepath = Path(output_filename_template.format(**props))
        output_filepath.parent.mkdir(exist_ok=True)
        rendered_rec = template.render(**rec)
        output_filepath.write_text(rendered_rec)
