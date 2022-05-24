import datetime as dt
import pytest
from hr import factories
from hr import security
from dirty_equals import IsStr


pytestmark = [
    pytest.mark.django_db(transaction=True)
]


def test_unregistered(jsonrpc_request, user):
    user.delete()

    resp = jsonrpc_request(
        'login',
        {
            'credentials': {
                'email': 'unregistered@example.com',
                'password': 'unregistered',
            },
        },
        use_auth=False,
    )

    assert resp.get('error') == {
        'code': 403,
        'message': 'forbidden',
    }


def test_wrong_password(jsonrpc_request):
    user = factories.UserFactory.create(raw_password='password')

    resp = jsonrpc_request(
        'login',
        {
            'credentials': {
                'email': user.email,
                'password': 'wrong_password',
            },
        },
        use_auth=False,
    )

    assert resp.get('error') == {
        'code': 403,
        'message': 'forbidden',
    }


def test_ok(jsonrpc_request, freezer, settings):
    now = dt.datetime.now()

    raw_password = 'test_password'
    user = factories.UserFactory.create(raw_password=raw_password)

    resp = jsonrpc_request(
        'login',
        {
            'credentials': {
                'email': user.email,
                'password': raw_password,
            },
        },
        use_auth=False,
    )

    assert resp.get('result') == {
        'token': IsStr,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'patronymic': user.patronymic,
            'department': {
                'id': user.department.id,
                'name': user.department.name,
            },
            'role': user.role,
        }
    }, resp.get('error')

    token = resp['result'].get('token')
    actual_token = security.decode_jwt(token)
    assert actual_token.user_id == user.id
    # TODO: проверять время жизни токена
