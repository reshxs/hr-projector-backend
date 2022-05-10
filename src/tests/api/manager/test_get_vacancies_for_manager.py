import pytest

from dirty_equals import IsListOrTuple

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
    }
