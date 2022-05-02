import pytest
from django.utils import timezone

from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


def test_ok(jsonrpc_request, auth_user, freezer):
    resume = factories.ResumeFactory.create(user=auth_user)
    assert resume.state == models.ResumeState.DRAFT
    assert resume.published_at is None

    resp = jsonrpc_request(
        'publish_resume',
        {
            'id': resume.id,
        },
    )

    assert resp.get('result') == {
        'id': resume.id,
        'state': 'PUBLISHED',
        'content': resume.content,
        'created_at': resume.created_at.isoformat(),
        'published_at': timezone.now().isoformat(),
    }, resp.get('error')

    resume.refresh_from_db()
    assert resume.state == models.ResumeState.PUBLISHED
    assert resume.published_at == timezone.now()


def test_resume__does_not_exists__not_found(jsonrpc_request):
    assert models.Resume.objects.count() == 0

    resp = jsonrpc_request(
        'publish_resume',
        {
            'id': 1,
        },
    )

    assert resp.get('error') == {'code': 3001, 'message': 'Resume not found'}


def test_other_user_resume__not_found(jsonrpc_request, auth_user):
    resume = factories.ResumeFactory.create()
    assert resume.user_id != auth_user.id

    resp = jsonrpc_request(
        'publish_resume',
        {
            'id': resume.id,
        },
    )

    assert resp.get('error') == {'code': 3001, 'message': 'Resume not found'}

