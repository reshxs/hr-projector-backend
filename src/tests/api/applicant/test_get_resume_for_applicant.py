import pytest

from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


def test_get_resume_for_applicant__ok(jsonrpc_request, user):
    resume = factories.ResumeFactory.create(user=user)
    skill = factories.SkillFactory.create()
    resume.skills.add(skill)
    resume.save()

    resp = jsonrpc_request(
        'get_resume_for_applicant',
        {
            'id': resume.id,
        }
    )

    assert resp.get('result') == {
        'id': resume.id,
        'state': resume.state.value,
        'current_position': resume.current_position,
        'desired_position': resume.desired_position,
        'skills': [skill.name],
        'experience': resume.experience,
        'bio': resume.bio,
        'created_at': resume.created_at.isoformat(),
        'published_at': resume.published_at,
    }, resp.get('error')


def test_get_resume_for_applicant__other_user__not_found(jsonrpc_request):
    resume = factories.ResumeFactory.create()

    resp = jsonrpc_request(
        'get_resume_for_applicant',
        {
            'id': resume.id,
        }
    )

    assert resp.get('error') == {'code': 3001, 'message': 'Resume not found'}


def test_get_resume_for_applicant__not_exists__not_found(jsonrpc_request):
    assert models.Resume.objects.count() == 0

    resp = jsonrpc_request(
        'get_resume_for_applicant',
        {
            'id': 1,
        }
    )

    assert resp.get('error') == {'code': 3001, 'message': 'Resume not found'}