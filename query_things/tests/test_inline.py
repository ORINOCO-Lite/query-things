import pytest

from query_things.inline_things import walk, inline_json_objects


def test_walk_inlines_string_reference_in_nested_dict():
    obj = {"a": {"b": "thing:1"}}

    def get_obj(pid):
        return {"pid": pid, "name": "resolved"} if pid == "thing:1" else None

    walk(obj, ("a", "b"), get_obj)

    assert obj["a"]["b"] == {"pid": "thing:1", "name": "resolved"}


def test_walk_recurses_into_lists():
    obj = {"items": [{"ref": "thing:1"}, {"ref": "thing:2"}]}

    def get_obj(pid):
        return {"pid": pid.upper()} if pid in {"thing:1", "thing:2"} else None

    walk(obj, ("items", "ref"), get_obj)

    assert obj["items"][0]["ref"] == {"pid": "THING:1"}
    assert obj["items"][1]["ref"] == {"pid": "THING:2"}


def test_walk_does_not_change_non_matching_values():
    obj = {"a": {"b": "plain text"}}

    def get_obj(pid):
        return {"pid": pid}

    walk(obj, ("a", "b"), get_obj)

    assert obj["a"]["b"] == "plain text"


def test_inline_json_objects_mutates_multiple_paths():
    obj = {
        "author": "person:1",
        "nested": {"thing": "thing:2"},
    }

    def get_obj(pid):
        return {"pid": pid}

    inline_json_objects(obj, [("author",), ("nested", "thing")], get_obj)

    assert obj == {
        "author": {"pid": "person:1"},
        "nested": {"thing": {"pid": "thing:2"}},
    }


def test_walk_ignores_unresolved_reference():
    obj = {"a": {"b": "thing:1"}}

    def get_obj(pid):
        return None

    walk(obj, ("a", "b"), get_obj)

    assert obj["a"]["b"] == "thing:1"
