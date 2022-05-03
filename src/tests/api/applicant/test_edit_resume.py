import pytest
from dirty_equals import IsPartialDict

from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


def test_ok(jsonrpc_request, user):
    resume = factories.ResumeFactory.create(
        user=user,
        content='old_content',
    )

    assert resume.state == models.ResumeState.DRAFT

    new_content = 'new_content'
    resp = jsonrpc_request(
        'edit_resume',
        {
            'id': resume.id,
            'new_content': new_content,
        },
    )

    assert resp.get('result') == IsPartialDict(
        {
            'id': resume.id,
            'state': 'DRAFT',
            'content': new_content,
        },
    ), resp.get('error')

    resume.refresh_from_db()
    assert resume.content == new_content


def test_resume_not_draft__wrong_state_error(jsonrpc_request, user):
    old_content = 'old_content'

    resume = factories.ResumeFactory.create(
        user=user,
        published=True,
        content=old_content,
    )

    resp = jsonrpc_request(
        'edit_resume',
        {
            'id': resume.id,
            'new_content': 'new_content',
        },
    )

    assert resp.get('error') == {'code': 3002, 'message': 'Resume has not allowed state for this method'}

    resume.refresh_from_db()
    assert resume.content == old_content


def test_resume_does_not_exists__not_found_error(jsonrpc_request):
    assert models.Resume.objects.count() == 0

    resp = jsonrpc_request(
        'edit_resume',
        {
            'id': 1,
            'new_content': 'new_content',
        },
    )

    assert resp.get('error') == {'code': 3001, 'message': 'Resume not found'}


def test_other_user_resume__not_found_error(jsonrpc_request, user):
    old_content = 'old_content'

    resume = factories.ResumeFactory.create(content=old_content)
    assert resume.user_id != user.id

    resp = jsonrpc_request(
        'edit_resume',
        {
            'id': resume.id,
            'new_content': 'new_content',
        },
    )

    assert resp.get('error') == {'code': 3001, 'message': 'Resume not found'}

    resume.refresh_from_db()
    assert resume.content == old_content
