import pytest
from django.utils import timezone

from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
@pytest.mark.parametrize('experience', [None, 3])
def test_ok(
    user: models.User,
    jsonrpc_request,
    freezer,
    experience,
):
    assert models.Vacancy.objects.count() == 0

    resp = jsonrpc_request(
        'create_vacancy',
        {
            'vacancy_data': {
                'position': 'developer',
                'description': 'python developer',
                'experience': experience,
            }
        }
    )

    assert models.Vacancy.objects.count() == 1
    vacancy = models.Vacancy.objects.last()

    assert vacancy.creator == user
    assert vacancy.state == models.VacancyState.DRAFT
    assert vacancy.position == 'developer'
    assert vacancy.experience == experience
    assert vacancy.description == 'python developer'
    assert vacancy.created_at == timezone.now()
    assert vacancy.published_at is None

    assert resp.get('result') == {
        'id': vacancy.id,
        'state': 'DRAFT',
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
            'role': 'MANAGER'
        },
        'position': 'developer',
        'description': 'python developer',
        'experience': experience,
        'published_at': None,
    }, resp.get('error')
