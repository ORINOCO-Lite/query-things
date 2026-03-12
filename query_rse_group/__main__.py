import click
from query_rse_group import (
    filter_linked_pid,
    filter_links_pid,
    inject_links_pid,
    inline_records,
    render_record,
    cache,
    list,
)


@click.group()
def main():
    """Tools to query, filter, and process research information schema metadata
    """


for mod in (
    filter_linked_pid,
    filter_links_pid,
    inject_links_pid,
    inline_records,
    render_record,
    cache,
    list,
):
    main.add_command(getattr(mod, 'cli'))


if __name__ == '__main__':
    main()
