import pytest
from dirty_equals import IsListOrTuple
from dirty_equals import IsPartialDict

from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_ok(jsonrpc_request, user):
    vacancies = factories.VacancyFactory.create_batch(3, creator=user)
    factories.VacancyFactory.create_batch(3)  # unexpected_vacancies

    resp = jsonrpc_request(
        'get_vacancies_for_manager',
        {
            'pagination': {
                'count': True,
            }
        }
    )

    assert resp.get('result') == {
        'has_next': False,
        'items': IsListOrTuple(
            *[
                {
                    'creator_full_name': vacancy.creator.full_name,
                    'creator_id': vacancy.creator.id,
                    'id': vacancy.id,
                    'position': vacancy.position,
                    'published_at': None,
                    'state': vacancy.state.value,
                }
                for vacancy in vacancies
            ],
            check_order=False,
        ),
        'total_size': 3,
    }, resp.get('error')


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_filter_by_state(jsonrpc_request, user):
    draft = factories.VacancyFactory.create(creator=user)
    hidden = factories.VacancyFactory.create(creator=user, hidden=True)
    factories.VacancyFactory.create(creator=user, published=True)  # published

    resp = jsonrpc_request(
        'get_vacancies_for_manager',
        {
            'filters': {
                'states': ['DRAFT', 'HIDDEN'],
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
                        'state': vacancy.state.value,
                    },
                )
                for vacancy in (draft, hidden)
            ],
            check_order=False,
        ),
        'total_size': 2,
    }, resp.get('error')


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
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
def test_filter_by_position(jsonrpc_request, user, position_param):
    expected_vacancy = factories.VacancyFactory.create(creator=user, position='Разработчик')
    factories.VacancyFactory.create(creator=user, position='Аналитик')  # unexpected

    assert models.Vacancy.objects.count() == 2

    resp = jsonrpc_request(
        'get_vacancies_for_manager',
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


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_filter_by_experience(jsonrpc_request, user):
    lower_bound = factories.VacancyFactory.create(creator=user, experience=2)
    between_bounds = factories.VacancyFactory.create(creator=user, experience=3)
    upper_bound = factories.VacancyFactory.create(creator=user, experience=4)
    factories.VacancyFactory.create(creator=user, experience=1)  # less_lower_bound
    factories.VacancyFactory.create(creator=user, experience=6)  # greater_lower_bound

    assert models.Vacancy.objects.count() == 5

    resp = jsonrpc_request(
        'get_vacancies_for_manager',
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
                        # FIXME: добавить стаж в схему
                        # 'experience': vacancy.experience,
                    },
                )
                for vacancy in (lower_bound, between_bounds, upper_bound)
            ],
            check_order=False,
        ),
        'total_size': 3,
    }, resp.get('error')


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_filter_by_published_at(jsonrpc_request, user, freezer):
    freezer.move_to('2022-05-07')
    factories.VacancyFactory.create(creator=user, published=True)  # too_old

    freezer.move_to('2022-05-08')
    lower_bound = factories.VacancyFactory.create(creator=user, published=True)

    freezer.move_to('2022-05-09')
    between_bounds = factories.VacancyFactory.create(creator=user, published=True)

    freezer.move_to('2022-05-10')
    upper_bound = factories.VacancyFactory.create(creator=user, published=True)

    freezer.move_to('2022-05-11')
    factories.VacancyFactory.create(creator=user, published=True)  # too_young

    resp = jsonrpc_request(
        'get_vacancies_for_manager',
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

