import json


def _handle_record_cache(ctx, _, value) -> dict:
    if value is None:
        # we return a cache, but it will be in-memory only
        return {}

    try:
        with value.open('r') as fp:
            cache = json.load(fp)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        # ok if it doesn't exist yet. If it doesn't load, we ignore it
        cache = {}

    # protect against invalid cache content
    if not isinstance(cache, dict):
        cache = {}

    @ctx.call_on_close
    def dump_cache():
        if not cache:
            # do not write an empty cache
            return
        with value.open('w') as fp:
            json.dump(cache, fp)

    return cache
