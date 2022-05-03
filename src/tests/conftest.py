import asyncio
import datetime
import platform

import fastapi_jsonrpc
import freezegun
import requests_mock.response
import simplejson
from asgiref.sync import sync_to_async

requests_mock.response.jsonutils = simplejson
requests_mock.response.json = simplejson


if platform.system() == 'Darwin':
    import socket

    socket.gethostbyname = lambda x: '127.0.0.1'


def patched_freezgun_astimezone(self, tz=None):
    from freezegun.api import datetime_to_fakedatetime
    from freezegun.api import real_datetime

    if tz is None:
        from freezegun.api import tzlocal

        tz = tzlocal()

    real = self
    if real.tzinfo is None:
        # we work with naive UTC date time
        # to correct converting make it aware
        mytz = datetime.timezone(self._tz_offset())
        real = self.replace(tzinfo=mytz)

    return datetime_to_fakedatetime(real_datetime.astimezone(real, tz))


def patched_freezegun_now(cls, tz=None):
    from freezegun.api import datetime_to_fakedatetime
    from freezegun.api import real_datetime

    now = cls._time_to_freeze() or real_datetime.now()

    result = now + cls._tz_offset()
    result = datetime_to_fakedatetime(result)

    if tz:
        result = cls.astimezone(result, tz)

    return result


# https://github.com/spulec/freezegun/issues/348#issuecomment-674549390
freezegun.api.FakeDatetime.astimezone = patched_freezgun_astimezone
freezegun.api.FakeDatetime.now = classmethod(patched_freezegun_now)


# Запускаем в главном потоке, а не в пуле, иначе будет требоваться transactional_db, и тесты будут выполняться долго
async def mock_call_sync_async(call, *args, **kwargs):
    is_coroutine = asyncio.iscoroutinefunction(call)
    if is_coroutine:
        return await call(*args, **kwargs)
    else:
        return await sync_to_async(call)(*args, **kwargs)


fastapi_jsonrpc.call_sync_async = mock_call_sync_async


pytest_plugins = [
    'tests.fixtures.fixtures',
    'tests.fixtures.const',
]