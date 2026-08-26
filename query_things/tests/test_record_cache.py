import json
from pathlib import Path

import pytest

from query_things.common.cache import RecordCache


def test_constructor_default_is_empty():
    cache = RecordCache()

    assert len(cache) == 0
    assert dict(cache) == {}


def test_constructor_with_none_data_is_empty():
    cache = RecordCache(data=None)

    assert len(cache) == 0
    assert dict(cache) == {}


def test_constructor_with_data():
    data = {
        'a': {'v': 1},
        'b': None,
    }

    cache = RecordCache(data=data)

    assert cache['a'] == {'v': 1}
    assert cache['b'] is None
    assert len(cache) == 2  # noqa: PLR2004


def test_getitem_existing():
    cache = RecordCache(data={'a': {'v': 1}, 'b': None})

    assert cache['a'] == {'v': 1}
    assert cache['b'] is None


def test_getitem_missing_raises_key_error():
    cache = RecordCache()

    with pytest.raises(KeyError, match='missing'):
        cache['missing']


def test_setitem_adds_and_updates():
    cache = RecordCache()

    cache['a'] = {'v': 1}
    assert cache['a'] == {'v': 1}

    cache['a'] = {'v': 2}
    assert cache['a'] == {'v': 2}


def test_setitem_can_store_none():
    cache = RecordCache()

    cache['a'] = None

    assert cache['a'] is None
    assert 'a' in cache


def test_contains():
    cache = RecordCache(data={'a': {'v': 1}, 'b': None})

    assert 'a' in cache
    assert 'b' in cache
    assert 'c' not in cache


def test_delitem_existing():
    cache = RecordCache(data={'a': {'v': 1}})

    del cache['a']

    assert 'a' not in cache
    assert len(cache) == 0


def test_delitem_missing_raises_key_error():
    cache = RecordCache()

    with pytest.raises(KeyError, match='missing'):
        del cache['missing']


def test_iter_yields_keys():
    cache = RecordCache(data={'a': {'v': 1}, 'b': {'v': 2}})

    assert list(iter(cache)) == ['a', 'b']


def test_len_reflects_changes():
    cache = RecordCache(data={'a': {'v': 1}, 'b': {'v': 2}})

    assert len(cache) == 2  # noqa: PLR2004

    cache['c'] = {'v': 3}
    assert len(cache) == 3  # noqa: PLR2004

    del cache['a']
    assert len(cache) == 2  # noqa: PLR2004


def test_keys_values_items_are_dynamic_views():
    cache = RecordCache(data={'a': {'v': 1}})

    keys = cache.keys()
    values = cache.values()

    assert list(keys) == ['a']
    assert list(values) == [{'v': 1}]

    cache['b'] = {'v': 2}

    assert list(keys) == ['a', 'b']
    assert list(values) == [{'v': 1}, {'v': 2}]


def test_get_existing_value():
    cache = RecordCache(data={'a': {'v': 1}})

    assert cache.get('a') == {'v': 1}


def test_get_existing_none_value():
    cache = RecordCache(data={'a': None})

    assert cache.get('a') is None


def test_get_missing_key_with_default():
    cache = RecordCache()
    default = {'fallback': True}

    assert cache.get('missing', default) is default


def test_get_missing_key_with_explicit_none_default():
    cache = RecordCache()

    assert cache.get('missing', None) is None


def test_load_none_path_returns_empty_cache():
    cache = RecordCache.load(None)

    assert len(cache) == 0


def test_load_returns_record_cache_instance(tmp_path: Path):
    path = tmp_path / 'cache.json'
    path.write_text('{}')

    cache = RecordCache.load(path)

    assert isinstance(cache, RecordCache)


def test_load_valid_empty_json_object(tmp_path: Path):
    path = tmp_path / 'cache.json'
    path.write_text('{}')

    cache = RecordCache.load(path)

    assert len(cache) == 0


def test_load_valid_json_object_uses_path(tmp_path: Path):
    path = tmp_path / 'cache.json'
    original = {'a': {'v': 1}, 'b': None}
    path.write_text(json.dumps(original))

    cache = RecordCache.load(path)

    assert cache['a'] == {'v': 1}
    assert cache['b'] is None
    assert len(cache) == 2  # noqa: PLR2004

    cache['c'] = {'v': 3}
    cache.save()

    assert json.loads(path.read_text()) == {
        'a': {'v': 1},
        'b': None,
        'c': {'v': 3},
    }


def test_load_missing_file_returns_empty_cache(tmp_path: Path):
    path = tmp_path / 'missing.json'

    cache = RecordCache.load(path)

    assert len(cache) == 0

    cache['a'] = {'v': 1}
    cache.save()

    assert json.loads(path.read_text()) == {'a': {'v': 1}}


def test_load_invalid_json_returns_empty_cache(tmp_path: Path):
    path = tmp_path / 'cache.json'
    path.write_text('{not valid json')

    cache = RecordCache.load(path)

    assert len(cache) == 0


def test_load_invalid_json_keeps_path_for_saving(tmp_path: Path):
    path = tmp_path / 'cache.json'
    path.write_text('{not valid json')

    cache = RecordCache.load(path)
    cache['a'] = {'v': 1}
    cache.save()

    assert json.loads(path.read_text()) == {'a': {'v': 1}}


@pytest.mark.parametrize(
    'raw_json',
    [
        'null',
        '"string"',
        '123',
        'true',
        '[1, 2, 3]',
    ],
)
def test_load_non_dict_json_returns_empty_cache(tmp_path: Path, raw_json: str):
    path = tmp_path / 'cache.json'
    path.write_text(raw_json)

    cache = RecordCache.load(path)

    assert len(cache) == 0


def test_load_non_dict_json_keeps_path_for_saving(tmp_path: Path):
    path = tmp_path / 'cache.json'
    path.write_text('[1, 2, 3]')

    cache = RecordCache.load(path)
    cache['a'] = {'v': 1}
    cache.save()

    assert json.loads(path.read_text()) == {'a': {'v': 1}}


def test_save_writes_json(tmp_path: Path):
    path = tmp_path / 'cache.json'
    cache = RecordCache(path=path, data={'a': {'v': 1}, 'b': None})

    cache.save()

    assert json.loads(path.read_text()) == {'a': {'v': 1}, 'b': None}


def test_save_no_path_does_not_raise():
    cache = RecordCache(data={'a': {'v': 1}})

    cache.save()


def test_save_empty_cache_does_not_create_file(tmp_path: Path):
    path = tmp_path / 'cache.json'
    cache = RecordCache(path=path)

    cache.save()

    assert not path.exists()


def test_save_empty_cache_does_not_overwrite_existing_file(tmp_path: Path):
    path = tmp_path / 'cache.json'
    path.write_text(json.dumps({'old': {'v': 1}}))

    cache = RecordCache(path=path, data={})
    cache.save()

    assert json.loads(path.read_text()) == {'old': {'v': 1}}


def test_save_cache_with_only_none_values(tmp_path: Path):
    path = tmp_path / 'cache.json'
    cache = RecordCache(path=path, data={'a': None})

    cache.save()

    assert json.loads(path.read_text()) == {'a': None}


def test_save_overwrites_existing_file(tmp_path: Path):
    path = tmp_path / 'cache.json'
    path.write_text(json.dumps({'old': {'v': 1}}))

    cache = RecordCache(path=path, data={'new': {'v': 2}})
    cache.save()

    assert json.loads(path.read_text()) == {'new': {'v': 2}}


def test_save_and_load_roundtrip(tmp_path: Path):
    path = tmp_path / 'cache.json'
    data = {
        'user-1': {'name': 'Alice', 'tags': ['a', 'b']},
        'user-2': None,
    }

    cache = RecordCache(path=path, data=data)
    cache.save()

    loaded = RecordCache.load(path)

    assert len(loaded) == len(data)
    assert all(loaded[k] == data[k] for k in data)
