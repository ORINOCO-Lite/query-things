import click

from query_things.cli import (
    cache,
    filter_linked_pid,
    filter_links_pid,
    inject_links_pid,
    inline_things,
    render_record,
)
from query_things.cli import (
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
