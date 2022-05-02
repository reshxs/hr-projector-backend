import functools
import pytest
import simplejson as json

from starlette.testclient import TestClient


@pytest.fixture(autouse=True, scope='session')
def _init_django():
    import os

    import django

    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    django.setup()


class ApiClient(TestClient):
    def api_jsonrpc_request(
        self,
        method: str,
        params: dict = None,
        *,
        url: str,
        use_decimal: bool = True,
        headers: dict = None,
        cookies: dict = None,
        use_auth: bool = True,
        auth_token: str = None
    ):
        headers = headers or {}
        cookies = cookies or {}

        if use_auth and auth_token is not None:
            headers['Authorization'] = f'bearer {auth_token}'

        resp = self.post(
            url=url,
            data=json.dumps(
                {
                    'id': 0,
                    'jsonrpc': '2.0',
                    'method': method,
                    'params': params or {},
                }
            ),
            headers=headers,
            cookies=cookies,
        )

        return resp.json(use_decimal=use_decimal)


@pytest.fixture()
def api_app():
    import hr.app

    return hr.app.app


@pytest.fixture()
def api_client(
    api_app,
):
    client = ApiClient(api_app)
    return client


@pytest.fixture()
def jsonrpc_request(transactional_db, api_client, requests_mock, auth_user_token):
    requests_mock.register_uri('POST', 'http://testserver/api/v1/web/jsonrpc', real_http=True)

    return functools.partial(api_client.api_jsonrpc_request, url='/api/v1/web/jsonrpc', auth_token=auth_user_token)


@pytest.fixture()
def auth_request(transactional_db, api_client, requests_mock):
    requests_mock.register_uri('POST', 'http://testserver/api/v1/auth/jsonrpc', real_http=True)

    return functools.partial(api_client.api_jsonrpc_request, url='/api/v1/auth/jsonrpc')
