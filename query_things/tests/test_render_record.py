import pytest
from jinja2 import Environment

from query_things.cli.render_record import cli
from query_things.render_record import _proc_rec, toyaml
from query_things.tests import (
    jsonl_lines,
    make_record,
)


@pytest.fixture
def jinja_env():
    env = Environment(autoescape=True)
    env.filters['toyaml'] = toyaml
    return env


@pytest.fixture
def render_record(tmp_path, jinja_env):
    """Render a record with `_proc_rec` and return the generated file path."""

    def _render(record, template_source, output_templates, env=None):
        template = (env or jinja_env).from_string(template_source)

        _proc_rec(
            record,
            template,
            output_filename_template=tuple(output_templates),
        )

        files = [path for path in tmp_path.rglob('*') if path.is_file()]
        assert len(files) == 1, f'Expected exactly one output file, got: {files}'
        return files[0]

    return _render


def test_renders_record_to_output_file(render_record, tmp_path):
    path = render_record(
        make_record('EXAMPLE:123', name='Example record'),
        'Name: {{ name }}\nPID: {{ pid }}\n',
        [str(tmp_path / 'output' / '{__pid_curie_reference}.txt')],
    )

    assert path == tmp_path / 'output' / '123.txt'
    assert path.read_text(encoding='utf-8') == (
        'Name: Example record\nPID: EXAMPLE:123'
    )


def test_makes_top_level_record_keys_available(render_record, tmp_path):
    path = render_record(
        make_record(
            'EXAMPLE:1',
            title='A title',
            nested={'value': 'A nested value'},
        ),
        '{{ title }}\n{{ nested.value }}\n',
        [str(tmp_path / 'output.txt')],
    )

    assert path.read_text(encoding='utf-8') == 'A title\nA nested value'


def test_normalizes_annotations(render_record, tmp_path):
    record = make_record(
        'EXAMPLE:1',
        annotations={
            'simple': 'simple value',
            'complex': {
                'annotation_value': 'complex value',
                'other_field': 'discarded',
            },
        },
    )

    path = render_record(
        record,
        '{{ annotations.simple }}\n{{ annotations.complex }}\n',
        [str(tmp_path / 'output.txt')],
    )

    assert record['annotations'] == {
        'simple': 'simple value',
        'complex': 'complex value',
    }
    assert path.read_text(encoding='utf-8') == 'simple value\ncomplex value'


def test_handles_missing_annotations(render_record, tmp_path):
    path = render_record(
        make_record('EXAMPLE:1', name='No annotations'),
        '{{ name }}',
        [str(tmp_path / 'output.txt')],
    )

    assert path.read_text(encoding='utf-8') == 'No annotations'


def test_uses_first_successful_output_filename_template(render_record, tmp_path):
    record = make_record(
        'EXAMPLE:abc',
        name='Example',
        annotations={},
    )

    invalid_template = str(tmp_path / 'missing' / '{annotations[missing]}.txt')
    valid_template = str(tmp_path / 'records' / '{__pid_curie_reference}.txt')

    path = render_record(
        record,
        '{{ name }}',
        [invalid_template, valid_template],
    )

    assert path == tmp_path / 'records' / 'abc.txt'
    assert path.read_text(encoding='utf-8') == 'Example'


def test_can_use_annotation_in_output_filename(render_record, tmp_path):
    record = make_record(
        'EXAMPLE:abc',
        name='Example',
        annotations={
            'target_id': {
                'annotation_value': 'target-123',
            },
        },
    )

    path = render_record(
        record,
        '{{ name }}',
        [str(tmp_path / 'content' / '{annotations[target_id]}' / '_index.md')],
    )

    assert path == tmp_path / 'content' / 'target-123' / '_index.md'
    assert path.read_text(encoding='utf-8') == 'Example'


def test_provides_special_template_variables(render_record, tmp_path):
    template = (
        '{% if __datetime %}'
        'has datetime;'
        '{% endif %}'
        '{% if __datetime_now %}'
        'has datetime_now;'
        '{% endif %}'
        '{{ __pid_curie_reference }};'
        '{{ __rec.name }}'
    )

    path = render_record(
        make_record('EXAMPLE:abc', name='Example'),
        template,
        [str(tmp_path / 'output.txt')],
    )

    assert path.read_text(encoding='utf-8') == (
        'has datetime;has datetime_now;abc;Example'
    )


def test_provides_toyaml_filter(render_record, tmp_path):
    path = render_record(
        make_record(
            'EXAMPLE:1',
            data={
                'name': 'Example',
                'values': [1, 2, 3],
            },
        ),
        '{{ data | toyaml }}',
        [str(tmp_path / 'output.yaml')],
    )

    assert path.read_text(encoding='utf-8') == (
        'name: Example\nvalues:\n- 1\n- 2\n- 3\n'
    )


def test_raises_when_all_filename_templates_fail(tmp_path, jinja_env):
    template = jinja_env.from_string('{{ name }}')
    record = make_record('EXAMPLE:1', name='Example')

    with pytest.raises(
        ValueError,
        match='All given output filename templates errored on record',
    ):
        _proc_rec(
            record,
            template,
            output_filename_template=(
                str(tmp_path / '{missing_key}.txt'),
                str(tmp_path / '{annotations[missing_annotation]}.txt'),
            ),
        )


def test_supports_custom_jinja_delimiters(render_record, tmp_path):
    env = Environment(
        block_start_string='[% ',
        block_end_string=' %]',
        variable_start_string='[[',
        variable_end_string=']]',
        comment_start_string='[#!',
        comment_end_string='!#]',
        autoescape=True,
    )
    env.filters['toyaml'] = toyaml

    path = render_record(
        make_record('EXAMPLE:1', name='Custom delimiters'),
        '[[ name ]]',
        [str(tmp_path / 'output.txt')],
        env=env,
    )

    assert path.read_text(encoding='utf-8') == 'Custom delimiters'


def test_cli_reads_json_records_from_stdin(runner, tmp_path):
    template_path = tmp_path / 'record.j2'
    template_path.write_text('Name: {{ name }}', encoding='utf-8')

    output_path = tmp_path / 'output.txt'

    result = runner.invoke(
        cli,
        [
            str(template_path),
            str(output_path),
        ],
        input=jsonl_lines(make_record('EXAMPLE:1', name='Example')),
    )

    assert result.exit_code == 0, result.output
    assert output_path.read_text(encoding='utf-8') == 'Name: Example'
