import json

import pytest
from click.testing import CliRunner
from jinja2 import Environment

from query_things.render_record import (
    _proc_rec,
    cli,
    toyaml,
)


@pytest.fixture
def jinja_env():
    env = Environment(autoescape=True)
    env.filters['toyaml'] = toyaml
    return env


def test_proc_rec_renders_record_to_output_file(
    tmp_path,
    jinja_env,
    capsys,
):
    template = jinja_env.from_string('Name: {{ name }}\nPID: {{ pid }}\n')

    record = {
        'pid': 'EXAMPLE:123',
        'name': 'Example record',
    }

    output_template = str(tmp_path / 'output' / '{__pid_curie_reference}.txt')

    _proc_rec(
        record,
        template,
        output_filename_template=(output_template,),
    )

    output_path = tmp_path / 'output' / '123.txt'

    assert output_path.exists()
    assert output_path.read_text() == ('Name: Example record\nPID: EXAMPLE:123')


def test_proc_rec_makes_top_level_record_keys_available(
    tmp_path,
    jinja_env,
):
    template = jinja_env.from_string('{{ title }}\n{{ nested.value }}\n')

    record = {
        'pid': 'EXAMPLE:1',
        'title': 'A title',
        'nested': {
            'value': 'A nested value',
        },
    }

    output_path = tmp_path / 'output.txt'

    _proc_rec(
        record,
        template,
        output_filename_template=(str(output_path),),
    )

    assert output_path.read_text() == 'A title\nA nested value'


def test_proc_rec_normalizes_annotations(
    tmp_path,
    jinja_env,
):
    template = jinja_env.from_string(
        '{{ annotations.simple }}\n{{ annotations.complex }}\n'
    )

    record = {
        'pid': 'EXAMPLE:1',
        'annotations': {
            'simple': 'simple value',
            'complex': {
                'annotation_value': 'complex value',
                'other_field': 'discarded',
            },
        },
    }

    output_path = tmp_path / 'output.txt'

    _proc_rec(
        record,
        template,
        output_filename_template=(str(output_path),),
    )

    assert record['annotations'] == {
        'simple': 'simple value',
        'complex': 'complex value',
    }
    assert output_path.read_text() == ('simple value\ncomplex value')


def test_proc_rec_handles_missing_annotations(
    tmp_path,
    jinja_env,
):
    template = jinja_env.from_string('{{ name }}')

    record = {
        'pid': 'EXAMPLE:1',
        'name': 'No annotations',
    }

    output_path = tmp_path / 'output.txt'

    _proc_rec(
        record,
        template,
        output_filename_template=(str(output_path),),
    )

    assert output_path.read_text() == 'No annotations'


def test_proc_rec_uses_first_successful_output_filename_template(
    tmp_path,
    jinja_env,
):
    template = jinja_env.from_string('{{ name }}')

    record = {
        'pid': 'EXAMPLE:abc',
        'name': 'Example',
        'annotations': {},
    }

    invalid_template = str(tmp_path / 'missing' / '{annotations[missing]}.txt')
    valid_template = str(tmp_path / 'records' / '{__pid_curie_reference}.txt')

    _proc_rec(
        record,
        template,
        output_filename_template=(
            invalid_template,
            valid_template,
        ),
    )

    output_path = tmp_path / 'records' / 'abc.txt'

    assert output_path.exists()
    assert output_path.read_text() == 'Example'


def test_proc_rec_can_use_annotation_in_output_filename(
    tmp_path,
    jinja_env,
):
    template = jinja_env.from_string('{{ name }}')

    record = {
        'pid': 'EXAMPLE:abc',
        'name': 'Example',
        'annotations': {
            'target_id': {
                'annotation_value': 'target-123',
            },
        },
    }

    output_template = str(
        tmp_path / 'content' / '{annotations[target_id]}' / '_index.md'
    )

    _proc_rec(
        record,
        template,
        output_filename_template=(output_template,),
    )

    output_path = tmp_path / 'content' / 'target-123' / '_index.md'

    assert output_path.exists()
    assert output_path.read_text() == 'Example'


def test_proc_rec_provides_special_template_variables(
    tmp_path,
    jinja_env,
):
    template = jinja_env.from_string(
        '{% if __datetime %}'
        'has datetime;'
        '{% endif %}'
        '{% if __datetime_now %}'
        'has datetime_now;'
        '{% endif %}'
        '{{ __pid_curie_reference }};'
        '{{ __rec.name }}'
    )

    record = {
        'pid': 'EXAMPLE:abc',
        'name': 'Example',
    }

    output_path = tmp_path / 'output.txt'

    _proc_rec(
        record,
        template,
        output_filename_template=(str(output_path),),
    )

    assert output_path.read_text() == ('has datetime;has datetime_now;abc;Example')


def test_proc_rec_provides_toyaml_filter(
    tmp_path,
    jinja_env,
):
    template = jinja_env.from_string('{{ data | toyaml }}')

    record = {
        'pid': 'EXAMPLE:1',
        'data': {
            'name': 'Example',
            'values': [1, 2, 3],
        },
    }

    output_path = tmp_path / 'output.yaml'

    _proc_rec(
        record,
        template,
        output_filename_template=(str(output_path),),
    )

    assert output_path.read_text() == ('name: Example\nvalues:\n- 1\n- 2\n- 3\n')


def test_proc_rec_raises_when_all_filename_templates_fail(
    tmp_path,
    jinja_env,
):
    template = jinja_env.from_string('{{ name }}')

    record = {
        'pid': 'EXAMPLE:1',
        'name': 'Example',
    }

    output_templates = (
        str(tmp_path / '{missing_key}.txt'),
        str(tmp_path / '{annotations[missing_annotation]}.txt'),
    )

    with pytest.raises(
        ValueError,
        match='All given output filename templates errored on record',
    ):
        _proc_rec(
            record,
            template,
            output_filename_template=output_templates,
        )


def test_proc_rec_supports_custom_jinja_delimiters(tmp_path):
    env = Environment(
        block_start_string='[% ',
        block_end_string=' %]',
        variable_start_string='[[',
        variable_end_string=']]',
        comment_start_string='[#!',
        comment_end_string='!#]',
        autoescape=True,
    )

    template = env.from_string('[[ name ]]')

    record = {
        'pid': 'EXAMPLE:1',
        'name': 'Custom delimiters',
    }

    output_path = tmp_path / 'output.txt'

    _proc_rec(
        record,
        template,
        output_filename_template=(str(output_path),),
    )

    assert output_path.read_text() == 'Custom delimiters'


def test_cli_reads_json_records_from_stdin(tmp_path):
    template_path = tmp_path / 'record.j2'
    template_path.write_text('Name: {{ name }}')

    output_path = tmp_path / 'output.txt'

    record = {
        'pid': 'EXAMPLE:1',
        'name': 'Example',
    }

    result = CliRunner().invoke(
        cli,
        [
            str(template_path),
            str(output_path),
        ],
        input=json.dumps(record) + '\n',
    )

    assert result.exit_code == 0, result.output
    assert output_path.read_text() == 'Name: Example'
