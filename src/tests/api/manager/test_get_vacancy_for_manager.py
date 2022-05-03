import pytest
from dirty_equals import IsPartialDict
from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True),
]


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_ok(user: models.User, jsonrpc_request):
    vacancy = factories.VacancyFactory.create(creator=user)

    resp = jsonrpc_request(
        'get_vacancy_for_manager',
        {
            'id': vacancy.id,
        }
    )

    assert resp.get('result') == {
        'id': vacancy.id,
        'state': vacancy.state.value,
        'creator': {
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
        },
        'position': vacancy.position,
        'experience': vacancy.experience,
        'description': vacancy.description,
        'published_at': vacancy.published_at,
    }, resp.get('error')


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_get_vacancy_from_same_department__ok(user: models.User, jsonrpc_request):
    vacancy = factories.VacancyFactory.create(creator__department=user.department)

    resp = jsonrpc_request(
        'get_vacancy_for_manager',
        {
            'id': vacancy.id,
        }
    )

    assert resp.get('result') == IsPartialDict(
        {
            'id': vacancy.id,
            'state': 'DRAFT',
        }
    )


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_get_vacancy_from_other_department__not_found_error(user: models.User, jsonrpc_request):
    vacancy = factories.VacancyFactory.create()
    assert vacancy.creator.department_id != user.department_id

    resp = jsonrpc_request(
        'get_vacancy_for_manager',
        {
            'id': vacancy.id,
        }
    )

    assert resp.get('error') == {'code': 4001, 'message': 'Vacancy not found'}


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_vacancy_does_not_exists__not_found_error(user: models.User, jsonrpc_request):
    assert models.Vacancy.objects.count() == 0

    resp = jsonrpc_request(
        'get_vacancy_for_manager',
        {
            'id': 1,
        }
    )

    assert resp.get('error') == {'code': 4001, 'message': 'Vacancy not found'}