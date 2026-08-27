import pytest

from query_things.cache import cli
from query_things.common.cache import RecordCache
from query_things.tests import (
    cache_as_dict,
    jsonl_lines,
    make_record,
)


@pytest.mark.parametrize(
    ('items', 'expected_cache'),
    [
        ([], {}),
        ([''], {}),
        (['not json'], {}),
        ([{'name': 'no pid'}], {}),
        (
            [make_record('123', name='example')],
            {'123': make_record('123', name='example')},
        ),
        (
            [
                make_record('1', value='first'),
                'not json',
                {'name': 'missing pid'},
                make_record('2', value='second'),
            ],
            {
                '1': make_record('1', value='first'),
                '2': make_record('2', value='second'),
            },
        ),
        (
            [
                make_record('123', value='old'),
                make_record('123', value='new'),
            ],
            {'123': make_record('123', value='new')},
        ),
    ],
)
def test_cache_command_caches_valid_records_and_echoes(
    run_callback,
    items,
    expected_cache,
):
    input_text = jsonl_lines(*items)
    cache = RecordCache()

    result = run_callback(
        cli.callback,
        input_text=input_text,
        record_cache=cache,
    )

    assert result.out == input_text
    assert result.err == ''
    assert cache_as_dict(cache) == expected_cache
