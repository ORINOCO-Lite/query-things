import click
import pytest

from query_things.common.cache import RecordCache
from query_things.list import cli
from query_things.tests import (
    make_record,
    output_records,
)

person = make_record('pid-1', schema_type='Person', name='Alice')
company = make_record('pid-2', schema_type='Company', name='Example Inc.')
animal = make_record('pid-3', schema_type='Animal')
no_type = make_record('pid-4', name='No schema type')

cache = {
    'pid-1': person,
    'pid-2': company,
    'pid-3': animal,
    'pid-4': no_type,
    'null': None,
}


@pytest.mark.parametrize(
    ('cache_data', 'pid', 'cls', 'expected'),
    [
        ({}, (), (), []),
        (cache, (), (), [person, company, animal, no_type]),
        (cache, (), ('Person',), [person]),
        (cache, (), ('Person', 'Company'), [person, company]),
        (cache, (), ('Animal',), [animal]),
        (cache, ('pid-2', 'pid-1'), (), [company, person]),
        (cache, ('pid-2',), ('Person',), [company]),
        ({'pid-1': person, 'null': None}, ('pid-1',), (), [person]),
    ],
)
def test_list_outputs_filtered_records(
    run_callback,
    cache_data,
    pid,
    cls,
    expected,
):
    record_cache = RecordCache(data=cache_data)

    result = run_callback(
        cli.callback,
        record_cache=record_cache,
        pid=pid,
        cls=cls,
    )

    assert output_records(result.out) == expected


def test_missing_pid_raises_click_exception(run_callback, capsys):
    record_cache = RecordCache(data={'pid-1': person})

    with pytest.raises(click.ClickException, match='No record'):
        run_callback(
            cli.callback,
            record_cache=record_cache,
            pid=('missing',),
            cls=(),
        )

    assert capsys.readouterr().out == ''


def test_missing_pid_error_stops_processing(run_callback, capsys):
    record_cache = RecordCache(data={'pid-1': person})

    with pytest.raises(click.ClickException):
        run_callback(
            cli.callback,
            record_cache=record_cache,
            pid=('pid-1', 'missing'),
            cls=(),
        )

    assert capsys.readouterr().out == ''
