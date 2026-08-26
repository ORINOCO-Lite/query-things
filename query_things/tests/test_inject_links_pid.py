import json

import pytest
from click.testing import CliRunner

from query_things.inject_links_pid import cli


API_URL = "https://example.test"


@pytest.fixture
def invoke():
    runner = CliRunner()

    def _invoke(args, record):
        return runner.invoke(
            cli,
            [
                *args,
                "--api-url",
                API_URL,
            ],
            input=json.dumps(record) + "\n",
        )

    return _invoke


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

        calls.append({
            "collection": collection,
            "class_name": class_name,
            "matching": matching,
            "token": token,
        })

        return records_by_collection.get(collection, [])

    monkeypatch.setattr(
        "query_things.inject_links_pid"
        ".collection_read_records_of_class",
        fake_collection_read_records_of_class,
    )

    return records_by_collection, calls


def json_lines(result):
    assert result.exit_code == 0, result.output

    return [
        json.loads(line)
        for line in result.output.splitlines()
        if line.strip()
    ]


def test_injects_linking_records_into_missing_property(
    invoke,
    linker_query,
):
    records_by_collection, calls = linker_query
    records_by_collection["public"] = [
        (
            {
                "pid": "person:1",
                "schema_type": "Person",
                "related": "dataset:1",
            },
            {},
        ),
    ]

    result = invoke(
        [
            "injected_people",
            "--link",
            "related",
            "--class",
            "Person",
            "--token",
            "secret-token",
        ],
        {
            "pid": "dataset:1",
            "title": "Example dataset",
        },
    )

    records = json_lines(result)

    assert records == [{
        "pid": "dataset:1",
        "title": "Example dataset",
        "injected_people": [
            {
                "pid": "person:1",
                "schema_type": "Person",
                "related": "dataset:1",
            },
        ],
    }]

    assert calls == [{
        "collection": "public",
        "class_name": "Person",
        "matching": "dataset:1",
        "token": "secret-token",
    }]


def test_appends_linking_records_to_existing_list(
    invoke,
    linker_query,
):
    records_by_collection, _ = linker_query
    records_by_collection["public"] = [
        (
            {
                "pid": "project:1",
                "name": "Project One",
                "datasets": ["dataset:1"],
            },
            {},
        ),
    ]

    result = invoke(
        [
            "projects",
            "--link",
            "datasets",
        ],
        {
            "pid": "dataset:1",
            "projects": [
                {
                    "pid": "project:existing",
                    "name": "Existing project",
                },
            ],
        },
    )

    records = json_lines(result)

    assert records[0]["projects"] == [
        {
            "pid": "project:existing",
            "name": "Existing project",
        },
        {
            "pid": "project:1",
            "name": "Project One",
            "datasets": ["dataset:1"],
        },
    ]


def test_converts_existing_scalar_to_list(
    invoke,
    linker_query,
):
    records_by_collection, _ = linker_query
    records_by_collection["public"] = [
        (
            {
                "pid": "person:1",
                "name": "New person",
                "projects": ["project:1"],
            },
            {},
        ),
    ]

    result = invoke(
        [
            "people",
            "--link",
            "projects",
        ],
        {
            "pid": "project:1",
            "people": {
                "pid": "person:existing",
                "name": "Existing person",
            },
        },
    )

    records = json_lines(result)

    assert records[0]["people"] == [
        {
            "pid": "person:existing",
            "name": "Existing person",
        },
        {
            "pid": "person:1",
            "name": "New person",
            "projects": ["project:1"],
        },
    ]


def test_queries_each_configured_collection(
    invoke,
    linker_query,
):
    records_by_collection, calls = linker_query
    records_by_collection["private"] = [
        (
            {
                "pid": "person:private",
                "projects": ["project:1"],
            },
            {},
        ),
    ]

    result = invoke(
        [
            "people",
            "--link",
            "projects",
            "--class",
            "Person",
            "-c",
            "public",
            "-c",
            "private",
        ],
        {"pid": "project:1"},
    )

    records = json_lines(result)

    assert [call["collection"] for call in calls] == [
        "public",
        "private",
    ]
    assert records[0]["people"] == [{
        "pid": "person:private",
        "projects": ["project:1"],
    }]


def test_multiple_link_properties_match_with_or_semantics(
    invoke,
    linker_query,
):
    records_by_collection, _ = linker_query
    records_by_collection["public"] = [
        (
            {
                "pid": "person:1",
                "projects": ["project:1"],
                "datasets": ["dataset:1"],
            },
            {},
        ),
    ]

    result = invoke(
        [
            "people",
            "--link",
            "projects",
            "--link",
            "datasets",
        ],
        {"pid": "dataset:1"},
    )

    records = json_lines(result)

    assert records[0]["people"] == [{
        "pid": "person:1",
        "projects": ["project:1"],
        "datasets": ["dataset:1"],
    }]
