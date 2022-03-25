import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import django.db
import fastapi_jsonrpc
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.asgi import get_asgi_application as get_django_asgi_app
from django.core.signals import request_started, request_finished
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import RedirectResponse

from hr.api.jsonrpc import api_v1 as jsonrpc_api_v1

logger = logging.getLogger(__name__)


class DjangoThreadPoolExecutor(ThreadPoolExecutor):
    def submit(self, fn, *args, **kwargs):
        def func():
            django.db.reset_queries()
            django.db.close_old_connections()
            return fn(*args, **kwargs)

        return super().submit(func)


default_executor = DjangoThreadPoolExecutor(max_workers=settings.THREADS)


app = fastapi_jsonrpc.API(
    title='HR PROJECTOR',
    version=settings.VERSION,
    description='Тут будет описание',
)

app.bind_entrypoint(jsonrpc_api_v1)


@app.on_event('startup')
async def on_startup():
    loop = asyncio.get_running_loop()
    logger.info('Setup ThreadPoolExecutor: max_workers=%s', settings.THREADS)
    loop.set_default_executor(default_executor)


@app.middleware('http')
async def django_request_signals(request: Request, call_next):
    await sync_to_async(request_started.send)(sender=app.__class__, scope=request.scope)

    try:
        response = await call_next(request)
    finally:
        await sync_to_async(request_finished.send)(sender=app.__class__, scope=request.scope)

    return response


app.mount('/app', get_django_asgi_app())
app.mount(
    '/static',
    app=StaticFiles(directory=settings.STATIC_ROOT.as_posix(), check_dir=False),
    name='staticfiles',
)


@app.get('/', include_in_schema=False)
def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse('/docs')
