import os

import django

# Инициализируем Django до инициализации приложения:
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

import click
import uvicorn

from django.core import management
from django.conf import settings
import hr.app


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    '--collectstatic/--no-collectstatic',
    is_flag=True,
    default=True,
    help='collect Django static',
)
@click.option(
    '--uvicorn-debug/--no-uvicorn-debug',
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
        host=settings.HOST,
        port=settings.PORT,
        debug=uvicorn_debug,
        access_log=False,
        log_config=None,
        lifespan='on',
        loop='uvloop',
    )


if __name__ == '__main__':
    cli()
