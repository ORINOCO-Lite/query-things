from dump_things_pyclient.communicate import (  # type: ignore[import-untyped]
    collection_read_records_of_class,
)

from query_things.common import (
    Record,
    record_has_link,
)


def inject_linking_records(
    record: Record,
    *,
    inject: str,
    collections: tuple[str, ...],
    link: tuple[str, ...],
    api_url: str,
    class_name: str | None = None,
    token: str | None = None,
) -> None:
    """Update input record with linking records injected at `inject`.

    Records from the given collections are looked up that link to the given
    record via any of the given `link` properties.  Those records are added to
    the value of the `inject` property: the property is created if absent,
    extended if it is a list, or promoted to a list if it holds a single value.
    """
    linkers = []
    for col in collections:
        linkers.extend(
            get_any_thing_that_links_pid_via_x(
                link,
                class_name,
                api_url,
                col,
                record['pid'],
                token=token,
            )
        )
    target = record.get(inject)
    if target is None:
        record[inject] = linkers
    elif isinstance(target, list):
        target.extend(linkers)
        record[inject] = target
    else:
        linkers.insert(0, target)
        record[inject] = linkers


def get_any_thing_that_links_pid_via_x(
    link: tuple[str, ...],
    class_name: str | None,
    api_url: str,
    collection: str,
    pid: str,
    token: str | None = None,
):
    return [
        res[0]
        for res in collection_read_records_of_class(
            api_url,
            collection,
            class_name if class_name else 'Thing',
            matching=pid,
            token=token,
        )
        if any(record_has_link(res[0], prop_id, pid) for prop_id in link)
    ]
