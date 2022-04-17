import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.hashers import make_password
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

    class Params:
        raw_password = 'password'
