import click

from query_things import (
    cache,
    filter_linked_pid,
    filter_links_pid,
    inject_links_pid,
    inline_records,
    inline_things,
    render_record,
)
from query_things import (
    list as list_cmd,
)


@click.group()
def main():
    """Tools to query, filter, and process Things-compliant metadata"""


for mod in (
    filter_linked_pid,
    filter_links_pid,
    inject_links_pid,
    inline_things,
    render_record,
    cache,
    list_cmd,
):
    main.add_command(mod.cli)

# accept, but no longer show
main.add_command(inline_records.cli, hidden=True)


if __name__ == '__main__':
    main()
