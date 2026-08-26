import io
import json

import pytest

from query_things.cache import cli


def run_cache_command(monkeypatch, capsys, input_text, record_cache):
    """Run the Click callback with controlled stdin/stdout."""
    monkeypatch.setattr("sys.stdin", io.StringIO(input_text))

    cli.callback(record_cache=record_cache)

    return capsys.readouterr()


def test_caches_valid_json_record_with_pid(monkeypatch, capsys):
    record = {"pid": "123", "name": "example"}
    input_text = json.dumps(record) + "\n"
    record_cache = {}

    result = run_cache_command(
        monkeypatch,
        capsys,
        input_text,
        record_cache,
    )

    assert record_cache == {"123": record}
    assert result.out == input_text
    assert result.err == ""


def test_passes_through_valid_record_without_caching(monkeypatch, capsys):
    input_text = '{"name": "missing pid"}\n'
    record_cache = {}

    result = run_cache_command(
        monkeypatch,
        capsys,
        input_text,
        record_cache,
    )

    assert record_cache == {}
    assert result.out == input_text
    assert result.err == ""


def test_ignores_invalid_json_but_passes_it_through(monkeypatch, capsys):
    input_text = "this is not valid JSON\n"
    record_cache = {}

    result = run_cache_command(
        monkeypatch,
        capsys,
        input_text,
        record_cache,
    )

    assert record_cache == {}
    assert result.out == input_text
    assert result.err == ""


def test_processes_multiple_lines(monkeypatch, capsys):
    first = {"pid": "1", "value": "first"}
    second = {"pid": "2", "value": "second"}

    input_text = (
        json.dumps(first)
        + "\n"
        + "not json\n"
        + json.dumps({"value": "missing pid"})
        + "\n"
        + json.dumps(second)
        + "\n"
    )
    record_cache = {}

    result = run_cache_command(
        monkeypatch,
        capsys,
        input_text,
        record_cache,
    )

    assert record_cache == {
        "1": first,
        "2": second,
    }
    assert result.out == input_text
    assert result.err == ""


def test_duplicate_pid_is_overwritten_by_latest_record(monkeypatch, capsys):
    first = {"pid": "123", "value": "old"}
    second = {"pid": "123", "value": "new"}

    input_text = json.dumps(first) + "\n" + json.dumps(second) + "\n"
    record_cache = {}

    result = run_cache_command(
        monkeypatch,
        capsys,
        input_text,
        record_cache,
    )

    assert record_cache == {"123": second}
    assert result.out == input_text


@pytest.mark.parametrize(
    "input_text",
    [
        "",
        "\n",
        "plain text",
        "{broken json",
        '{"name": "without pid"}',
    ],
)
def test_invalid_or_non_cacheable_input_is_still_emitted(
    monkeypatch,
    capsys,
    input_text,
):
    record_cache = {}

    result = run_cache_command(
        monkeypatch,
        capsys,
        input_text,
        record_cache,
    )

    assert record_cache == {}
    assert result.out == input_text

