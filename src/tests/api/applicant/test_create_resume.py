import pytest
from hr import models
from django.utils import timezone

pytestmark = [
    pytest.mark.django_db(transaction=True)
]


@pytest.fixture()
def existing_skill():
    return models.Skill.objects.create(name='python')


def assert_skills_in_database(skills):
    existing_skills = models.Skill.objects.all()
    skill_names = {skill.name for skill in existing_skills}

    assert skill_names == set(skills)


def test_ok(user, jsonrpc_request, freezer, existing_skill):
    assert models.Resume.objects.count() == 0
    assert_skills_in_database(['python'])

    resp = jsonrpc_request(
        'create_resume',
        {
            'content': {
                'current_position': 'Разработчик',
                'desired_position': 'Тим лид',
                'skills': [
                    'python',
                    'docker',
                    'kubernetes',
                ],
                'experience': 7,
                'bio': 'Python разработчик с семилетнем стажем',
            },
        },
    )

    resume = models.Resume.objects.get()

    assert resp.get('result') == {
        'id': resume.id,
        'state': 'DRAFT',
        'current_position': 'Разработчик',
        'desired_position': 'Тим лид',
        'skills': [
            'python',
            'docker',
            'kubernetes',
        ],
        'experience': 7,
        'bio': 'Python разработчик с семилетнем стажем',
        'created_at': timezone.now().isoformat(),
        'published_at': None,
    }, resp.get('error')

    assert resume.user == user
    assert resume.state == models.ResumeState.DRAFT
    assert resume.current_position == 'Разработчик'
    assert resume.desired_position == 'Тим лид'
    assert resume.experience == 7
    assert resume.bio == 'Python разработчик с семилетнем стажем'
    assert resume.created_at == timezone.now().astimezone()
    assert resume.published_at is None

    assert ['python', 'docker', 'kubernetes'] == [
        skill.name for skill in resume.skills.all()
    ]

    assert_skills_in_database(['python', 'docker', 'kubernetes'])
