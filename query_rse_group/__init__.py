from dump_things_pyclient.communicate import collection_read_record_with_pid

# this collection cannot contain the help strings.
# they are hard to write generic and still be fitting.
# also, arguments do not have help.
stdargs = {
    '--api-url': {
        'envvar': 'DUMPTHINGS_APIURL',
    },
    'collection': {},
    '--token': {
        'envvar': 'DUMPTHINGS_TOKEN',
    },
}


def _get_rec_from_any_collection(
    api_url: str,
    collections: tuple[str],
    pid: str,
    cache: dict,
    token: str | None = None,
):
    for col in collections:
        rec = cache.get(pid) or collection_read_record_with_pid(
            api_url,
            col,
            pid,
            token=token,
        )
        if rec is not None:
            cache[pid] = rec
            return rec

    # yes, also cache that we asked and nothing was there
    cache[pid] = None
    return None
