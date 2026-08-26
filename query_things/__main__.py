import click

from query_things import (
    cache,
    filter_linked_pid,
    filter_links_pid,
    inject_links_pid,
    inline_records,
    inline_things,
    list,
    render_record,
)


@click.group()
def main():
    """Tools to query, filter, and process Things-compliant metadata
    """


for mod in (
    filter_linked_pid,
    filter_links_pid,
    inject_links_pid,
    inline_records,
    inline_things,
    render_record,
    cache,
    list,
):
    main.add_command(mod.cli)


if __name__ == '__main__':
    main()
