import pytest
from dirty_equals import IsPartialDict

from hr import factories
from hr import models
from testing import UnorderedList

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


def test_return_only_users_resumes(jsonrpc_request, auth_user):
    resumes = factories.ResumeFactory.create_batch(3, user=auth_user)
    factories.ResumeFactory.create_batch(3)  # other_user

    resp = jsonrpc_request(
        'get_resumes_for_applicant',
    )

    assert resp.get('result') == UnorderedList(
        [
            {
                'id': resume.id,
                'state': resume.state.value,
                'content': resume.content,
                'created_at': resume.created_at.isoformat(),
                'published_at': resume.published_at,
            }
            for resume in resumes
        ],
    ), resp.get('error')


def test_filter_by_id(jsonrpc_request, auth_user):
    expected_resumes = factories.ResumeFactory.create_batch(3, user=auth_user)
    factories.ResumeFactory.create_batch(3, user=auth_user)  # not expected resumes

    resp = jsonrpc_request(
        'get_resumes_for_applicant',
        {
            'filters': {
                'ids': [resume.id for resume in expected_resumes],
            },
        },
    )

    assert resp.get('result') == UnorderedList(
        [
            {
                'id': resume.id,
                'state': resume.state.value,
                'content': resume.content,
                'created_at': resume.created_at.isoformat(),
                'published_at': resume.published_at,
            }
            for resume in expected_resumes
        ],
    ), resp.get('error')


def test_filter_by_state(jsonrpc_request, auth_user):
    draft = factories.ResumeFactory.create(user=auth_user)
    published = factories.ResumeFactory.create(published=True, user=auth_user)
    hidden = factories.ResumeFactory.create(state=models.ResumeState.HIDDEN, user=auth_user)

    for resume in (draft, published, hidden):
        resp = jsonrpc_request(
            'get_resumes_for_applicant',
            {
                'filters': {
                    'states': [resume.state],
                },
            },
        )

        assert resp.get('result') == [
            IsPartialDict(
                {
                    'id': resume.id,
                    'state': resume.state.value,
                },
            ),
        ], resp.get('error')
