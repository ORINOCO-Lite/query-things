import json

import pytest

from query_things.common import jsonl_from_record
from query_things.common.cache import RecordCache
from query_things.tests import (
    cache_as_dict,
)


@pytest.mark.parametrize(
    ('data', 'expected'),
    [
        (None, {}),
        ({'a': {'v': 1}, 'b': None}, {'a': {'v': 1}, 'b': None}),
    ],
)
def test_constructor(data, expected):
    cache = RecordCache(data=data)

    assert cache_as_dict(cache) == expected
    assert len(cache) == len(expected)


def test_mapping_read_protocol():
    cache = RecordCache(data={'a': {'v': 1}, 'b': None})

    assert cache['a'] == {'v': 1}
    assert cache['b'] is None
    assert 'a' in cache
    assert 'b' in cache
    assert 'c' not in cache
    assert list(cache) == ['a', 'b']
    assert len(cache) == 2  # noqa: PLR2004
    assert cache.get('a') == {'v': 1}
    assert cache.get('b') is None
    assert cache.get('missing', {'fallback': True}) == {'fallback': True}
    assert cache.get('missing') is None


def test_mapping_write_protocol():
    cache = RecordCache()

    cache['a'] = {'v': 1}
    cache['a'] = {'v': 2}
    cache['b'] = None

    assert cache['a'] == {'v': 2}
    assert cache['b'] is None
    assert len(cache) == 2  # noqa: PLR2004

    del cache['a']

    assert 'a' not in cache
    assert len(cache) == 1


def test_missing_key_errors():
    cache = RecordCache()

    with pytest.raises(KeyError, match='missing'):
        cache['missing']

    with pytest.raises(KeyError, match='missing'):
        del cache['missing']


def test_views_are_live():
    cache = RecordCache(data={'a': {'v': 1}})

    keys = cache.keys()
    values = cache.values()

    assert list(keys) == ['a']
    assert list(values) == [{'v': 1}]

    cache['b'] = {'v': 2}

    assert list(keys) == ['a', 'b']
    assert list(values) == [{'v': 1}, {'v': 2}]


@pytest.mark.parametrize(
    ('content', 'expected'),
    [
        (None, {}),
        ('{}', {}),
        ('{"a":{"v":1},"b":null}', {'a': {'v': 1}, 'b': None}),
        ('{not valid json', {}),
        ('null', {}),
        ('"string"', {}),
        ('123', {}),
        ('true', {}),
        ('[1,2,3]', {}),
    ],
)
def test_load_returns_expected_cache(tmp_path, content, expected):
    path = tmp_path / 'cache.json'
    if content is not None:
        path.write_text(content, encoding='utf-8')

    cache = RecordCache.load(path)

    assert cache_as_dict(cache) == expected


def test_load_none_path_returns_empty_cache():
    cache = RecordCache.load(None)

    assert len(cache) == 0
    assert cache_as_dict(cache) == {}


@pytest.mark.parametrize(
    ('content', 'initial'),
    [
        ('{}', {}),
        ('{"a":{"v":1},"b":null}', {'a': {'v': 1}, 'b': None}),
        ('{not valid json', {}),
        ('[1,2,3]', {}),
    ],
)
def test_load_keeps_path_and_retains_valid_data(tmp_path, content, initial):
    path = tmp_path / 'cache.json'
    path.write_text(content, encoding='utf-8')

    cache = RecordCache.load(path)
    cache['c'] = {'v': 3}
    cache.save()

    assert json.loads(path.read_text(encoding='utf-8')) == {
        **initial,
        'c': {'v': 3},
    }


@pytest.mark.parametrize(
    ('data', 'expected'),
    [
        ({'a': {'v': 1}, 'b': None}, {'a': {'v': 1}, 'b': None}),
        ({'a': None}, {'a': None}),
    ],
)
def test_save_writes_json(tmp_path, data, expected):
    path = tmp_path / 'cache.json'
    cache = RecordCache(path=path, data=data)

    cache.save()

    assert json.loads(path.read_text(encoding='utf-8')) == expected


def test_save_without_path_is_noop():
    RecordCache(data={'a': {'v': 1}}).save()


def test_save_empty_cache_does_not_create_file(tmp_path):
    path = tmp_path / 'cache.json'

    RecordCache(path=path, data={}).save()

    assert not path.exists()


def test_save_empty_cache_does_not_overwrite_existing_file(tmp_path):
    path = tmp_path / 'cache.json'
    path.write_text(jsonl_from_record({'old': {'v': 1}}))

    RecordCache(path=path, data={}).save()

    assert json.loads(path.read_text(encoding='utf-8')) == {'old': {'v': 1}}


def test_save_overwrites_existing_file(tmp_path):
    path = tmp_path / 'cache.json'
    path.write_text(jsonl_from_record({'old': {'v': 1}}))

    RecordCache(path=path, data={'new': {'v': 2}}).save()

    assert json.loads(path.read_text(encoding='utf-8')) == {'new': {'v': 2}}


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / 'cache.json'
    data = {
        'user-1': {'name': 'Alice', 'tags': ['a', 'b']},
        'user-2': None,
    }

    RecordCache(path=path, data=data).save()

    loaded = RecordCache.load(path)

    assert len(loaded) == len(data)
    assert all(loaded[key] == data[key] for key in data)


def test_readers_see_complete_cache_during_save(tmp_path, monkeypatch):
    path = tmp_path / 'cache.json'
    original = {'homepage': {'pid': 'example:.'}}
    path.write_text(json.dumps(original))
    observed = []
    dump = json.dump

    def interrupted_write(data, stream):
        stream.write('{')
        stream.flush()
        observed.append(cache_as_dict(RecordCache.load(path)))
        stream.seek(0)
        stream.truncate()
        dump(data, stream)

    monkeypatch.setattr(json, 'dump', interrupted_write)
    updated = {**original, 'person': {'pid': 'example:person'}}
    RecordCache(path=path, data=updated).save()
    assert observed == [original]
    assert cache_as_dict(RecordCache.load(path)) == updated


def test_failed_save_preserves_complete_cache(tmp_path, monkeypatch):
    path = tmp_path / 'cache.json'
    original = {'homepage': {'pid': 'example:.'}}
    path.write_text(json.dumps(original))

    def fail(data, stream):
        stream.write('{')
        raise ValueError('interrupted serialization')

    monkeypatch.setattr(json, 'dump', fail)
    with pytest.raises(ValueError, match='interrupted serialization'):
        RecordCache(path=path, data={'replacement': {}}).save()
    assert cache_as_dict(RecordCache.load(path)) == original
