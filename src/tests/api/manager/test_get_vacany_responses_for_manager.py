import pytest

from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True)
]


def test_ok(jsonrpc_request, user):
    expected_responses = factories.VacancyResponseFactory.create_batch(3, vacancy__creator=user)
    factories.VacancyResponseFactory.create_batch(3)  # unexpected

    resp = jsonrpc_request(
        'get_vacancy_responses_for_manager',
        {
            'pagination': {
                'count': True,
            },
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'total_size': 3,
        'items': [
            {
                'id': vacancy_response.id,
                'vacancy': {
                    'id': vacancy_response.vacancy.id,
                    'creator_id': vacancy_response.vacancy.creator.id,
                    'creator_full_name': vacancy_response.vacancy.creator.full_name,
                    'creator_contact': vacancy_response.vacancy.creator.email,
                    'department_id': vacancy_response.vacancy.creator.department.id,
                    'department_name': vacancy_response.vacancy.creator.department.name,
                    'position': vacancy_response.vacancy.position,
                    'experience': vacancy_response.vacancy.experience,
                    'description': vacancy_response.vacancy.description,
                    'published_at': vacancy_response.vacancy.published_at.isoformat(),
                },
                'resume': {
                    'applicant': {
                        'department': {
                            'id': vacancy_response.resume.user.department.id,
                            'name': vacancy_response.resume.user.department.name,
                        },
                        'email': vacancy_response.resume.user.email,
                        'full_name': vacancy_response.resume.user.full_name,
                        'id': vacancy_response.resume.user_id,
                    },
                    'bio': vacancy_response.resume.bio,
                    'current_position': vacancy_response.resume.current_position,
                    'desired_position': vacancy_response.resume.desired_position,
                    'experience': vacancy_response.resume.experience,
                    'id': vacancy_response.resume.id,
                    'skills': [skill.name for skill in vacancy_response.resume.skills.all()],
                },
                'applicant_message': vacancy_response.applicant_message,
            }
            for vacancy_response in expected_responses
        ]
    }, resp.get('error')

