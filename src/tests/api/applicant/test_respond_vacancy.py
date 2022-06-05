import pytest
from dirty_equals import IsInt

from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True),
]


def test_ok(jsonrpc_request, user, freezer):
    vacancy = factories.VacancyFactory.create(published=True)
    resume = factories.ResumeFactory.create(user=user, published=True)

    resp = jsonrpc_request(
        'respond_vacancy',
        {
            'vacancy_id': vacancy.id,
            'resume_id': resume.id,
            'message': 'test_message',
        }
    )

    assert resp.get('result') == {
        'id': IsInt,
        'vacancy': {
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
        },
        'resume': {
                'applicant': {
                    'department': {
                        'id': resume.user.department.id,
                        'name': resume.user.department.name,
                    },
                    'email': resume.user.email,
                    'full_name': resume.user.full_name,
                    'id': resume.user_id,
                },
                'bio': resume.bio,
                'current_position': resume.current_position,
                'desired_position': resume.desired_position,
                'experience': resume.experience,
                'id': resume.id,
                'skills': [skill.name for skill in resume.skills.all()],
        },
        'applicant_message': 'test_message',
    }


def test_vacancy_does_not_exists_error(jsonrpc_request, user):
    resume = factories.ResumeFactory.create(published=True, user=user)
    assert models.Vacancy.objects.count() == 0

    resp = jsonrpc_request(
        'respond_vacancy',
        {
            'vacancy_id': 1,
            'resume_id': resume.id,
        }
    )

    assert resp.get('error') == {'code': 4001, 'message': 'Vacancy not found'}


def test_vacancy_not_published_error(jsonrpc_request, user):
    resume = factories.ResumeFactory.create(published=True, user=user)
    vacancy = factories.VacancyFactory.create()  # DRAFT

    resp = jsonrpc_request(
        'respond_vacancy',
        {
            'vacancy_id': vacancy.id,
            'resume_id': resume.id,
        }
    )

    assert resp.get('error') == {'code': 4001, 'message': 'Vacancy not found'}


def test_resume_does_not_exists_error(jsonrpc_request):
    assert models.Resume.objects.count() == 0
    vacancy = factories.VacancyFactory.create(published=True)

    resp = jsonrpc_request(
        'respond_vacancy',
        {
            'vacancy_id': vacancy.id,
            'resume_id': 1,
        }
    )

    assert resp.get('error') == {'code': 3001, 'message': 'Resume not found'}


def test_resume_wrong_state_error(jsonrpc_request, user):
    resume = factories.ResumeFactory.create(user=user)  # DRAFT
    vacancy = factories.VacancyFactory.create(published=True)

    resp = jsonrpc_request(
        'respond_vacancy',
        {
            'vacancy_id': vacancy.id,
            'resume_id': resume.id,
        }
    )

    assert resp.get('error') == {'code': 3002, 'message': 'Resume has not allowed state for this method'}


def test_other_user_resume_error(jsonrpc_request, user):
    resume = factories.ResumeFactory.create(published=True)
    assert resume.user != user

    vacancy = factories.VacancyFactory.create(published=True)

    resp = jsonrpc_request(
        'respond_vacancy',
        {
            'vacancy_id': vacancy.id,
            'resume_id': resume.id,
        }
    )

    assert resp.get('error') == {'code': 3001, 'message': 'Resume not found'}


def test_already_created_error(jsonrpc_request, user):
    resume = factories.ResumeFactory.create(published=True, user=user)
    vacancy = factories.VacancyFactory.create(published=True)

    models.VacancyResponse.objects.create(resume=resume, vacancy=vacancy)

    resp = jsonrpc_request(
        'respond_vacancy',
        {
            'vacancy_id': vacancy.id,
            'resume_id': resume.id,
        }
    )

    assert resp.get('error') == {'code': 5003, 'message': 'Vacancy response already exists'}
