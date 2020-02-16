import click
from .client import Client
import os
from datetime import datetime
import json

import csv

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
    pending = wk.assignments(available_before=datetime.now(), hidden=False)
    click.echo('You have {} reviews waiting:'.format(len(pending)))
    for assignment in pending:
        click.echo(f'{assignment.subject.characters} ({assignment.available_at})')


@main.command()
@click.argument('csv_file', type=click.Path(writable=True, dir_okay=False))
@click.pass_obj
def statistics(wk, csv_file):
    click.echo("Exporting reviews")

    if os.path.exists(csv_file):
        click.confirm('File already exists, overwrite?', abort=True)

    stats = wk.review_statistics()
    
    headers = stats[0]._resource.keys()

    with open(csv_file, 'w', newline='') as csv_fd:
        csv_writer = csv.DictWriter(csv_fd, fieldnames=headers)
        csv_writer.writeheader()

        with click.progressbar(stats) as bar:
            for stat in bar:
                csv_writer.writerow(stat._resource)
        


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter, unexpected-keyword-arg
    main(auto_envvar_prefix='WANIKANI')