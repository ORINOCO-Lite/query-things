import json

import click
import pytest

from query_things.list import cli


def emitted_json(capsys):
    """Return JSON objects emitted by the command, in order."""
    output = capsys.readouterr().out
    return [json.loads(line) for line in output.splitlines()]


def test_lists_all_non_null_records(capsys):
    record_cache = {
        'pid-1': {
            'pid': 'pid-1',
            'schema_type': 'Person',
            'name': 'Alice',
        },
        'pid-2': None,
        'pid-3': {
            'pid': 'pid-3',
            'schema_type': 'Company',
            'name': 'Example Inc.',
        },
    }

    cli.callback(record_cache=record_cache, pid=(), cls=())

    assert emitted_json(capsys) == [
        {
            'pid': 'pid-1',
            'schema_type': 'Person',
            'name': 'Alice',
        },
        {
            'pid': 'pid-3',
            'schema_type': 'Company',
            'name': 'Example Inc.',
        },
    ]


def test_empty_cache_emits_nothing(capsys):
    cli.callback(record_cache={}, pid=(), cls=())

    assert capsys.readouterr().out == ''


def test_skips_none_records_when_filtering_by_class(capsys):
    record_cache = {
        'pid-1': None,
        'pid-2': {
            'pid': 'pid-2',
            'schema_type': 'Person',
        },
    }

    cli.callback(record_cache=record_cache, pid=(), cls=('Person',))

    assert emitted_json(capsys) == [
        {
            'pid': 'pid-2',
            'schema_type': 'Person',
        }
    ]


def test_filters_records_by_single_class(capsys):
    record_cache = {
        'pid-1': {
            'pid': 'pid-1',
            'schema_type': 'Person',
        },
        'pid-2': {
            'pid': 'pid-2',
            'schema_type': 'Company',
        },
    }

    cli.callback(record_cache=record_cache, pid=(), cls=('Person',))

    assert emitted_json(capsys) == [
        {
            'pid': 'pid-1',
            'schema_type': 'Person',
        }
    ]


def test_filters_records_by_multiple_classes(capsys):
    record_cache = {
        'pid-1': {
            'pid': 'pid-1',
            'schema_type': 'Person',
        },
        'pid-2': {
            'pid': 'pid-2',
            'schema_type': 'Company',
        },
        'pid-3': {
            'pid': 'pid-3',
            'schema_type': 'Animal',
        },
    }

    cli.callback(
        record_cache=record_cache,
        pid=(),
        cls=('Person', 'Company'),
    )

    assert emitted_json(capsys) == [
        {
            'pid': 'pid-1',
            'schema_type': 'Person',
        },
        {
            'pid': 'pid-2',
            'schema_type': 'Company',
        },
    ]


def test_records_without_schema_type_are_excluded_when_class_filter_is_used(
    capsys,
):
    record_cache = {
        'pid-1': {
            'pid': 'pid-1',
            'name': 'No schema type',
        },
        'pid-2': {
            'pid': 'pid-2',
            'schema_type': 'Person',
        },
    }

    cli.callback(record_cache=record_cache, pid=(), cls=('Person',))

    assert emitted_json(capsys) == [
        {
            'pid': 'pid-2',
            'schema_type': 'Person',
        }
    ]


def test_lists_records_by_pid_in_requested_order(capsys):
    record_cache = {
        'pid-1': {
            'pid': 'pid-1',
            'schema_type': 'Person',
        },
        'pid-2': {
            'pid': 'pid-2',
            'schema_type': 'Company',
        },
    }

    cli.callback(
        record_cache=record_cache,
        pid=('pid-2', 'pid-1'),
        cls=(),
    )

    assert emitted_json(capsys) == [
        {
            'pid': 'pid-2',
            'schema_type': 'Company',
        },
        {
            'pid': 'pid-1',
            'schema_type': 'Person',
        },
    ]


def test_missing_pid_raises_value_error():
    record_cache = {
        'pid-1': {
            'pid': 'pid-1',
            'schema_type': 'Person',
        },
    }

    with pytest.raises(
        click.ClickException,
        match=r'missing',
    ):
        cli.callback(
            record_cache=record_cache,
            pid=('missing',),
            cls=(),
        )


def test_missing_pid_error_stops_processing(capsys):
    record_cache = {
        'pid-1': {
            'pid': 'pid-1',
            'schema_type': 'Person',
        },
    }

    with pytest.raises(click.ClickException):
        cli.callback(
            record_cache=record_cache,
            pid=('pid-1', 'missing'),
            cls=(),
        )
    # no partial report
    assert emitted_json(capsys) == []


def test_pid_filter_takes_precedence_over_class_filter(capsys):
    record_cache = {
        'pid-1': {
            'pid': 'pid-1',
            'schema_type': 'Person',
        },
        'pid-2': {
            'pid': 'pid-2',
            'schema_type': 'Company',
        },
    }

    cli.callback(
        record_cache=record_cache,
        pid=('pid-2',),
        cls=('Person',),
    )

    assert emitted_json(capsys) == [
        {
            'pid': 'pid-2',
            'schema_type': 'Company',
        }
    ]
