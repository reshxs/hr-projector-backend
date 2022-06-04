import pytest
from dirty_equals import IsPartialDict
from django.forms import model_to_dict

from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


def test_ok(jsonrpc_request, user):
    resume = factories.ResumeFactory.create(
        user=user,
        current_position='Тестировщик',
        desired_position='Разработчик',
        experience=3,
        bio='old_bio',
    )

    skill = factories.SkillFactory.create(name='testing')
    resume.skills.add(skill)
    resume.save()

    assert resume.state == models.ResumeState.DRAFT

    resp = jsonrpc_request(
        'update_resume',
        {
            'id': resume.id,
            'content': {
                'current_position': 'QA инженер',
                'desired_position': 'Руководитель разработки',
                'experience': 4,
                'bio': 'new_bio',
                'skills': [
                    'python',
                ],
            },
        },
    )

    assert resp.get('result') == IsPartialDict(
        {
            'id': resume.id,
            'state': 'DRAFT',
            'current_position': 'QA инженер',
            'desired_position': 'Руководитель разработки',
            'experience': 4,
            'bio': 'new_bio',
            'skills': [
                'python',
            ],
        },
    ), resp.get('error')

    resume.refresh_from_db()
    assert resume.current_position == 'QA инженер'
    assert resume.desired_position == 'Руководитель разработки'
    assert resume.experience == 4
    assert resume.bio == 'new_bio'
    assert ['python'] == [
        skill.name for skill in resume.skills.all()
    ]


def test_resume_not_draft__wrong_state_error(jsonrpc_request, user):
    resume = factories.ResumeFactory.create(
        user=user,
        published=True,
    )
    old_resume = model_to_dict(resume)

    resp = jsonrpc_request(
        'update_resume',
        {
            'id': resume.id,
            'content': {
                'current_position': 'Разработчик',
            },
        },
    )

    assert resp.get('error') == {'code': 3002, 'message': 'Resume has not allowed state for this method'}

    resume.refresh_from_db()
    actual_resume = model_to_dict(resume)
    assert old_resume == actual_resume


def test_resume_does_not_exists__not_found_error(jsonrpc_request):
    assert models.Resume.objects.count() == 0

    resp = jsonrpc_request(
        'update_resume',
        {
            'id': 1,
            'content': {
                'current_position': 'Разработчик',
            },
        },
    )

    assert resp.get('error') == {'code': 3001, 'message': 'Resume not found'}


def test_other_user_resume__not_found_error(jsonrpc_request, user):
    resume = factories.ResumeFactory.create()
    assert resume.user_id != user.id

    old_resume = model_to_dict(resume)

    resp = jsonrpc_request(
        'update_resume',
        {
            'id': resume.id,
            'content': {
                'current_position': 'Разработчик',
            },
        },
    )

    assert resp.get('error') == {'code': 3001, 'message': 'Resume not found'}

    resume.refresh_from_db()
    actual_resume = model_to_dict(resume)
    assert old_resume == actual_resume
