import functools
import datetime as dt
import pytest

from hr import security
from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


@pytest.fixture()
def jsonrpc_request(api_client, requests_mock):
    # Переопределяем основную фикстуру, так как та автоматически проставляет авторизацию
    requests_mock.register_uri('POST', 'http://testserver/api/v1/web/jsonrpc', real_http=True)

    return functools.partial(api_client.api_jsonrpc_request, url='/api/v1/web/jsonrpc')


def test_forbidden(jsonrpc_request):
    resp = jsonrpc_request(
        'create_resume',
        {'content': 'content'},
        use_auth=False,
    )
    assert resp.get('error') == {
        'code': 403,
        'message': 'forbidden',
    }


def test_token_expired(freezer, settings, jsonrpc_request, user):
    now = dt.datetime.now()

    token = security.encode_jwt(user)

    token_expired_date = now + settings.JWT_EXPIRATION_INTERVAL + dt.timedelta(minutes=1)
    freezer.move_to(token_expired_date)

    resp = jsonrpc_request(
        'create_resume',
        {'content': 'content'},
        auth_token=token,
    )
    assert resp.get('error') == {
        'code': 403,
        'message': 'forbidden',
    }


def test_ok(jsonrpc_request, user, user_token):
    resp = jsonrpc_request(
        'create_resume',
        {'content': 'content'},
        auth_token=user_token,
    )
    assert resp.get('error') is None


def test_not_allowed_role__forbidden(jsonrpc_request, freezer):
    user = factories.UserFactory.create(role=models.UserRole.MANAGER)
    token = security.encode_jwt(user)

    resp = jsonrpc_request(
        'create_resume',
        {
            'content': 'content',
        },
        auth_token=token,
    )

    assert resp.get('error') == {'code': 403, 'message': 'forbidden'}
