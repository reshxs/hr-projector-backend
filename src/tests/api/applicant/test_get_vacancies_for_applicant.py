import pytest
from dirty_equals import IsListOrTuple
from dirty_equals import IsPartialDict

from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True),
]


def test_ok(jsonrpc_request):
    vacancies = factories.VacancyFactory.create_batch(3, published=True)
    factories.VacancyFactory.create_batch(3, hidden=True)  # unexpected (hidden)
    factories.VacancyFactory.create_batch(3)  # unexpected (draft)

    resp = jsonrpc_request(
        'get_vacancies_for_applicant',
        {
            'pagination': {
                'count': True,
            },
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'total_size': 3,
        'items': IsListOrTuple(
            *[
                {
                    'id': vacancy.id,
                    'creator_id': vacancy.creator.id,
                    'creator_full_name': vacancy.creator.full_name,
                    'department_id': vacancy.creator.department.id,
                    'department_name': vacancy.creator.department.name,
                    'position': vacancy.position,
                    'experience': vacancy.experience,
                    'published_at': vacancy.published_at.isoformat()
                }
                for vacancy in vacancies
            ],
            check_order=False,
        ),
    }, resp.get('error')


def test_filter_by_department(jsonrpc_request):
    expected_department = factories.DepartmentFactory.create()
    expected_vacancy = factories.VacancyFactory.create(
        creator__department=expected_department,
        published=True,
    )
    factories.VacancyFactory.create(published=True)  # unexpected

    assert models.Vacancy.objects.count() == 2

    resp = jsonrpc_request(
        'get_vacancies_for_applicant',
        {
            'filters': {
                'department_ids': [expected_department.id],
            },
            'pagination': {
                'count': True,
            },
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'items': [
            IsPartialDict(
                {
                    'id': expected_vacancy.id,
                    'department_id': expected_department.id,
                },
            )
        ],
        'total_size': 1,
    }, resp.get('error')


@pytest.mark.parametrize(
    'position_param',
    [
        'Разработчик',
        'разработчик',
        'разраб',
        'раз',
        'ботчик',
    ]
)
def test_filter_by_position(jsonrpc_request, position_param):
    expected_vacancy = factories.VacancyFactory.create(
        position='Разработчик',
        published=True,
    )
    factories.VacancyFactory.create(
        position='Аналитик',
        published=True,
    )  # unexpected

    assert models.Vacancy.objects.count() == 2

    resp = jsonrpc_request(
        'get_vacancies_for_applicant',
        {
            'filters': {
                'position': position_param,
            },
            'pagination': {
                'count': True,
            },
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'items': [
            IsPartialDict(
                {
                    'id': expected_vacancy.id,
                    'position': 'Разработчик',
                },
            )
        ],
        'total_size': 1,
    }, resp.get('error')


def test_filter_by_experience(jsonrpc_request):
    lower_bound = factories.VacancyFactory.create(experience=2, published=True)
    between_bounds = factories.VacancyFactory.create(experience=3, published=True)
    upper_bound = factories.VacancyFactory.create(experience=4, published=True)
    factories.VacancyFactory.create(experience=1, published=True)  # less_lower_bound
    factories.VacancyFactory.create(experience=6, published=True)  # greater_lower_bound

    assert models.Vacancy.objects.count() == 5

    resp = jsonrpc_request(
        'get_vacancies_for_applicant',
        {
            'filters': {
                'experience_lte': 4,
                'experience_gte': 2,
            },
            'pagination': {
                'count': True,
            },
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'items': IsListOrTuple(
            *[
                IsPartialDict(
                    {
                        'id': vacancy.id,
                        'experience': vacancy.experience,
                    },
                )
                for vacancy in (lower_bound, between_bounds, upper_bound)
            ],
            check_order=False,
        ),
        'total_size': 3,
    }, resp.get('error')


def test_filter_by_published_at(jsonrpc_request, freezer):
    freezer.move_to('2022-05-07')
    factories.VacancyFactory.create(published=True)  # too_old

    freezer.move_to('2022-05-08')
    lower_bound = factories.VacancyFactory.create(published=True)

    freezer.move_to('2022-05-09')
    between_bounds = factories.VacancyFactory.create(published=True)

    freezer.move_to('2022-05-10')
    upper_bound = factories.VacancyFactory.create(published=True)

    freezer.move_to('2022-05-11')
    factories.VacancyFactory.create(published=True)  # too_young

    resp = jsonrpc_request(
        'get_vacancies_for_applicant',
        {
            'filters': {
                'published_lte': '2022-05-10',
                'published_gte': '2022-05-08',
            },
            'pagination': {
                'count': True,
            },
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'items': IsListOrTuple(
            *[
                IsPartialDict(
                    {
                        'id': vacancy.id,
                        'published_at': vacancy.published_at.isoformat(),
                    },
                )
                for vacancy in (lower_bound, between_bounds, upper_bound)
            ],
            check_order=False,
        ),
        'total_size': 3,
    }, resp.get('error')
