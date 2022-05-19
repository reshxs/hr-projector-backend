import pytest
from dirty_equals import IsListOrTuple
from dirty_equals import IsPartialDict


from hr import factories
from hr import models


pytestmark = [
    pytest.mark.django_db(transaction=True),
]


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_ok(jsonrpc_request, user):
    applicants = factories.UserFactory.create_batch(3, role=models.UserRole.APPLICANT)
    factories.UserFactory.create_batch(3, role=models.UserRole.MANAGER)  # managers

    resp = jsonrpc_request(
        'get_applicants_for_manager',
        {
            'pagination': {
                'count': True,
            },
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'items': IsListOrTuple(
            *[
                {
                    'id': applicant.id,
                    'email': applicant.email,
                    'full_name': applicant.full_name,
                    'department': {
                        'id': applicant.department.id,
                        'name': applicant.department.name,
                    },
                }
                for applicant in applicants
            ],
            check_order=False,
        ),
        'total_size': 3,
    }, resp.get('error')


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
@pytest.mark.parametrize(
    'search_param',
    [
        'Иванов Василий Вячеславович',
        'иванов василий',
        'василий Вячеславович',
        'Иванов',
        'Василий',
        'Вячеславович',
        'иванов',
        'сили',
    ]
)
def test_search_by_full_name(jsonrpc_request, user, search_param):
    expected_applicant = factories.UserFactory(
        role=models.UserRole.APPLICANT,
        last_name='Иванов',
        first_name='Василий',
        patronymic='Вячеславович',
    )

    factories.UserFactory(
        role=models.UserRole.APPLICANT,
        last_name='Петров',
        first_name='Григорий',
        patronymic='Русланович',
    )

    resp = jsonrpc_request(
        'get_applicants_for_manager',
        {
            'pagination': {
                'count': True,
            },
            'filters': {
                'full_name': search_param,
            },
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'total_size': 1,
        'items': [
            IsPartialDict(
                {
                    'id': expected_applicant.id,
                    'full_name': expected_applicant.full_name,
                },
            ),
        ],
    }


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
@pytest.mark.parametrize(
    'search_param',
    [
        'expected@example.com',
        'expected',
        'example.com',
        'pected',
    ]
)
def test_search_by_email(jsonrpc_request, user, search_param):
    expected_applicant = factories.UserFactory.create(
        role=models.UserRole.APPLICANT,
        email='expected@example.com',
    )
    factories.UserFactory.create(
        role=models.UserRole.APPLICANT,
        email='otheruser@test.ru',
    )  # unexpected_user

    resp = jsonrpc_request(
        'get_applicants_for_manager',
        {
            'pagination': {
                'count': True,
            },
            'filters': {
                'email': search_param,
            },
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'total_size': 1,
        'items': [
            IsPartialDict(
                {
                    'id': expected_applicant.id,
                    'email': expected_applicant.email,
                },
            ),
        ],
    }


@pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
def test_search_by_department(jsonrpc_request, user):
    expected_applicant = factories.UserFactory.create(
        role=models.UserRole.APPLICANT,
    )
    unexpected_applicant = factories.UserFactory.create(
        role=models.UserRole.APPLICANT,
    )

    assert expected_applicant.department != unexpected_applicant.department

    resp = jsonrpc_request(
        'get_applicants_for_manager',
        {
            'pagination': {
                'count': True,
            },
            'filters': {
                'department_ids': [expected_applicant.department.id],
            },
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'total_size': 1,
        'items': [
            IsPartialDict(
                {
                    'id': expected_applicant.id,
                    'department': {
                        'id': expected_applicant.department.id,
                        'name': expected_applicant.department.name,
                    },
                },
            ),
        ],
    }
