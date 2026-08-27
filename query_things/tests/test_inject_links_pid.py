import json

import pytest

from query_things.inject_links_pid import _proc_record, cli
from query_things.tests import (
    jsonl_lines,
    make_record,
)

API_URL = 'https://api.example.test'


class FakeLinkQuery:
    def __init__(self) -> None:
        self.records: dict[str, list[tuple[dict, dict]]] = {}
        self.calls: list[dict] = []

    def __call__(
        self,
        api_url,
        collection,
        class_name,
        matching,
        token=None,
    ):
        self.calls.append(
            {
                'api_url': api_url,
                'collection': collection,
                'class_name': class_name,
                'matching': matching,
                'token': token,
            }
        )
        return self.records.get(collection, [])


@pytest.fixture
def link_query(monkeypatch: pytest.MonkeyPatch) -> FakeLinkQuery:
    fake = FakeLinkQuery()
    monkeypatch.setattr(
        'query_things.inject_links_pid.collection_read_records_of_class',
        fake,
    )
    return fake


@pytest.fixture
def process_record(link_query: FakeLinkQuery):  # noqa: ARG001
    def _process(
        record: dict,
        *,
        inject: str = 'people',
        collections: tuple[str, ...] = ('public',),
        link: tuple[str, ...] = ('projects',),
        class_name: str | None = None,
        token: str | None = None,
    ) -> dict:
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
    link_query,
):
    linker = make_record(
        'person:1',
        schema_type='Person',
        related='dataset:1',
    )
    link_query.records['public'] = [(linker, {})]

    record = process_record(
        make_record('dataset:1', title='Example dataset'),
        inject='injected_people',
        link=('related',),
        class_name='Person',
        token='secret-token',  # noqa: S106
    )

    assert record == {
        'pid': 'dataset:1',
        'title': 'Example dataset',
        'injected_people': [linker],
    }

    assert link_query.calls == [
        {
            'api_url': API_URL,
            'collection': 'public',
            'class_name': 'Person',
            'matching': 'dataset:1',
            'token': 'secret-token',
        }
    ]


def test_appends_linking_records_to_existing_list(process_record, link_query):
    linker = make_record(
        'project:1',
        name='Project One',
        datasets=['dataset:1'],
    )
    link_query.records['public'] = [(linker, {})]

    existing = [make_record('project:existing', name='Existing project')]

    record = process_record(
        make_record('dataset:1', projects=existing),
        inject='projects',
        link=('datasets',),
    )

    assert record['projects'] == [*existing, linker]


def test_converts_existing_scalar_to_list(process_record, link_query):
    linker = make_record(
        'person:1',
        name='New person',
        projects=['project:1'],
    )
    link_query.records['public'] = [(linker, {})]

    existing = make_record('person:existing', name='Existing person')

    record = process_record(
        make_record('project:1', people=existing),
        inject='people',
        link=('projects',),
    )

    assert record['people'] == [existing, linker]


def test_queries_each_configured_collection(process_record, link_query):
    link_query.records['public'] = []
    linker = make_record('person:private', projects=['project:1'])
    link_query.records['private'] = [(linker, {})]

    record = process_record(
        make_record('project:1'),
        inject='people',
        collections=('public', 'private'),
        link=('projects',),
        class_name='Person',
    )

    assert [call['collection'] for call in link_query.calls] == [
        'public',
        'private',
    ]
    assert record['people'] == [linker]


def test_multiple_link_properties_match_with_or_semantics(
    process_record,
    link_query,
):
    linker = make_record(
        'person:1',
        projects=['project:1'],
        datasets=['dataset:1'],
    )
    link_query.records['public'] = [(linker, {})]

    record = process_record(
        make_record('dataset:1'),
        inject='people',
        link=('projects', 'datasets'),
    )

    assert record['people'] == [linker]


def test_matches_scalar_and_object_link_values(process_record, link_query):
    scalar = make_record('person:scalar', related='dataset:1')
    object_link = make_record('person:object', related={'object': 'dataset:1'})
    link_query.records['public'] = [(scalar, {}), (object_link, {})]

    record = process_record(
        make_record('dataset:1'),
        inject='people',
        link=('related',),
    )

    assert [person['pid'] for person in record['people']] == [
        'person:scalar',
        'person:object',
    ]


def test_cli_wires_arguments_and_json_lines(runner, link_query):
    linker = make_record('person:1', related='dataset:1')
    link_query.records['public'] = [(linker, {})]

    result = runner.invoke(
        cli,
        [
            'people',
            '--link',
            'related',
            '--api-url',
            API_URL,
        ],
        input=jsonl_lines(make_record('dataset:1')),
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        'pid': 'dataset:1',
        'people': [linker],
    }
