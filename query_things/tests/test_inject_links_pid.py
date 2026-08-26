import json

import pytest
from click.testing import CliRunner

from query_things.inject_links_pid import _proc_record, cli


API_URL = 'https://example.test'


@pytest.fixture
def linker_query(monkeypatch):
    """Install a configurable mock for the Things client query."""
    records_by_collection = {}
    calls = []

    def fake_collection_read_records_of_class(
        api_url,
        collection,
        class_name,
        matching,
        token=None,
    ):
        assert api_url == API_URL

        calls.append(
            {
                'collection': collection,
                'class_name': class_name,
                'matching': matching,
                'token': token,
            }
        )

        return records_by_collection.get(collection, [])

    monkeypatch.setattr(
        'query_things.inject_links_pid.collection_read_records_of_class',
        fake_collection_read_records_of_class,
    )

    return records_by_collection, calls


@pytest.fixture
def process_record(linker_query):
    records_by_collection, _ = linker_query

    def _process(
        record,
        *,
        inject='links',
        collections=('public',),
        link=('related',),
        class_name=None,
        token=None,
    ):
        _proc_record(
            record,
            inject=inject,
            collections=collections,
            link=link,
            class_name=class_name,
            api_url=API_URL,
            token=token,
        )
        return record

    return _process


def test_injects_linking_records_into_missing_property(
    process_record,
    linker_query,
):
    records_by_collection, calls = linker_query
    records_by_collection['public'] = [
        (
            {
                'pid': 'person:1',
                'schema_type': 'Person',
                'related': 'dataset:1',
            },
            {},
        ),
    ]

    record = process_record(
        {
            'pid': 'dataset:1',
            'title': 'Example dataset',
        },
        inject='injected_people',
        link=('related',),
        class_name='Person',
        token='secret-token',
    )

    assert record == {
        'pid': 'dataset:1',
        'title': 'Example dataset',
        'injected_people': [
            {
                'pid': 'person:1',
                'schema_type': 'Person',
                'related': 'dataset:1',
            },
        ],
    }

    assert calls == [
        {
            'collection': 'public',
            'class_name': 'Person',
            'matching': 'dataset:1',
            'token': 'secret-token',
        }
    ]


def test_appends_linking_records_to_existing_list(
    process_record,
    linker_query,
):
    records_by_collection, _ = linker_query
    records_by_collection['public'] = [
        (
            {
                'pid': 'project:1',
                'name': 'Project One',
                'datasets': ['dataset:1'],
            },
            {},
        ),
    ]

    record = process_record(
        {
            'pid': 'dataset:1',
            'projects': [
                {
                    'pid': 'project:existing',
                    'name': 'Existing project',
                },
            ],
        },
        inject='projects',
        link=('datasets',),
    )

    assert record['projects'] == [
        {
            'pid': 'project:existing',
            'name': 'Existing project',
        },
        {
            'pid': 'project:1',
            'name': 'Project One',
            'datasets': ['dataset:1'],
        },
    ]


def test_converts_existing_scalar_to_list(
    process_record,
    linker_query,
):
    records_by_collection, _ = linker_query
    records_by_collection['public'] = [
        (
            {
                'pid': 'person:1',
                'name': 'New person',
                'projects': ['project:1'],
            },
            {},
        ),
    ]

    record = process_record(
        {
            'pid': 'project:1',
            'people': {
                'pid': 'person:existing',
                'name': 'Existing person',
            },
        },
        inject='people',
        link=('projects',),
    )

    assert record['people'] == [
        {
            'pid': 'person:existing',
            'name': 'Existing person',
        },
        {
            'pid': 'person:1',
            'name': 'New person',
            'projects': ['project:1'],
        },
    ]


def test_queries_each_configured_collection(
    process_record,
    linker_query,
):
    records_by_collection, calls = linker_query
    records_by_collection['private'] = [
        (
            {
                'pid': 'person:private',
                'projects': ['project:1'],
            },
            {},
        ),
    ]

    record = process_record(
        {'pid': 'project:1'},
        inject='people',
        collections=('public', 'private'),
        link=('projects',),
        class_name='Person',
    )

    assert [call['collection'] for call in calls] == [
        'public',
        'private',
    ]
    assert record['people'] == [
        {
            'pid': 'person:private',
            'projects': ['project:1'],
        },
    ]


def test_multiple_link_properties_match_with_or_semantics(
    process_record,
    linker_query,
):
    records_by_collection, _ = linker_query
    records_by_collection['public'] = [
        (
            {
                'pid': 'person:1',
                'projects': ['project:1'],
                'datasets': ['dataset:1'],
            },
            {},
        ),
    ]

    record = process_record(
        {'pid': 'dataset:1'},
        inject='people',
        link=('projects', 'datasets'),
    )

    assert record['people'] == [
        {
            'pid': 'person:1',
            'projects': ['project:1'],
            'datasets': ['dataset:1'],
        }
    ]


def test_matches_scalar_and_object_link_values(
    process_record,
    linker_query,
):
    records_by_collection, _ = linker_query
    records_by_collection['public'] = [
        (
            {
                'pid': 'person:scalar',
                'related': 'dataset:1',
            },
            {},
        ),
        (
            {
                'pid': 'person:object',
                'related': {'object': 'dataset:1'},
            },
            {},
        ),
    ]

    record = process_record(
        {'pid': 'dataset:1'},
        inject='people',
        link=('related',),
    )

    assert [person['pid'] for person in record['people']] == [
        'person:scalar',
        'person:object',
    ]


def test_cli_wires_arguments_and_json_lines(linker_query):
    records_by_collection, _ = linker_query
    records_by_collection['public'] = [
        (
            {
                'pid': 'person:1',
                'related': 'dataset:1',
            },
            {},
        ),
    ]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            'people',
            '--link',
            'related',
            '--api-url',
            API_URL,
        ],
        input=json.dumps({'pid': 'dataset:1'}) + '\n',
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        'pid': 'dataset:1',
        'people': [
            {
                'pid': 'person:1',
                'related': 'dataset:1',
            },
        ],
    }
