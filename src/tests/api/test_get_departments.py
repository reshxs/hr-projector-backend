import pytest
import functools
from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


@pytest.fixture()
def jsonrpc_request(transactional_db, api_client, requests_mock):
    # Переопределяем стандартный jsonrpc_request, так как, тот создает департамент в базе, что мешает тестированию.
    requests_mock.register_uri('POST', 'http://testserver/api/v1/web/jsonrpc', real_http=True)

    return functools.partial(api_client.api_jsonrpc_request, url='/api/v1/web/jsonrpc')


def test_get_departments(jsonrpc_request):
    first = factories.DepartmentFactory.create(name='Аналитика')
    second = factories.DepartmentFactory.create(name='Бизнес')
    third = factories.DepartmentFactory.create(name='Разработка')

    assert models.Department.objects.count() == 3

    resp = jsonrpc_request('get_departments', use_auth=False)
    assert resp.get('result') == [
        {
            'id': first.id,
            'name': first.name,
        },
        {
            'id': second.id,
            'name': second.name,
        },
        {
            'id': third.id,
            'name': third.name,
        },
    ], resp.get('error')

