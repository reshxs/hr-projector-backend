import datetime as dt
import pytest
from hr import factories
from hr import security
from dirty_equals import IsStr


pytestmark = [
    pytest.mark.django_db(transaction=True)
]


def test_unregistered(auth_request, user):
    user.delete()

    resp = auth_request(
        'login',
        {
            'credentials': {
                'email': 'unregistered@example.com',
                'password': 'unregistered',
            },
        },
    )

    assert resp.get('error') == {
        'code': 403,
        'message': 'forbidden',
    }


def test_wrong_password(auth_request):
    user = factories.UserFactory.create(raw_password='password')

    resp = auth_request(
        'login',
        {
            'credentials': {
                'email': user.email,
                'password': 'wrong_password',
            },
        },
    )

    assert resp.get('error') == {
        'code': 403,
        'message': 'forbidden',
    }


def test_ok(auth_request, freezer, settings):
    now = dt.datetime.now()

    raw_password = 'test_password'
    user = factories.UserFactory.create(raw_password=raw_password)

    resp = auth_request(
        'login',
        {
            'credentials': {
                'email': user.email,
                'password': raw_password,
            },
        },
    )

    assert resp.get('result') == {
        'token': IsStr,
    }, resp.get('error')

    token = resp['result'].get('token')
    actual_token = security.decode_jwt(token)
    assert actual_token.user_id == user.id
    # TODO: проверять время жизни токена
