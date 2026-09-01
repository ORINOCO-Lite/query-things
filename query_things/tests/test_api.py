import json
from unittest.mock import patch

import pytest

from query_things.cache import cache_record
from query_things.common import (
    RecordCache,
    parse_json_objects,
)
from query_things.filter_linked_pid import (
    get_reference_linked_pids,
    record_matches_pids,
)
from query_things.filter_links_pid import record_links_pid
from query_things.inject_links_pid import inject_linking_records
from query_things.inline_things import inline_things
from query_things.list_records import list_records
from query_things.tests import (
    cache_as_dict,
    jsonl_lines,
    make_record,
)


def lines_of(*items):
    return jsonl_lines(*items).splitlines(keepends=True)


class TestParseJsonObjects:
    def test_yields_line_and_record(self):
        line = json.dumps(make_record('a:1', name='A'))
        assert list(parse_json_objects([line + '\n'])) == [
            (line + '\n', {'pid': 'a:1', 'name': 'A'})
        ]

    def test_skips_blank_lines(self):
        assert list(parse_json_objects(['\n', '   \n'])) == []

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match='Invalid JSON on line 1'):
            list(parse_json_objects(['not json\n']))

    def test_non_object_raises(self):
        with pytest.raises(ValueError, match='Line 1 must be a JSON object'):
            list(parse_json_objects(['[1, 2, 3]\n']))

    def test_missing_pid_raises(self):
        with pytest.raises(ValueError, match="Line 1 must have a string 'pid'"):
            list(parse_json_objects([json.dumps({'name': 'x'}) + '\n']))

    def test_non_string_pid_raises(self):
        with pytest.raises(ValueError, match="Line 1 must have a string 'pid'"):
            list(parse_json_objects([json.dumps({'pid': 1}) + '\n']))

    def test_line_numbering(self):
        with pytest.raises(ValueError, match='Invalid JSON on line 2'):
            list(
                parse_json_objects(
                    [json.dumps(make_record('a:1')) + '\n', 'not json\n']
                )
            )


class TestCacheRecords:
    def test_stores_and_passes_through(self):
        cache = RecordCache()
        rec = make_record('a:1')

        cache_record(rec, cache)

        assert cache_as_dict(cache) == {
            'a:1': make_record('a:1'),
        }

    def test_invalid_input_is_skipped_but_passed_through(self):
        cache = RecordCache()
        vals = [
            {},
            {'other', 5},
        ]

        for val in vals:
            assert cache_record(val, cache) == val

        assert cache_as_dict(cache) == {}

    def test_duplicate_pid_overwrites(self):
        cache = RecordCache()
        for rec in (
            make_record('a:1', name='old'),
            make_record('a:1', name='new'),
        ):
            cache_record(rec, cache)

        assert cache['a:1']['name'] == 'new'


class TestFilterLinkedPid:
    def test_get_reference_linked_pids(self):
        reference = {'links': ['p:1', {'object': 'p:2'}]}
        with patch(
            'query_things.filter_linked_pid.collection_read_record_with_pid'
        ) as read:
            read.return_value = reference
            pids = get_reference_linked_pids('people', 'pr:1', 'links', 'https://api')

        assert pids == frozenset({'p:1', 'p:2'})
        read.assert_called_once_with(
            service_url='https://api',
            collection='people',
            pid='pr:1',
            token=None,
        )

    def test_get_reference_linked_pids_missing_property(self):
        with patch(
            'query_things.filter_linked_pid.collection_read_record_with_pid'
        ) as read:
            read.return_value = {'other': 'x'}
            assert (
                get_reference_linked_pids('c', 'p', 'missing', 'https://api')
                == frozenset()
            )

    def test_filter_keeps_matching_records(self):
        pids = {'p:2'}
        assert not record_matches_pids(make_record('p:1'), pids)
        assert record_matches_pids(make_record('p:2'), pids)


class TestFilterLinksPid:
    @staticmethod
    def none_resolver(_) -> None:
        return None

    def test_direct_link_matches(self):
        rec = make_record('p:1', projects=[{'object': 'pr:1'}])
        other = make_record('p:2')

        kwargs = {
            'links': [('projects', 'pr:1')],
            'resolver': TestFilterLinksPid.none_resolver,
        }
        assert record_links_pid(rec, **kwargs)
        assert not record_links_pid(other, **kwargs)

    def test_all_links_required(self):
        rec = make_record('p:1', projects=[{'object': 'pr:1'}])

        assert not record_links_pid(
            rec,
            links=[('projects', 'pr:1'), ('projects', 'pr:2')],
            resolver=TestFilterLinksPid.none_resolver,
        )

    def test_file_links_match_any(self):
        rec = make_record('p:1', related=['pr:2'])

        assert record_links_pid(
            rec,
            file_links=[('related', frozenset({'pr:1', 'pr:2'}))],
            resolver=TestFilterLinksPid.none_resolver,
        )

    def test_no_links_keeps_all(self):
        assert all(
            record_links_pid(
                rec,
                resolver=TestFilterLinksPid.none_resolver,
            )
            for rec in (make_record('p:1'), make_record('p:2'))
        )


class TestInjectLinksPid:
    @pytest.mark.parametrize(
        ('rec', 'expected'),
        [
            (make_record('p:1'), [make_record('pr:1', author=[{'object': 'p:1'}])]),
            (
                make_record('p:1', projects=[{'object': 'pr:0'}]),
                [
                    {'object': 'pr:0'},
                    make_record('pr:1', author=[{'object': 'p:1'}]),
                ],
            ),
            (
                make_record('p:1', projects='pr:0'),
                [
                    'pr:0',
                    make_record('pr:1', author=[{'object': 'p:1'}]),
                ],
            ),
        ],
    )
    def test_inject(self, rec, expected):
        with patch(
            'query_things.inject_links_pid.collection_read_records_of_class'
        ) as read:
            read.return_value = [
                (make_record('pr:1', author=[{'object': 'p:1'}]), None)
            ]
            inject_linking_records(
                rec,
                inject='projects',
                link=('author',),
                api_url='https://api',
                collections=('public',),
            )

        assert rec['projects'] == expected
        read.assert_called_once()
        args, kwargs = read.call_args
        assert args[:2] == ('https://api', 'public')
        assert args[2] == 'Thing'
        assert kwargs == {'matching': 'p:1', 'token': None}

    def test_inject_respects_class_name(self):
        rec = make_record('p:1')
        with patch(
            'query_things.inject_links_pid.collection_read_records_of_class'
        ) as read:
            read.return_value = []
            inject_linking_records(
                rec,
                inject='projects',
                link=('author',),
                collections=['some'],
                api_url='https://api',
                class_name='Project',
            )

        args, _ = read.call_args
        assert args[2] == 'Project'

    def test_inject_skips_non_linking_records(self):
        rec = make_record('p:1')
        with patch(
            'query_things.inject_links_pid.collection_read_records_of_class'
        ) as read:
            read.return_value = [(make_record('pr:1', other='p:1'), None)]
            inject_linking_records(
                rec,
                inject='projects',
                link=('author',),
                collections=['some'],
                api_url='https://api',
            )

        assert rec['projects'] == []


class TestInlineThings:
    def test_inline_nested_reference(self):
        rec = make_record('p:1', projects=[{'object': 'pr:1'}])
        records = {'pr:1': make_record('pr:1', name='Proj')}

        out = list(
            inline_things(
                lines_of(rec),
                [('projects', 'object')],
                lambda pid: records.get(pid),
            )
        )

        assert json.loads(out[0])['projects'] == [
            {'object': make_record('pr:1', name='Proj')}
        ]

    def test_unresolved_reference_unchanged(self):
        rec = make_record('p:1', projects=[{'object': 'pr:1'}])

        out = list(
            inline_things(lines_of(rec), [('projects', 'object')], lambda _: None)
        )

        assert json.loads(out[0])['projects'] == [{'object': 'pr:1'}]

    def test_no_paths_is_passthrough(self):
        rec = make_record('p:1', projects=[{'object': 'pr:1'}])

        out = list(inline_things(lines_of(rec), [], lambda _: None))

        assert json.loads(out[0]) == rec


class TestListRecords:
    def test_pid_filter_preserves_order(self):
        cache = RecordCache(data={'a:1': make_record('a:1'), 'b:2': make_record('b:2')})

        assert [rec['pid'] for rec in list_records(cache, pid=('b:2', 'a:1'))] == [
            'b:2',
            'a:1',
        ]

    def test_missing_pid_raises_before_yield(self):
        cache = RecordCache(data={'a:1': make_record('a:1')})
        gen = list_records(cache, pid=('a:1', 'missing:1'))

        with pytest.raises(KeyError, match='missing:1'):
            next(gen)

    def test_null_cache_entry_counts_as_missing(self):
        cache = RecordCache(data={'a:1': None})

        with pytest.raises(KeyError):
            list(list_records(cache, pid=('a:1',)))

    def test_class_filter(self):
        cache = RecordCache(
            data={
                'a:1': make_record('a:1', schema_type='Project'),
                'b:2': make_record('b:2', schema_type='Person'),
                'c:3': make_record('c:3'),
            }
        )

        assert [rec['pid'] for rec in list_records(cache, cls=('Project',))] == ['a:1']

    def test_skips_null_records(self):
        cache = RecordCache(data={'a:1': make_record('a:1'), 'b:2': None})

        assert [rec['pid'] for rec in list_records(cache)] == ['a:1']

    def test_pid_takes_precedence_over_class(self):
        cache = RecordCache(
            data={
                'a:1': make_record('a:1', schema_type='Project'),
                'b:2': make_record('b:2', schema_type='Person'),
            }
        )

        assert [
            rec['pid'] for rec in list_records(cache, pid=('b:2',), cls=('Project',))
        ] == [
            'b:2',
        ]
