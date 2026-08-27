import json
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

import query_things.common.api as common_api
from query_things.filter_links_pid import _read_pids, cli


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture(autouse=True)
def no_api(monkeypatch):
    """
    Prevent accidental network access during command tests.

    Tests that need recursive resolution can override this mock using
    ``monkeypatch.setattr(common_api, '_get_rec_from_any_collection', ...)``.
    """
    monkeypatch.delenv('QRI_RECORD_CACHE', raising=False)
    monkeypatch.delenv('DUMPTHINGS_APIURL', raising=False)
    monkeypatch.delenv('DUMPTHINGS_TOKEN', raising=False)

    monkeypatch.setattr(
        common_api,
        '_get_rec_from_any_collection',
        lambda *args, **kwargs: None,  # noqa: ARG005
    )


@pytest.fixture
def sample_record():
    """Provide a sample JSON record."""
    return {
        'pid': 'rec1',
        'title': 'Test Record',
        'related_to': {'object': 'pid123'},
        'tags': ['tag1', 'tag2'],
    }


def write_pid_file(tmp_path: Path, filename: str, pids: list[str]) -> Path:
    """Write one PID per line to a temporary file."""
    path = tmp_path / filename
    if pids:
        path.write_text('\n'.join(pids) + '\n', encoding='utf-8')
    else:
        path.write_text('', encoding='utf-8')
    return path


def output_lines(result) -> list[str]:
    """Return non-empty output lines from a CliRunner result."""
    return [line for line in result.output.splitlines() if line.strip()]


# Basic tests for filter-links-pid command


def test_command_requires_at_least_one_link_option(runner):
    """At least one of --link or --link-from-file must be provided."""
    result = runner.invoke(cli, ['--api-url', 'http://test.api'])

    assert result.exit_code != 0
    assert 'At least one of --link or --link-from-file' in result.output


def test_single_link_filter_match(runner, sample_record):
    """Test filtering a record that matches the link criteria."""
    input_data = json.dumps(sample_record)

    result = runner.invoke(
        cli,
        [
            '--link',
            'related_to',
            'pid123',
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [input_data]


def test_single_link_filter_no_match(runner, sample_record):
    """Test filtering a record that doesn't match the link criteria."""
    input_data = json.dumps(sample_record)

    result = runner.invoke(
        cli,
        [
            '--link',
            'related_to',
            'pid999',
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == []


def test_multiple_records(runner):
    """Test filtering multiple JSON records from stdin."""
    record1 = {'pid': 'rec1', 'links_to': {'object': 'pid123'}}
    record2 = {'pid': 'rec2', 'links_to': {'object': 'pid456'}}
    input_data = f'{json.dumps(record1)}\n{json.dumps(record2)}\n'

    result = runner.invoke(
        cli,
        [
            '--link',
            'links_to',
            'pid123',
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [json.dumps(record1)]


def test_multiple_link_filters(runner):
    """Test filtering with multiple --link criteria (AND logic)."""
    record = {
        'pid': 'rec1',
        'related_to': {'object': 'pid123'},
        'linked_from': {'object': 'pid456'},
    }
    input_data = json.dumps(record)

    result = runner.invoke(
        cli,
        [
            '--link',
            'related_to',
            'pid123',
            '--link',
            'linked_from',
            'pid456',
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [input_data]

    record_missing_one_link = {
        'pid': 'rec1',
        'related_to': {'object': 'pid123'},
    }

    result = runner.invoke(
        cli,
        [
            '--link',
            'related_to',
            'pid123',
            '--link',
            'linked_from',
            'pid456',
            '--api-url',
            'http://test.api',
        ],
        input=json.dumps(record_missing_one_link),
    )

    assert result.exit_code == 0
    assert output_lines(result) == []


def test_list_property_matching(runner):
    """Test matching against list properties."""
    record = {'pid': 'rec1', 'tags': ['tag1', 'pid123', 'tag3']}
    input_data = json.dumps(record)

    result = runner.invoke(
        cli,
        [
            '--link',
            'tags',
            'pid123',
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [input_data]


def test_recursive_flag(runner, sample_record):
    """Test that recursive flag is accepted and direct match still works."""
    input_data = json.dumps(sample_record)

    result = runner.invoke(
        cli,
        [
            '--link',
            'related_to',
            'pid123',
            '--recursive',
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [input_data]


def test_collection_option(runner, sample_record):
    """Test specifying custom collection."""
    input_data = json.dumps(sample_record)

    result = runner.invoke(
        cli,
        [
            '--link',
            'related_to',
            'pid123',
            '--collection',
            'custom_collection',
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [input_data]


def test_missing_link_property(runner):
    """Test record without the specified link property."""
    record = {'pid': 'rec1', 'title': 'No links'}
    input_data = json.dumps(record)

    result = runner.invoke(
        cli,
        [
            '--link',
            'nonexistent_property',
            'pid123',
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == []


# Tests for --link-from-file behavior


def test_file_option_match_any_pid(runner, tmp_path, sample_record):
    """A record passes if it links to any PID listed in the file."""
    pid_file = write_pid_file(
        tmp_path,
        'pids.txt',
        ['pid111', 'pid123', 'pid222'],
    )
    input_data = json.dumps(sample_record)

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [input_data]


def test_file_option_no_match(runner, tmp_path):
    """A record fails if it links to none of the PIDs in the file."""
    pid_file = write_pid_file(
        tmp_path,
        'pids.txt',
        ['pid123', 'pid456'],
    )
    record = {'pid': 'rec1', 'related_to': {'object': 'pid999'}}
    input_data = json.dumps(record)

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == []


def test_file_only_is_sufficient(runner, tmp_path):
    """--link-from-file can be used without any --link option."""
    pid_file = write_pid_file(tmp_path, 'pids.txt', ['pid123'])
    record = {'pid': 'rec1', 'related_to': {'object': 'pid123'}}
    input_data = json.dumps(record)

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [input_data]


def test_file_option_filters_multiple_records(runner, tmp_path):
    """Only records linked to at least one PID in the file are emitted."""
    pid_file = write_pid_file(
        tmp_path,
        'pids.txt',
        ['pid123', 'pid456'],
    )

    record1 = {'pid': 'rec1', 'related_to': {'object': 'pid123'}}
    record2 = {'pid': 'rec2', 'related_to': {'object': 'pid999'}}
    record3 = {'pid': 'rec3', 'related_to': ['pid999', {'object': 'pid456'}]}

    input_data = (
        f'{json.dumps(record1)}\n{json.dumps(record2)}\n{json.dumps(record3)}\n'
    )

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [
        json.dumps(record1),
        json.dumps(record3),
    ]


def test_preserves_original_input_lines(runner, tmp_path):
    """Matching records should be emitted unchanged."""
    pid_file = write_pid_file(tmp_path, 'pids.txt', ['pid123'])
    input_text = '{"pid": "rec1", "related_to": {"object": "pid123"}}\n'

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=input_text,
    )

    assert result.exit_code == 0
    assert result.output == input_text


@pytest.mark.parametrize(
    ('property_value', 'matching_pid'),
    [
        ('pid123', 'pid123'),
        (['pid111', 'pid123'], 'pid123'),
        ([{'object': 'pid123'}], 'pid123'),
        (['pid999', {'object': 'pid123'}], 'pid123'),
    ],
)
def test_supports_documented_link_formats_from_file(
    runner,
    tmp_path,
    property_value,
    matching_pid,
):
    """File-based matching should accept the same link shapes as --link."""
    record = {'pid': 'rec1', 'links': property_value}
    pid_file = write_pid_file(
        tmp_path,
        'pids.txt',
        ['not-matching', matching_pid],
    )
    input_data = json.dumps(record)

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'links',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [input_data]


def test_file_pids_only_apply_to_declared_property(runner, tmp_path):
    """PIDs from a file must only be considered for the declared property."""
    pid_file = write_pid_file(tmp_path, 'pids.txt', ['pid123'])
    record = {'pid': 'rec1', 'related_to': {'object': 'pid123'}}
    input_data = json.dumps(record)

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'linked_from',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == []


def test_link_and_file_options_are_anded(runner, tmp_path):
    """--link and --link-from-file must both be satisfied."""
    pid_file = write_pid_file(tmp_path, 'pids.txt', ['pidB', 'pidC'])
    passing_record = {
        'pid': 'rec1',
        'exact': {'object': 'pidA'},
        'file_prop': {'object': 'pidC'},
    }
    failing_record = {
        'pid': 'rec1',
        'exact': {'object': 'pidA'},
        'file_prop': {'object': 'pidD'},
    }
    args = [
        '--link',
        'exact',
        'pidA',
        '--link-from-file',
        'file_prop',
        str(pid_file),
        '--api-url',
        'http://test.api',
    ]

    result = runner.invoke(cli, args, input=json.dumps(passing_record))
    assert result.exit_code == 0
    assert output_lines(result) == [json.dumps(passing_record)]

    result = runner.invoke(cli, args, input=json.dumps(failing_record))
    assert result.exit_code == 0
    assert output_lines(result) == []


def test_multiple_file_options_are_anded(runner, tmp_path):
    """Multiple --link-from-file options are ANDed together."""
    file1 = write_pid_file(tmp_path, 'one.txt', ['pid1', 'pid3'])
    file2 = write_pid_file(tmp_path, 'two.txt', ['pid2', 'pid4'])
    passing_record = {
        'pid': 'rec1',
        'prop1': {'object': 'pid1'},
        'prop2': {'object': 'pid2'},
    }
    failing_record = {
        'pid': 'rec2',
        'prop1': {'object': 'pid1'},
    }
    args = [
        '--link-from-file',
        'prop1',
        str(file1),
        '--link-from-file',
        'prop2',
        str(file2),
        '--api-url',
        'http://test.api',
    ]

    result = runner.invoke(cli, args, input=json.dumps(passing_record))
    assert result.exit_code == 0
    assert output_lines(result) == [json.dumps(passing_record)]

    result = runner.invoke(cli, args, input=json.dumps(failing_record))
    assert result.exit_code == 0
    assert output_lines(result) == []


def test_or_is_only_within_each_file(runner, tmp_path):
    """OR behavior must not leak across separate --link-from-file options."""
    file1 = write_pid_file(tmp_path, 'one.txt', ['pid1'])
    file2 = write_pid_file(tmp_path, 'two.txt', ['pid2'])
    passing_record = {'pid': 'rec1', 'prop': ['pid1', 'pid2']}
    failing_record = {'pid': 'rec2', 'prop': ['pid1']}
    args = [
        '--link-from-file',
        'prop',
        str(file1),
        '--link-from-file',
        'prop',
        str(file2),
        '--api-url',
        'http://test.api',
    ]

    result = runner.invoke(cli, args, input=json.dumps(passing_record))
    assert result.exit_code == 0
    assert output_lines(result) == [json.dumps(passing_record)]

    result = runner.invoke(cli, args, input=json.dumps(failing_record))
    assert result.exit_code == 0
    assert output_lines(result) == []


def test_exact_link_is_not_replaced_by_file_alternatives(runner, tmp_path):
    """An exact --link PID is still required even if the file has alternatives."""
    pid_file = write_pid_file(tmp_path, 'pids.txt', ['pidY'])
    passing_record = {'pid': 'rec1', 'prop': ['pidX', 'pidY']}
    failing_record = {'pid': 'rec2', 'prop': ['pidY']}
    args = [
        '--link',
        'prop',
        'pidX',
        '--link-from-file',
        'prop',
        str(pid_file),
        '--api-url',
        'http://test.api',
    ]

    result = runner.invoke(cli, args, input=json.dumps(passing_record))
    assert result.exit_code == 0
    assert output_lines(result) == [json.dumps(passing_record)]

    result = runner.invoke(cli, args, input=json.dumps(failing_record))
    assert result.exit_code == 0
    assert output_lines(result) == []


def test_empty_pid_file_matches_nothing(runner, tmp_path):
    """An empty PID file should cause every record to be filtered out."""
    pid_file = tmp_path / 'empty.txt'
    pid_file.write_text('', encoding='utf-8')
    record = {'pid': 'rec1', 'related_to': {'object': 'pid123'}}

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=json.dumps(record),
    )

    assert result.exit_code == 0
    assert output_lines(result) == []


def test_pid_file_with_only_blank_lines_matches_nothing(runner, tmp_path):
    """Blank lines should be ignored, so a blank-only file has no PIDs."""
    pid_file = tmp_path / 'pids.txt'
    pid_file.write_text('\n   \n\t\n', encoding='utf-8')
    record = {'pid': 'rec1', 'related_to': {'object': 'pid123'}}

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=json.dumps(record),
    )

    assert result.exit_code == 0
    assert output_lines(result) == []


def test_pid_file_lines_are_stripped(runner, tmp_path):
    """Surrounding whitespace around PIDs should be ignored."""
    pid_file = tmp_path / 'pids.txt'
    pid_file.write_text('pid1\n  pid2 \n\n  \n', encoding='utf-8')
    record = {'pid': 'rec1', 'related_to': {'object': 'pid2'}}
    input_data = json.dumps(record)

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [input_data]


def test_duplicate_pid_lines_are_allowed(runner, tmp_path):
    """Duplicate PIDs in a file should not change matching behavior."""
    pid_file = tmp_path / 'pids.txt'
    pid_file.write_text('pid123\npid123\n', encoding='utf-8')
    record = {'pid': 'rec1', 'related_to': {'object': 'pid123'}}
    input_data = json.dumps(record)

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [input_data]


def test_missing_pid_file_errors(runner, tmp_path, sample_record):
    """A missing PID file should produce a CLI error."""
    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(tmp_path / 'missing.txt'),
            '--api-url',
            'http://test.api',
        ],
        input=json.dumps(sample_record),
    )

    assert result.exit_code != 0
    assert 'error' in result.output.lower()
    assert 'exist' in result.output.lower() or 'missing' in result.output.lower()


def test_directory_as_pid_file_errors(runner, tmp_path, sample_record):
    """A directory should not be accepted as a PID file."""
    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(tmp_path),
            '--api-url',
            'http://test.api',
        ],
        input=json.dumps(sample_record),
    )

    assert result.exit_code != 0
    assert 'error' in result.output.lower()


# Tests for the PID-file parsing helper


def test_read_pids_returns_frozenset_of_stripped_pids(tmp_path):
    path = tmp_path / 'pids.txt'
    path.write_text('pid1\n  pid2  \n\npid3\n', encoding='utf-8')

    assert _read_pids(path) == frozenset({'pid1', 'pid2', 'pid3'})


def test_read_pids_empty_file(tmp_path):
    path = tmp_path / 'empty.txt'
    path.write_text('', encoding='utf-8')

    assert _read_pids(path) == frozenset()


def test_read_pids_accepts_string_path(tmp_path):
    path = tmp_path / 'pids.txt'
    path.write_text('pid1\n', encoding='utf-8')

    assert _read_pids(str(path)) == frozenset({'pid1'})


def test_read_pids_missing_file_raises(tmp_path):
    with pytest.raises(click.ClickException):
        _read_pids(tmp_path / 'missing.txt')


# Tests for --link-from-file with --recursive


def test_recursive_file_matches_indirect_link(runner, tmp_path, monkeypatch):
    pid_file = write_pid_file(tmp_path, 'pids.txt', ['target'])
    record = {'pid': 'rec1', 'related_to': {'object': 'intermediate'}}
    input_data = json.dumps(record)

    def fake_resolver(api_url, collections, pid, cache, token=None):  # noqa: ARG001
        if pid == 'intermediate':
            return {'related_to': {'object': 'target'}}
        return None

    monkeypatch.setattr(
        common_api,
        '_get_rec_from_any_collection',
        fake_resolver,
    )

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--recursive',
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [input_data]


def test_non_recursive_file_does_not_match_indirect_link(runner, tmp_path):
    pid_file = write_pid_file(tmp_path, 'pids.txt', ['target'])
    record = {'pid': 'rec1', 'related_to': {'object': 'intermediate'}}

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=json.dumps(record),
    )

    assert result.exit_code == 0
    assert output_lines(result) == []


def test_recursive_file_no_match_when_indirect_link_not_target(
    runner,
    tmp_path,
    monkeypatch,
):
    pid_file = write_pid_file(tmp_path, 'pids.txt', ['target'])
    record = {'pid': 'rec1', 'related_to': {'object': 'intermediate'}}

    def fake_resolver(api_url, collections, pid, cache, token=None):  # noqa: ARG001
        if pid == 'intermediate':
            return {'related_to': {'object': 'other'}}
        return None

    monkeypatch.setattr(
        common_api,
        '_get_rec_from_any_collection',
        fake_resolver,
    )

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--recursive',
            '--api-url',
            'http://test.api',
        ],
        input=json.dumps(record),
    )

    assert result.exit_code == 0
    assert output_lines(result) == []


def test_direct_file_match_does_not_call_resolver(
    runner,
    tmp_path,
    monkeypatch,
):
    """Direct matching against a PID file should not require resolution."""
    pid_file = write_pid_file(tmp_path, 'pids.txt', ['other', 'target'])
    record = {'pid': 'rec1', 'related_to': {'object': 'target'}}
    input_data = json.dumps(record)
    calls = []

    def fake_resolver(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(
        common_api,
        '_get_rec_from_any_collection',
        fake_resolver,
    )

    result = runner.invoke(
        cli,
        [
            '--link-from-file',
            'related_to',
            str(pid_file),
            '--api-url',
            'http://test.api',
        ],
        input=input_data,
    )

    assert result.exit_code == 0
    assert output_lines(result) == [input_data]
    assert calls == []
