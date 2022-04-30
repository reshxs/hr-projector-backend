import pytest
from dirty_equals import AnyThing
from hr import models
from django.utils import timezone

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


def test_ok(auth_user, jsonrpc_request, freezer):
    assert models.Resume.objects.count() == 0

    content = 'Dummy resume content'
    resp = jsonrpc_request(
        'add_resume',
        {
            'content': content,
        },
    )

    assert models.Resume.objects.count() == 1
    resume = models.Resume.objects.first()

    assert resp.get('result') == {
        'id': resume.id,
        'state': 'DRAFT',
        'content': content,
        'created_at': AnyThing,  # FIXME: сравнивать с нормальной timezone
        'published_at': None,
    }, resp.get('error')

    assert resume.user == auth_user
    assert resume.content == content
    assert resume.state == models.ResumeState.DRAFT
    assert resume.created_at == timezone.now()
    assert resume.published_at is None


def test_manager_user__forbidden(auth_user, jsonrpc_request):
    auth_user.is_manager = True
    auth_user.save()

    assert models.Resume.objects.count() == 0

    resp = jsonrpc_request(
        'add_resume',
        {
            'content': 'content',
        },
    )

    assert resp.get('error') == {'code': 403, 'message': 'forbidden'}
    assert models.Resume.objects.count() == 0
