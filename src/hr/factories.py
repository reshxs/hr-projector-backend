import factory
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from factory.django import DjangoModelFactory

from . import models

factory.Faker._DEFAULT_LOCALE = 'ru_RU'


class DepartmentFactory(DjangoModelFactory):
    class Meta:
        model = models.Department

    name = factory.Faker('word')


class UserFactory(DjangoModelFactory):
    class Meta:
        model = models.User

    email = factory.Faker('email')
    first_name = factory.Faker('first_name_male')
    last_name = factory.Faker('last_name_male')
    patronymic = factory.Faker('middle_name_male')
    password = factory.LazyAttribute(lambda s: make_password(s.raw_password))
    department = factory.SubFactory(DepartmentFactory)

    role = models.UserRole.APPLICANT

    class Params:
        raw_password = 'password'


class SkillFactory(DjangoModelFactory):
    class Meta:
        model = models.Skill

    name = factory.Faker('word')


class ResumeFactory(DjangoModelFactory):
    class Meta:
        model = models.Resume

    user = factory.SubFactory(UserFactory)
    state = models.ResumeState.DRAFT
    current_position = factory.Faker('word')
    desired_position = factory.Faker('word')
    experience = None
    bio = factory.Faker('sentence')
    published_at = None

    class Params:
        published = factory.Trait(
            state=models.ResumeState.PUBLISHED,
            published_at=factory.LazyFunction(timezone.now),
        )
        hidden = factory.Trait(
            state=models.ResumeState.HIDDEN,
            published_at=None,
        )


class VacancyFactory(DjangoModelFactory):
    class Meta:
        model = models.Vacancy

    creator = factory.SubFactory(UserFactory, role=models.UserRole.MANAGER)

    state = models.VacancyState.DRAFT

    position = factory.Faker('word')
    experience = None
    description = factory.Faker('sentence')

    created_at = factory.LazyFunction(timezone.now)
    published_at = None

    class Params:
        published = factory.Trait(
            state=models.VacancyState.PUBLISHED,
            published_at=factory.LazyFunction(timezone.now),
        )
        hidden = factory.Trait(
            state=models.VacancyState.HIDDEN,
            published_at=None,
        )


class VacancyResponseFactory(DjangoModelFactory):
    class Meta:
        model = models.VacancyResponse

    vacancy = factory.SubFactory(VacancyFactory, published=True)
    resume = factory.SubFactory(ResumeFactory, published=True)
    applicant_message = factory.Faker('sentence')

