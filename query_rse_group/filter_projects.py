import click
import json
import sys


def _test_partof(rec: dict, part_of: str) -> bool:
    return part_of in rec.get('part_of', {})


@click.command()
@click.option(
    '--part-of', help='Identifier of a parent project', multiple=True)
def cli(part_of: str | None = None):
    """Filter project records matching particular criteria.

    Every option can be given multiple times. All values given
    for an individual check are considered to be valid alternatives
    (OR-test). Across different checks, all conditions must be met
    (AND-test).
    """
    for line in sys.stdin:
        rec = json.loads(line)
        report = True
        for check, checker in (
            (part_of, _test_partof),
        ):
            if check and not any(checker(rec, val) for val in check):
                # did not pass this check for any alternative,
                # we are done with this record
                report = False
                break
        if not report:
            continue
        click.echo(line, nl=False)
