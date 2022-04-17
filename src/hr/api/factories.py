import factory
from . import schemas


factory.Faker._DEFAULT_LOCALE = 'ru_RU'


class StartRegistrationRequestFactory(factory.Factory):
    class Meta:
        model = schemas.RegistrationSchema

    email = factory.Faker('email')
    first_name = factory.Faker('first_name_male')
    last_name = factory.Faker('last_name_male')
    patronymic = factory.Faker('middle_name_male')
    password = factory.Faker('word')
    password_confirmation = factory.LazyAttribute(lambda obj: obj.password)
    department_id = factory.Faker('random_int')
