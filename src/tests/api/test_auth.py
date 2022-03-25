import functools
import datetime as dt
import pytest

from hr import security

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


@pytest.fixture()
def jsonrpc_request(api_client, requests_mock):
    # Переопределяем основную фикстуру, так как та автоматически проставляет авторизацию
    requests_mock.register_uri('POST', 'http://testserver/api/v1/web/jsonrpc', real_http=True)

    return functools.partial(api_client.api_jsonrpc_request, url='/api/v1/web/jsonrpc')


def test_forbidden(jsonrpc_request):
    resp = jsonrpc_request('test_auth', use_auth=False)
    assert resp.get('error') == {
        'code': 403,
        'message': 'forbidden',
    }


def test_token_expired(freezer, settings, jsonrpc_request, auth_user_id):
    now = dt.datetime.now()

    token = security.encode_jwt(auth_user_id)

    token_expired_date = now + settings.JWT_EXPIRATION_INTERVAL + dt.timedelta(minutes=1)
    freezer.move_to(token_expired_date)

    resp = jsonrpc_request('test_auth', auth_token=token)
    assert resp.get('error') == {
        'code': 403,
        'message': 'forbidden',
    }


def test_ok(jsonrpc_request, auth_user, auth_user_token):
    resp = jsonrpc_request('test_auth', auth_token=auth_user_token)
    assert resp.get('result') == f'Hello, {auth_user.full_name}', resp.get('error')
