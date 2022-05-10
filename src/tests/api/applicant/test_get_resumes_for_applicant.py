import pytest
from dirty_equals import IsPartialDict

from hr import factories
from hr import models
from dirty_equals import IsListOrTuple

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


def test_return_only_users_resumes(jsonrpc_request, user):
    resumes = factories.ResumeFactory.create_batch(3, user=user)
    factories.ResumeFactory.create_batch(3)  # other_user

    resp = jsonrpc_request(
        'get_resumes_for_applicant',
    )

    assert resp.get('result') == IsListOrTuple(
        *[
            {
                'id': resume.id,
                'state': resume.state.value,
                'content': resume.content,
                'created_at': resume.created_at.isoformat(),
                'published_at': resume.published_at,
            }
            for resume in resumes
        ],
        check_order=False,
    ), resp.get('error')


def test_filter_by_id(jsonrpc_request, user):
    expected_resumes = factories.ResumeFactory.create_batch(3, user=user)
    factories.ResumeFactory.create_batch(3, user=user)  # not expected resumes

    resp = jsonrpc_request(
        'get_resumes_for_applicant',
        {
            'filters': {
                'ids': [resume.id for resume in expected_resumes],
            },
        },
    )

    assert resp.get('result') == IsListOrTuple(
        *[
            {
                'id': resume.id,
                'state': resume.state.value,
                'content': resume.content,
                'created_at': resume.created_at.isoformat(),
                'published_at': resume.published_at,
            }
            for resume in expected_resumes
        ],
        check_order=False,
    ), resp.get('error')


def test_filter_by_state(jsonrpc_request, user):
    draft = factories.ResumeFactory.create(user=user)
    published = factories.ResumeFactory.create(published=True, user=user)
    hidden = factories.ResumeFactory.create(state=models.ResumeState.HIDDEN, user=user)

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
