import pytest


from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True),
]


def test_ok(jsonrpc_request, user):
    vacancy = factories.VacancyFactory.create(published=True)

    resp = jsonrpc_request(
        'get_vacancy_for_applicant',
        {
            'id': vacancy.id,
        },
    )

    assert resp.get('result') == {
        'id': vacancy.id,
        'creator_id': vacancy.creator.id,
        'creator_full_name': vacancy.creator.full_name,
        'creator_contact': vacancy.creator.email,
        'department_id': vacancy.creator.department.id,
        'department_name': vacancy.creator.department.name,
        'position': vacancy.position,
        'experience': vacancy.experience,
        'description': vacancy.description,
        'published_at': vacancy.published_at.isoformat(),
    }, resp.get('error')


@pytest.mark.parametrize(
    'vacancy_trait',
    [
        {},
        {'hidden': True},
    ]
)
def test_not_published_vacancy__not_found_error(
    jsonrpc_request,
    user,
    vacancy_trait,
):
    vacancy = factories.VacancyFactory.create(**vacancy_trait)

    resp = jsonrpc_request(
        'get_vacancy_for_applicant',
        {
            'id': vacancy.id,
        },
    )

    assert resp.get('error') == {'code': 4001, 'message': 'Vacancy not found'}


def test_not_exist_vacancy__not_found_error(
    jsonrpc_request,
    user,
):
    assert models.Vacancy.objects.count() == 0

    resp = jsonrpc_request(
        'get_vacancy_for_applicant',
        {
            'id': 1,
        },
    )

    assert resp.get('error') == {'code': 4001, 'message': 'Vacancy not found'}
