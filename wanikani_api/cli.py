import click
from .client import Client
import os
from datetime import datetime

@click.command()
@click.option('-a', '--api-key', prompt='Enter your v.2 API key:', required=True)
def main(api_key):
    wk = Client(api_key)

    click.echo('This is the information I found about you: {}'.format(wk.user_information()))
    pending = wk.assignments(available_before=datetime.now(), hidden=False)
    click.echo('You have {} reviews waiting:'.format(len(pending)))
    for assignment in pending:
        click.echo(f'{assignment.subject.characters} ({assignment.available_at})')


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter, unexpected-keyword-arg
    main(auto_envvar_prefix='WANIKANI')