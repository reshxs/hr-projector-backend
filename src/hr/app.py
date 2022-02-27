import asyncio
import logging
import os

from concurrent.futures import ThreadPoolExecutor

import django.db
import fastapi_jsonrpc
from fastapi.staticfiles import StaticFiles
from django.core.asgi import get_asgi_application as get_django_asgi_app
from django.conf import settings
from starlette.responses import RedirectResponse

from hr.api.web import api_v1 as web_api_v1

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


class DjangoThreadPoolExecutor(ThreadPoolExecutor):
    def submit(self, fn, *args, **kwargs):
        def func():
            django.db.reset_queries()
            django.db.close_old_connections()
            return fn(*args, **kwargs)

        return super().submit(func)


app = fastapi_jsonrpc.API(
    title='HR PROJECTOR',
    version='1.0.0',
    description='Тут будет описание',
)

app.bind_entrypoint(web_api_v1)


default_executor = DjangoThreadPoolExecutor(max_workers=4)  # TODO: add to settings


@app.on_event('startup')
async def on_startup():
    loop = asyncio.get_running_loop()
    logger.info('Setup ThreadPoolExecutor: max_workers=%s', 4)
    loop.set_default_executor(default_executor)


app.mount('/app', get_django_asgi_app())
app.mount(
    '/static',
    app=StaticFiles(directory=settings.STATIC_ROOT.as_posix(), check_dir=False),
    name='staticfiles',
)


@app.get('/')
def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse('/docs')
