from django.contrib.auth.hashers import make_password
from fastapi import Body
from fastapi_jsonrpc import Entrypoint

from hr import models
from hr import security
from . import errors
from . import schemas

api_v1 = Entrypoint(
    '/api/v1/auth/jsonrpc',
    name='auth',
    summary='Методы системы авторизации',
)


@api_v1.method(
    tags=['auth'],
    summary='Регистрация пользователя',
    errors=[
        errors.UserAlreadyExists,
        errors.DepartmentNotFound,
    ],
)
def register(
    user_data: schemas.RegistrationSchema = Body(..., title='Данные для создания пользователя'),
) -> schemas.UserSchema:
    department = models.Department.objects.get_or_none(id=user_data.department_id)
    if department is None:
        raise errors.DepartmentNotFound

    user, created = models.User.objects.get_or_create(
        email=user_data.email,
        defaults={
            'password': make_password(user_data.password),
            'first_name': user_data.first_name,
            'last_name': user_data.last_name,
            'patronymic': user_data.patronymic,
            'department_id': user_data.department_id,
        }
    )

    if not created:
        raise errors.UserAlreadyExists

    return schemas.UserSchema.from_model(user)


@api_v1.method(
    tags=['auth'],
    summary='Авторизоваться в системе',
    description='В ответ возвращается токен, который необходимо передавать в заголовках в качестве bearer',
    errors=[
        errors.Forbidden
    ]
)
def login(
    credentials: schemas.LoginSchema = Body(..., ),
) -> schemas.UserTokenSchema:
    user = models.User.objects.get_or_none(email=credentials.email)

    if user is None:
        raise errors.Forbidden

    if not user.check_password(credentials.password):
        raise errors.Forbidden

    token = security.encode_jwt(user)

    return schemas.UserTokenSchema(token=token)
