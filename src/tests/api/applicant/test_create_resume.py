import pytest
from hr import models
from django.utils import timezone

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


def test_ok(user, jsonrpc_request, freezer):
    assert models.Resume.objects.count() == 0

    content = 'Dummy applicant content'
    resp = jsonrpc_request(
        'create_resume',
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
        'created_at': resume.created_at.isoformat(),  # FIXME: с  помощью freezer явно проверять, что время == now
        'published_at': None,
    }, resp.get('error')

    assert resume.user == user
    assert resume.content == content
    assert resume.state == models.ResumeState.DRAFT
    assert resume.created_at == timezone.now().astimezone()
    assert resume.published_at is None
