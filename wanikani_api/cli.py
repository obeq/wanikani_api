import click
from .client import Client
import os
from datetime import datetime, timezone
import json

import pandas as pd

@click.group()
@click.option('-a', '--api-key', required=False)
@click.pass_context
def main(ctx, api_key=None):
    if api_key is None:
        api_key = click.prompt('Please enter your v.2 API key')

    wk = Client(api_key)

    click.echo('This is the information I found about you: {}'.format(wk.user_information()))

    ctx.obj = wk


@main.command()
@click.pass_obj
def reviews(wk):
    pending = wk.assignments(available_before=datetime.utcnow(), hidden=False)
    click.echo('You have {} reviews waiting:'.format(len(pending)))
    for assignment in pending:
        click.echo(f'{assignment.subject.characters} ({assignment.available_at})')


@main.command()
@click.argument('data_type', type=click.Choice(['reviews', 'assignments', 'subjects']))
@click.argument('csv_file', type=click.Path(writable=True, dir_okay=False))
@click.pass_obj
def export(wk, data_type, csv_file):
    click.echo(f"Exporting {data_type}")

    if os.path.exists(csv_file):
        click.confirm('File already exists, overwrite?', abort=True)

    if data_type == 'reviews':
        stats = wk.review_statistics()
    else:
        stats = getattr(wk, data_type)()

    rev_frame = pd.DataFrame.from_records([stat._resource for stat in stats])

    rev_frame.to_csv(csv_file)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter, unexpected-keyword-arg
    main(auto_envvar_prefix='WANIKANI')