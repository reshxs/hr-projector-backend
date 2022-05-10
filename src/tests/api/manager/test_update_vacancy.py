import pytest
from django.forms import model_to_dict

from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True),
]


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test__ok(user: models.User, jsonrpc_request):
    vacancy = factories.VacancyFactory.create(
        creator=user,
        position='analytics',
        experience=None,
        description='business analytics',
    )

    assert vacancy.state == models.VacancyState.DRAFT

    resp = jsonrpc_request(
        'update_vacancy',
        {
            'id': vacancy.id,
            'new_data': {
                'position': 'developer',
                'experience': 4,
                'description': 'python developer',
            },
        },
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
        'position': 'developer',
        'experience': 4,
        'description': 'python developer',
        'published_at': None,
    }, resp.get('error')

    vacancy.refresh_from_db()
    assert vacancy.position == 'developer'
    assert vacancy.experience == 4
    assert vacancy.description == 'python developer'


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
@pytest.mark.parametrize(
    'vacancy_trait',
    [
        {'published': True},
        {'hidden': True},
    ],
)
def test_non_draft_vacancy__wrong_state_error(user: models.User, jsonrpc_request, vacancy_trait):
    vacancy = factories.VacancyFactory.create(**vacancy_trait, creator=user)

    resp = jsonrpc_request(
        'update_vacancy',
        {
            'id': vacancy.id,
            'new_data': {
                'position': 'developer',
                'experience': 4,
                'description': 'python developer',
            },
        },
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
        'update_vacancy',
        {
            'id': vacancy.id,
            'new_data': {
                'position': 'developer',
                'experience': 4,
                'description': 'python developer',
            },
        },
    )

    assert resp.get('error') == {'code': 4001, 'message': 'Vacancy not found'}

    old_vacancy = model_to_dict(vacancy)

    vacancy.refresh_from_db()
    actual_vacancy = model_to_dict(vacancy)

    assert actual_vacancy == old_vacancy


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_vacancy_not_exist__not_found_error(user: models.User, jsonrpc_request):
    assert models.Vacancy.objects.count() == 0

    resp = jsonrpc_request(
        'update_vacancy',
        {
            'id': 1,
            'new_data': {
                'position': 'developer',
                'experience': 4,
                'description': 'python developer',
            },
        },
    )

    assert resp.get('error') == {'code': 4001, 'message': 'Vacancy not found'}
