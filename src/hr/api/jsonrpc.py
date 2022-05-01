from django.contrib.auth.hashers import make_password
from fastapi import Body
from fastapi import Depends
from fastapi_jsonrpc import Entrypoint

from hr import models
from hr import security
from . import errors
from . import schemas
from .dependencies import UserGetter

api_v1 = Entrypoint(
    '/api/v1/web/jsonrpc',
    name='web',
    summary='Web JSON_RPC entrypoint',
)


# TODO: вытащить handle_default_errors из NPD
# TODO: отдавать понятные ошибки валидации из pydantic


@api_v1.method(
    tags=['test'],
    summary='Тестовый метод, возвращает содержимое сообщения',
)
def echo(message: str) -> str:
    return message


@api_v1.method(
    tags=['test'],
    summary='Тестовый метод, проверяем авторизацию',
)
def test_auth(
    user: models.User = Depends(UserGetter())
) -> str:
    return f'Hello, {user.full_name}'


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


@api_v1.method(
    tags=["applicant"],
    summary="Добавить резюме",
)
def add_resume(
    user: models.User = Depends(
        UserGetter(
            allowed_roles=[models.UserRole.EMPLOYEE],
        ),
    ),
    content: str = Body(..., title='Содержимое резюме'),
) -> schemas.ResumeForApplicantSchema:
    resume = models.Resume.objects.create(
        user=user,
        content=content,
    )

    return schemas.ResumeForApplicantSchema.from_model(resume)
