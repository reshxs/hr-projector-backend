import pytest


pytestmark = [
    pytest.mark.django_db(transaction=True),
]


def test_ok(jsonrpc_request, user):
    resp = jsonrpc_request('get_current_user')

    assert resp.get('result') == {
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
    }, resp.get('error')


def test_not_authorized__forbidden(jsonrpc_request):
    resp = jsonrpc_request('get_current_user', use_auth=False)
    assert resp.get('error') == {'code': 403, 'message': 'forbidden'}
