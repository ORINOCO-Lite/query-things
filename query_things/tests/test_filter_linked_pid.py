from unittest.mock import Mock

import pytest

from query_things.cli.filter_linked_pid import cli
from query_things.tests import (
    jsonl_lines,
    make_record,
    output_records,
)


@pytest.fixture
def reference_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock()
    monkeypatch.setattr(
        'query_things.filter_linked_pid.collection_read_record_with_pid',
        mock,
    )
    return mock


@pytest.mark.parametrize(
    ('reference_value', 'matching_record'),
    [
        ('person-1', make_record('person-1')),
        (['person-1', 'person-2'], make_record('person-2')),
        ([{'object': 'person-1'}], make_record('person-1')),
        (['person-1', {'object': 'person-2'}], make_record('person-2')),
    ],
)
def test_filter_linked_pid_matches_all_documented_link_shapes(
    run_callback,
    reference_mock,
    reference_value,
    matching_record,
):
    reference_mock.return_value = make_record('project-1', links=reference_value)
    records = [matching_record, make_record('unrelated')]

    result = run_callback(
        cli.callback,
        input_text=jsonl_lines(*records),
        collection='people',
        pid='project-1',
        property='links',
        api_url='https://api.example.test',
        token='secret-token',  # noqa: S106
    )

    reference_mock.assert_called_once_with(
        service_url='https://api.example.test',
        collection='people',
        pid='project-1',
        token='secret-token',  # noqa: S106
    )
    assert output_records(result.out) == [matching_record]


def test_filter_linked_pid_emits_nothing_when_no_record_is_linked(
    run_callback,
    reference_mock,
):
    reference_mock.return_value = make_record(
        'project-1',
        related_people=['person-1'],
    )

    result = run_callback(
        cli.callback,
        input_text=jsonl_lines(
            make_record('person-2'),
            make_record('person-3'),
        ),
        collection='people',
        pid='project-1',
        property='related_people',
        api_url='https://api.example.test',
        token='secret-token',  # noqa: S106
    )

    assert result.out == ''
    assert result.err == ''


def test_filter_linked_pid_preserves_original_input_line(
    run_callback,
    reference_mock,
):
    reference_mock.return_value = {'related_people': ['person-1']}
    input_text = jsonl_lines('{"pid": "person-1", "value": 1}')

    result = run_callback(
        cli.callback,
        input_text=input_text,
        collection='people',
        pid='project-1',
        property='related_people',
        api_url='https://example.test',
        token=None,
    )

    assert result.out == input_text
    reference_mock.assert_called_once_with(
        service_url='https://example.test',
        collection='people',
        pid='project-1',
        token=None,
    )
