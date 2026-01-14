import click
from query_rse_group import (
    filter_linked_pid,
    filter_projects,
    inline_records,
    render_record,
    resolve_datasets,
)


@click.group()
def main():
    """Tools to query, filter, and process RSE group schema metadata
    """


for mod in (
    filter_linked_pid,
    filter_projects,
    inline_records,
    render_record,
    resolve_datasets,
):
    main.add_command(getattr(mod, 'cli'))


if __name__ == '__main__':
    main()
