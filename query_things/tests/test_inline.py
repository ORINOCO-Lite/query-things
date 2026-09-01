import copy

import pytest

from query_things.inline_things import (
    inline_records,
    walk,
)


def make_get_obj(records: dict[str, dict]):
    return lambda pid: records.get(pid)


@pytest.mark.parametrize(
    ('obj', 'path', 'records', 'expected'),
    [
        (
            {'a': {'b': 'thing:1'}},
            ('a', 'b'),
            {'thing:1': {'pid': 'thing:1', 'name': 'resolved'}},
            {'a': {'b': {'pid': 'thing:1', 'name': 'resolved'}}},
        ),
        (
            {'a': {'b': {'c': 'thing:1'}}},
            ('a', 'b', 'c'),
            {'thing:1': {'pid': 'thing:1'}},
            {'a': {'b': {'c': {'pid': 'thing:1'}}}},
        ),
        (
            {'items': [{'ref': 'thing:1'}, {'ref': 'thing:2'}]},
            ('items', 'ref'),
            {
                'thing:1': {'pid': 'THING:1'},
                'thing:2': {'pid': 'THING:2'},
            },
            {
                'items': [
                    {'ref': {'pid': 'THING:1'}},
                    {'ref': {'pid': 'THING:2'}},
                ]
            },
        ),
        (
            {'a': {'b': 'plain text'}},
            ('a', 'b'),
            {'plain text': {'pid': 'plain text'}},
            {'a': {'b': 'plain text'}},
        ),
        (
            {'a': {'b': 'thing:1'}},
            ('a', 'b'),
            {},
            {'a': {'b': 'thing:1'}},
        ),
        (
            {'inf': [{'obj': 'ex:inf'}]},
            ('inf', 'obj', 'att', 'obj'),
            {
                'ex:inf': {'pid': 'ex:inf', 'att': [{'obj': 'ex:att'}]},
                'ex:att': {'pid': 'ex:att', 'dummy': 'yes'},
            },
            {
                'inf': [
                    {
                        'obj': {
                            'pid': 'ex:inf',
                            'att': [{'obj': {'pid': 'ex:att', 'dummy': 'yes'}}],
                        }
                    }
                ]
            },
        ),
    ],
)
def test_walk_inlines_pid_references(obj, path, records, expected):
    obj = copy.deepcopy(obj)

    walk(obj, path, make_get_obj(records))

    assert obj == expected


def test_inline_records_mutates_multiple_paths():
    obj = {
        'author': 'person:1',
        'nested': {'thing': 'thing:2'},
    }
    records = {
        'person:1': {'pid': 'person:1'},
        'thing:2': {'pid': 'thing:2'},
    }

    inline_records(
        obj,
        [('author',), ('nested', 'thing')],
        make_get_obj(records),
    )

    assert obj == {
        'author': {'pid': 'person:1'},
        'nested': {'thing': {'pid': 'thing:2'}},
    }
