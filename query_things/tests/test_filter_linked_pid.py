import io
import json
from unittest.mock import Mock

import pytest

import query_things.filter_linked_pid as filter_linked_pid


def run_filter(
    monkeypatch,
    capsys,
    *,
    reference,
    input_records,
    collection='people',
    pid='project-1',
    property_name='related_people',
    api_url='https://example.test',
    token='test-token',
):
    """Run the Click callback with mocked API access and stdin."""
    collection_read_record = Mock(return_value=reference)

    monkeypatch.setattr(
        filter_linked_pid,
        'collection_read_record_with_pid',
        collection_read_record,
    )
    monkeypatch.setattr(
        'sys.stdin',
        io.StringIO(''.join(json.dumps(record) + '\n' for record in input_records)),
    )

    filter_linked_pid.cli.callback(
        collection=collection,
        pid=pid,
        property=property_name,
        api_url=api_url,
        token=token,
    )

    return collection_read_record, capsys.readouterr()


def test_fetches_reference_record_with_expected_arguments(
    monkeypatch,
    capsys,
):
    reference = {
        'related_people': ['person-1'],
    }

    api_call, result = run_filter(
        monkeypatch,
        capsys,
        reference=reference,
        input_records=[],
        collection='people',
        pid='project-1',
        property_name='related_people',
        api_url='https://api.example.test',
        token='secret-token',
    )

    api_call.assert_called_once_with(
        service_url='https://api.example.test',
        collection='people',
        pid='project-1',
        token='secret-token',
    )
    assert result.out == ''
    assert result.err == ''


def test_filters_records_linked_by_scalar_reference_value(
    monkeypatch,
    capsys,
):
    reference = {
        'related_people': 'person-1',
    }
    input_records = [
        {'pid': 'person-1', 'name': 'Alice'},
        {'pid': 'person-2', 'name': 'Bob'},
    ]

    _, result = run_filter(
        monkeypatch,
        capsys,
        reference=reference,
        input_records=input_records,
    )

    assert result.out == json.dumps(input_records[0]) + '\n'
    assert result.err == ''


def test_filters_records_linked_by_list_of_values(
    monkeypatch,
    capsys,
):
    reference = {
        'related_people': ['person-1', 'person-3'],
    }
    input_records = [
        {'pid': 'person-1'},
        {'pid': 'person-2'},
        {'pid': 'person-3'},
    ]

    _, result = run_filter(
        monkeypatch,
        capsys,
        reference=reference,
        input_records=input_records,
    )

    expected_output = (
        json.dumps(input_records[0]) + '\n' + json.dumps(input_records[2]) + '\n'
    )
    assert result.out == expected_output


def test_filters_records_linked_by_association_objects(
    monkeypatch,
    capsys,
):
    reference = {
        'related_people': [
            {'object': 'person-1', 'label': 'author'},
            {'object': 'person-3', 'label': 'editor'},
        ],
    }
    input_records = [
        {'pid': 'person-1', 'name': 'Alice'},
        {'pid': 'person-2', 'name': 'Bob'},
        {'pid': 'person-3', 'name': 'Carol'},
    ]

    _, result = run_filter(
        monkeypatch,
        capsys,
        reference=reference,
        input_records=input_records,
    )

    expected_output = (
        json.dumps(input_records[0]) + '\n' + json.dumps(input_records[2]) + '\n'
    )
    assert result.out == expected_output


@pytest.mark.parametrize(
    ('reference_property', 'matching_pid'),
    [
        ('person-1', 'person-1'),
        (['person-1', 'person-2'], 'person-2'),
        ([{'object': 'person-1'}], 'person-1'),
        (
            ['person-1', {'object': 'person-2'}],
            'person-2',
        ),
    ],
)
def test_supports_all_documented_link_formats(
    monkeypatch,
    capsys,
    reference_property,
    matching_pid,
):
    reference = {
        'links': reference_property,
    }
    input_records = [
        {'pid': matching_pid},
        {'pid': 'unrelated'},
    ]

    _, result = run_filter(
        monkeypatch,
        capsys,
        reference=reference,
        input_records=input_records,
        property_name='links',
    )

    assert result.out == json.dumps(input_records[0]) + '\n'


def test_does_not_emit_unlinked_records(monkeypatch, capsys):
    reference = {
        'related_people': ['person-1'],
    }
    input_records = [
        {'pid': 'person-2'},
        {'pid': 'person-3'},
    ]

    _, result = run_filter(
        monkeypatch,
        capsys,
        reference=reference,
        input_records=input_records,
    )

    assert result.out == ''


def test_preserves_original_input_lines(monkeypatch, capsys):
    reference = {
        'related_people': ['person-1'],
    }
    input_text = '{"pid": "person-1", "value": 1}\n'

    collection_read_record = Mock(return_value=reference)
    monkeypatch.setattr(
        filter_linked_pid,
        'collection_read_record_with_pid',
        collection_read_record,
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(input_text))

    filter_linked_pid.cli.callback(
        collection='people',
        pid='project-1',
        property='related_people',
        api_url='https://example.test',
        token=None,
    )

    result = capsys.readouterr()

    assert result.out == input_text
    collection_read_record.assert_called_once_with(
        service_url='https://example.test',
        collection='people',
        pid='project-1',
        token=None,
    )
