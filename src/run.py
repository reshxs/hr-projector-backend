import os

import click
import django
import uvicorn


# Иницилизируем Django ДО импортов приложения:
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from django.core import management
import hr.app


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    '--collectstatic/--no_collectstatic',
    is_flag=True,
    default=True,
    help='collect Django static',
)
@click.option(
    '--uvicorn-debug/--no_uvicorn-debug',
    is_flag=True,
    default=True,
    help='Enable/Disable debug and auto-reload'
)
def web(collectstatic: bool, uvicorn_debug: bool):
    app = hr.app.app

    if uvicorn_debug:
        app = 'hr.app:app'

    if collectstatic:
        management.call_command('collectstatic', '--no-input', '--clear')

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
        debug=uvicorn_debug,
        loop='uvloop',
    )


if __name__ == '__main__':
    cli()
