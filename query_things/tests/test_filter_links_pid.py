from pathlib import Path

import click
import pytest

from query_things.filter_links_pid import _read_pids, cli
from query_things.tests import (
    jsonl_lines,
    make_record,
    output_records,
)

API_URL = 'https://api.example.test'


def build_filter_args(
    *links: tuple[str, str],
    link_files: list[tuple[str, Path]] | None = None,
    recursive: bool = False,
    collections: tuple[str, ...] = (),
    api_url: str = API_URL,
    token: str | None = None,
) -> list[str]:
    args: list[str] = []

    for prop, pid in links:
        args.extend(['--link', prop, pid])

    for prop, path in link_files or ():
        args.extend(['--link-from-file', prop, str(path)])

    if recursive:
        args.append('--recursive')

    for collection in collections:
        args.extend(['--collection', collection])

    args.extend(['--api-url', api_url])

    if token is not None:
        args.extend(['--token', token])

    return args


def make_resolver(records_by_pid: dict[str, dict], calls: list[dict] | None = None):
    """Create a fake `_get_rec_from_any_collection` implementation."""

    def fake_resolver(**kwargs):
        if calls is not None:
            calls.append(kwargs)
        return records_by_pid.get(kwargs.get('pid'))

    return fake_resolver


@pytest.fixture
def invoke_filter(runner, monkeypatch: pytest.MonkeyPatch):
    """Invoke `filter-links-pid` with a mocked record resolver."""

    def _invoke(
        records: dict | list[dict | str] | str,
        *links: tuple[str, str],
        link_files: list[tuple[str, Path]] | None = None,
        recursive: bool = False,
        collections: tuple[str, ...] = (),
        resolver=None,
        api_url: str = API_URL,
        token: str | None = None,
    ):
        if resolver is None:

            def resolver(**kwargs):  # noqa: ARG001
                return None

        monkeypatch.setattr(
            'query_things.common.api._get_rec_from_any_collection',
            resolver,
        )

        if isinstance(records, (dict, str)):
            records = [records]

        args = build_filter_args(
            *links,
            link_files=link_files,
            recursive=recursive,
            collections=collections,
            api_url=api_url,
            token=token,
        )

        return runner.invoke(cli, args, input=jsonl_lines(*records))

    return _invoke


def test_requires_at_least_one_link_option(runner):
    result = runner.invoke(
        cli,
        build_filter_args(),
        input=jsonl_lines(make_record('rec1')),
    )

    assert result.exit_code != 0
    assert 'At least one of --link or --link-from-file' in result.output


match_record = make_record('rec1', related_to={'object': 'pid123'})
list_record = make_record('rec1', tags=['tag1', 'pid123', 'tag3'])
empty_record = make_record('rec1', title='No links')


@pytest.mark.parametrize(
    ('record', 'prop', 'target', 'expected'),
    [
        (match_record, 'related_to', 'pid123', [match_record]),
        (match_record, 'related_to', 'pid999', []),
        (list_record, 'tags', 'pid123', [list_record]),
        (empty_record, 'nonexistent', 'pid123', []),
    ],
)
def test_single_link_filter(invoke_filter, record, prop, target, expected):
    result = invoke_filter([record], (prop, target))

    assert result.exit_code == 0
    assert output_records(result.output) == expected


def test_multiple_records(invoke_filter):
    record1 = make_record('rec1', links_to={'object': 'pid123'})
    record2 = make_record('rec2', links_to={'object': 'pid456'})

    result = invoke_filter([record1, record2], ('links_to', 'pid123'))

    assert result.exit_code == 0
    assert output_records(result.output) == [record1]


def test_multiple_link_options_are_anded(invoke_filter):
    passing = make_record(
        'rec1',
        related_to={'object': 'pid123'},
        linked_from={'object': 'pid456'},
    )
    failing = make_record('rec1', related_to={'object': 'pid123'})

    links = [
        ('related_to', 'pid123'),
        ('linked_from', 'pid456'),
    ]

    assert output_records(invoke_filter([passing], *links).output) == [passing]
    assert output_records(invoke_filter([failing], *links).output) == []


def test_link_from_file_matches_any_pid(invoke_filter, write_pid_file):
    pid_file = write_pid_file('pids.txt', pids=['pid111', 'pid123', 'pid222'])
    record = make_record('rec1', related_to={'object': 'pid123'})

    result = invoke_filter([record], link_files=[('related_to', pid_file)])

    assert result.exit_code == 0
    assert output_records(result.output) == [record]


def test_link_from_file_no_match(invoke_filter, write_pid_file):
    pid_file = write_pid_file('pids.txt', pids=['pid123', 'pid456'])
    record = make_record('rec1', related_to={'object': 'pid999'})

    result = invoke_filter([record], link_files=[('related_to', pid_file)])

    assert result.exit_code == 0
    assert output_records(result.output) == []


def test_link_from_file_filters_multiple_records(invoke_filter, write_pid_file):
    pid_file = write_pid_file('pids.txt', pids=['pid123', 'pid456'])

    record1 = make_record('rec1', related_to={'object': 'pid123'})
    record2 = make_record('rec2', related_to={'object': 'pid999'})
    record3 = make_record('rec3', related_to=['pid999', {'object': 'pid456'}])

    result = invoke_filter(
        [record1, record2, record3],
        link_files=[('related_to', pid_file)],
    )

    assert result.exit_code == 0
    assert output_records(result.output) == [record1, record3]


def test_link_from_file_preserves_original_input_line(
    invoke_filter,
    write_pid_file,
):
    pid_file = write_pid_file('pids.txt', pids=['pid123'])
    raw_line = '{"pid": "rec1", "related_to": {"object": "pid123"}}'
    input_text = jsonl_lines(raw_line)

    result = invoke_filter([raw_line], link_files=[('related_to', pid_file)])

    assert result.exit_code == 0
    assert result.output == input_text


@pytest.mark.parametrize(
    ('value', 'target_pid'),
    [
        ('pid123', 'pid123'),
        (['pid111', 'pid123'], 'pid123'),
        ([{'object': 'pid123'}], 'pid123'),
        (['pid999', {'object': 'pid123'}], 'pid123'),
    ],
)
def test_link_from_file_supports_documented_link_shapes(
    invoke_filter,
    write_pid_file,
    value,
    target_pid,
):
    record = make_record('rec1', links=value)
    pid_file = write_pid_file('pids.txt', pids=['not-matching', target_pid])

    result = invoke_filter([record], link_files=[('links', pid_file)])

    assert result.exit_code == 0
    assert output_records(result.output) == [record]


def test_link_from_file_pids_only_apply_to_declared_property(
    invoke_filter,
    write_pid_file,
):
    pid_file = write_pid_file('pids.txt', pids=['pid123'])
    record = make_record('rec1', related_to={'object': 'pid123'})

    result = invoke_filter([record], link_files=[('linked_from', pid_file)])

    assert result.exit_code == 0
    assert result.output == ''


def test_link_and_file_options_are_anded(invoke_filter, write_pid_file):
    pid_file = write_pid_file('pids.txt', pids=['pidB', 'pidC'])

    passing = make_record(
        'rec1',
        exact={'object': 'pidA'},
        file_prop={'object': 'pidC'},
    )
    failing = make_record(
        'rec1',
        exact={'object': 'pidA'},
        file_prop={'object': 'pidD'},
    )

    assert output_records(
        invoke_filter(
            [passing],
            ('exact', 'pidA'),
            link_files=[('file_prop', pid_file)],
        ).output
    ) == [passing]

    assert (
        output_records(
            invoke_filter(
                [failing],
                ('exact', 'pidA'),
                link_files=[('file_prop', pid_file)],
            ).output
        )
        == []
    )


def test_multiple_file_options_are_anded(invoke_filter, write_pid_file):
    file1 = write_pid_file('one.txt', pids=['pid1', 'pid3'])
    file2 = write_pid_file('two.txt', pids=['pid2', 'pid4'])

    passing = make_record(
        'rec1',
        prop1={'object': 'pid1'},
        prop2={'object': 'pid2'},
    )
    failing = make_record('rec2', prop1={'object': 'pid1'})

    assert output_records(
        invoke_filter(
            [passing],
            link_files=[('prop1', file1), ('prop2', file2)],
        ).output
    ) == [passing]

    assert (
        output_records(
            invoke_filter(
                [failing],
                link_files=[('prop1', file1), ('prop2', file2)],
            ).output
        )
        == []
    )


def test_or_is_only_within_each_file(invoke_filter, write_pid_file):
    file1 = write_pid_file('one.txt', pids=['pid1'])
    file2 = write_pid_file('two.txt', pids=['pid2'])

    passing = make_record('rec1', prop=['pid1', 'pid2'])
    failing = make_record('rec2', prop=['pid1'])

    assert output_records(
        invoke_filter(
            [passing],
            link_files=[('prop', file1), ('prop', file2)],
        ).output
    ) == [passing]

    assert (
        output_records(
            invoke_filter(
                [failing],
                link_files=[('prop', file1), ('prop', file2)],
            ).output
        )
        == []
    )


def test_exact_link_is_not_replaced_by_file_alternatives(
    invoke_filter,
    write_pid_file,
):
    pid_file = write_pid_file('pids.txt', pids=['pidY'])

    passing = make_record('rec1', prop=['pidX', 'pidY'])
    failing = make_record('rec2', prop=['pidY'])

    assert output_records(
        invoke_filter(
            [passing],
            ('prop', 'pidX'),
            link_files=[('prop', pid_file)],
        ).output
    ) == [passing]

    assert (
        output_records(
            invoke_filter(
                [failing],
                ('prop', 'pidX'),
                link_files=[('prop', pid_file)],
            ).output
        )
        == []
    )


@pytest.mark.parametrize('content', ['', '\n   \n\t\n'])
def test_blank_pid_file_matches_nothing(
    invoke_filter,
    write_pid_file,
    content,
):
    pid_file = write_pid_file('pids.txt', content=content)
    record = make_record('rec1', related_to={'object': 'pid123'})

    result = invoke_filter([record], link_files=[('related_to', pid_file)])

    assert result.exit_code == 0
    assert result.output == ''


def test_pid_file_lines_are_stripped_and_duplicates_are_ignored(
    invoke_filter,
    write_pid_file,
):
    pid_file = write_pid_file('pids.txt', content='pid1\n  pid2 \n\n  \npid2\n')
    record = make_record('rec1', related_to={'object': 'pid2'})

    result = invoke_filter([record], link_files=[('related_to', pid_file)])

    assert result.exit_code == 0
    assert output_records(result.output) == [record]


def test_missing_pid_file_errors(runner, tmp_path):
    args = build_filter_args(
        link_files=[('related_to', tmp_path / 'missing.txt')],
    )
    result = runner.invoke(cli, args, input=jsonl_lines(make_record('rec1')))

    assert result.exit_code != 0
    lowered = result.output.lower()
    assert 'exist' in lowered or 'missing' in lowered


def test_directory_as_pid_file_errors(runner, tmp_path):
    args = build_filter_args(link_files=[('related_to', tmp_path)])
    result = runner.invoke(cli, args, input=jsonl_lines(make_record('rec1')))

    assert result.exit_code != 0
    assert 'error' in result.output.lower()


@pytest.mark.parametrize(
    ('content', 'expected'),
    [
        ('pid1\n  pid2  \n\npid3\n', frozenset({'pid1', 'pid2', 'pid3'})),
        ('', frozenset()),
        ('\n   \n\t\n', frozenset()),
        ('pid1\npid1\n', frozenset({'pid1'})),
    ],
)
def test_read_pids(tmp_path, content, expected):
    path = tmp_path / 'pids.txt'
    path.write_text(content, encoding='utf-8')

    assert _read_pids(path) == expected


def test_read_pids_accepts_string_path(tmp_path):
    path = tmp_path / 'pids.txt'
    path.write_text('pid1\n', encoding='utf-8')

    assert _read_pids(str(path)) == frozenset({'pid1'})


def test_read_pids_missing_file_raises(tmp_path):
    with pytest.raises(click.ClickException):
        _read_pids(tmp_path / 'missing.txt')


def test_recursive_link_matches_indirect_link(invoke_filter):
    calls = []
    resolver = make_resolver(
        {
            'intermediate': make_record(
                'intermediate',
                related_to={'object': 'target'},
            )
        },
        calls=calls,
    )
    record = make_record('rec1', related_to={'object': 'intermediate'})

    result = invoke_filter(
        [record],
        ('related_to', 'target'),
        recursive=True,
        resolver=resolver,
    )

    assert result.exit_code == 0
    assert output_records(result.output) == [record]
    assert [call['pid'] for call in calls] == ['intermediate']


def test_non_recursive_link_does_not_match_indirect_link(invoke_filter):
    record = make_record('rec1', related_to={'object': 'intermediate'})

    result = invoke_filter([record], ('related_to', 'target'))

    assert result.exit_code == 0
    assert output_records(result.output) == []


def test_recursive_link_no_match_when_indirect_link_points_elsewhere(
    invoke_filter,
):
    resolver = make_resolver(
        {
            'intermediate': make_record(
                'intermediate',
                related_to={'object': 'other'},
            )
        }
    )
    record = make_record('rec1', related_to={'object': 'intermediate'})

    result = invoke_filter(
        [record],
        ('related_to', 'target'),
        recursive=True,
        resolver=resolver,
    )

    assert result.exit_code == 0
    assert output_records(result.output) == []


def test_direct_link_does_not_call_resolver(invoke_filter):
    calls = []
    resolver = make_resolver({}, calls=calls)
    record = make_record('rec1', related_to={'object': 'target'})

    result = invoke_filter([record], ('related_to', 'target'), resolver=resolver)

    assert result.exit_code == 0
    assert output_records(result.output) == [record]
    assert calls == []


indirect_match = {
    'intermediate': make_record(
        'intermediate',
        related_to={'object': 'target'},
    )
}
indirect_no_match = {
    'intermediate': make_record(
        'intermediate',
        related_to={'object': 'other'},
    )
}


@pytest.mark.parametrize(
    ('resolver_records', 'recursive', 'should_match'),
    [
        (indirect_match, True, True),
        (indirect_no_match, True, False),
        (indirect_match, False, False),
    ],
)
def test_link_from_file_recursive(
    invoke_filter,
    write_pid_file,
    resolver_records,
    recursive,
    should_match,
):
    pid_file = write_pid_file('pids.txt', pids=['target'])
    record = make_record('rec1', related_to={'object': 'intermediate'})

    result = invoke_filter(
        [record],
        link_files=[('related_to', pid_file)],
        recursive=recursive,
        resolver=make_resolver(resolver_records),
    )

    assert result.exit_code == 0
    assert output_records(result.output) == ([record] if should_match else [])


def test_direct_file_match_does_not_call_resolver(
    invoke_filter,
    write_pid_file,
):
    calls = []
    resolver = make_resolver({}, calls=calls)
    pid_file = write_pid_file('pids.txt', pids=['other', 'target'])
    record = make_record('rec1', related_to={'object': 'target'})

    result = invoke_filter(
        [record],
        link_files=[('related_to', pid_file)],
        resolver=resolver,
    )

    assert result.exit_code == 0
    assert output_records(result.output) == [record]
    assert calls == []


def test_collection_and_token_options_are_passed_to_resolver(invoke_filter):
    calls = []
    resolver = make_resolver(
        {
            'intermediate': make_record(
                'intermediate',
                related_to={'object': 'target'},
            )
        },
        calls=calls,
    )
    record = make_record('rec1', related_to={'object': 'intermediate'})

    result = invoke_filter(
        [record],
        ('related_to', 'target'),
        recursive=True,
        collections=('custom_collection',),
        token='secret',  # noqa: S106
        resolver=resolver,
    )

    assert result.exit_code == 0
    assert [call['collections'] for call in calls] == [('custom_collection',)]
    assert calls[0]['token'] == 'secret'  # noqa: S105
