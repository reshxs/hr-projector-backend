import pytest
from django.utils import timezone

from hr import factories
from hr import models
from libs.testing import model_to_dict

pytestmark = [
    pytest.mark.django_db(transaction=True),
]


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_ok(user: models.User, jsonrpc_request, freezer):
    vacancy = factories.VacancyFactory.create(creator=user, published=True)

    assert vacancy.state == models.VacancyState.PUBLISHED
    assert vacancy.published_at == timezone.now()

    resp = jsonrpc_request(
        'hide_vacancy',
        {
            'id': vacancy.id,
        }
    )

    assert resp.get('result') == {
        'id': vacancy.id,
        'state': 'HIDDEN',
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
        'published_at': None,
    }, resp.get('error')

    vacancy.refresh_from_db()
    assert vacancy.state == models.VacancyState.HIDDEN
    assert vacancy.published_at is None


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
@pytest.mark.parametrize(
    'vacancy_trait',
    [
        {},
        {'hidden': True},
    ]
)
def test_not_published_vacancy__wrong_state_error(user: models.User, jsonrpc_request, vacancy_trait):
    vacancy = factories.VacancyFactory.create(creator=user, **vacancy_trait)

    resp = jsonrpc_request(
        'hide_vacancy',
        {
            'id': vacancy.id,
        }
    )

    assert resp.get('error') == {'code': 4002, 'message': 'Vacancy has not allowed state for this method'}

    old_vacancy = model_to_dict(vacancy)
    vacancy.refresh_from_db()
    actual_vacancy = model_to_dict(vacancy)
    assert actual_vacancy == old_vacancy


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_other_user_vacancy__not_found_error(user: models.User, jsonrpc_request):
    vacancy = factories.VacancyFactory.create()
    assert vacancy.creator != user

    resp = jsonrpc_request(
        'hide_vacancy',
        {
            'id': vacancy.id,
        }
    )

    assert resp.get('error') == {'code': 4001, 'message': 'Vacancy not found'}

    old_vacancy = model_to_dict(vacancy)
    vacancy.refresh_from_db()
    actual_vacancy = model_to_dict(vacancy)
    assert actual_vacancy == old_vacancy


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_vacancy_not_exits__not_found_error(user: models.User, jsonrpc_request):
    assert models.Vacancy.objects.count() == 0

    resp = jsonrpc_request(
        'hide_vacancy',
        {
            'id': 1,
        }
    )

    assert resp.get('error') == {'code': 4001, 'message': 'Vacancy not found'}
