import pytest
import functools
from dirty_equals import IsPartialDict

from hr import factories
from hr import models

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.parametrize('user', [models.UserRole.MANAGER], indirect=True),
]


@pytest.fixture()
def published_resume():
    resume = factories.ResumeFactory.create(published=True)

    skills = factories.SkillFactory.create_batch(3)
    resume.skills.set(skills)
    resume.save()

    return resume


@pytest.fixture()
def draft_resume():
    return factories.ResumeFactory.create()


@pytest.fixture()
def hidden_resume():
    return factories.ResumeFactory.create(hidden=True)


@pytest.fixture()
def published_resume_factory():
    return functools.partial(factories.ResumeFactory.create, published=True)


def test_ok(
    user,
    published_resume,
    draft_resume,
    hidden_resume,
    jsonrpc_request,
):
    resume = published_resume

    resp = jsonrpc_request(
        'get_resumes_for_manager',
        {
            'pagination': {
                'count': True,
            },
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'items': [
            {
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
        ],
        'total_size': 1,
    }, resp.get('error')


@pytest.mark.parametrize(
    'search_param',
    [
        'expected@example.com',
        'expected',
        'example.com',
        'exp',
    ]
)
def test_filter_by_applicant_email(user, jsonrpc_request, published_resume_factory, search_param):
    expected_resume = published_resume_factory(user__email='expected@example.com')
    published_resume_factory(user__email='test@mail.ru')  # unexpected

    resp = jsonrpc_request(
        'get_resumes_for_manager',
        {
            'pagination': {
                'count': True,
            },
            'filters': {
                'email': search_param,
            }
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'total_size': 1,
        'items': [
            IsPartialDict(
                {
                    'id': expected_resume.id,
                    'applicant': IsPartialDict(
                        {
                            'email': expected_resume.user.email,
                        },
                    ),
                },
            ),
        ],
    }, resp.get('error')


@pytest.mark.parametrize(
    'search_param',
    [
        'Иванов Иван Иванович',
        'иван иванович иванов',
        'иван',
        'иван иванов'
    ]
)
def test_filter_by_applicant_full_name(user, jsonrpc_request, published_resume_factory, search_param):
    expected_resume = published_resume_factory(
        user__first_name='Иван',
        user__last_name='Иванов',
        user__patronymic='Иванович',
    )
    published_resume_factory(
        user__first_name='Петр',
        user__last_name='Петров',
        user__patronymic='Петрович',
    )  # unexpected

    resp = jsonrpc_request(
        'get_resumes_for_manager',
        {
            'pagination': {
                'count': True,
            },
            'filters': {
                'full_name': search_param,
            }
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'total_size': 1,
        'items': [
            IsPartialDict(
                {
                    'id': expected_resume.id,
                    'applicant': IsPartialDict(
                        {
                            'full_name': expected_resume.user.full_name,
                        },
                    ),
                },
            ),
        ],
    }, resp.get('error')


@pytest.mark.parametrize(
    'filter_key, filter_value',
    [
        ('department_ids', [31]),
        ('current_position', 'Разработчик'),
        ('current_position', 'разраб'),
        ('desired_position', 'Разработчик'),
        ('desired_position', 'разраб'),
        ('experience_gte', 9),
    ]
)
def test_other_filters(jsonrpc_request, published_resume_factory, filter_key, filter_value):
    expected_resume = published_resume_factory(
        user__department__id=31,
        current_position='Разработчик',
        desired_position='Разработчик',
        experience=10,
    )
    published_resume_factory(
        user__department__id=48,
        current_position='Тестировщик',
        desired_position='Тестировщик',
        experience=1,
    )  # unexpected

    resp = jsonrpc_request(
        'get_resumes_for_manager',
        {
            'pagination': {
                'count': True,
            },
            'filters': {
                filter_key: filter_value,
            }
        },
    )

    assert resp.get('result') == {
        'has_next': False,
        'total_size': 1,
        'items': [
            IsPartialDict({'id': expected_resume.id}),
        ],
    }, resp.get('error')
