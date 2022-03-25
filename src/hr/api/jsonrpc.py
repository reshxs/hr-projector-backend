from fastapi import Body
from fastapi import Depends
from fastapi_jsonrpc import Entrypoint

from hr import models
from hr import security

from . import schemes
from . import errors
from .dependencies import get_token

api_v1 = Entrypoint(
    '/api/v1/web/jsonrpc',
    name='web',
    summary='Web JSON_RPC entrypoint',
)


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
    token: security.UserToken = Depends(get_token)
) -> str:
    user = models.User.objects.get_or_none(id=token.user_id)
    return f'Hello, {user.full_name}'


@api_v1.method(
    tags=['auth'],
    summary='Авторизоваться в системе',
    description='В ответ возвращается токен, который необходимо передавать в заголовках в качестве bearer',
    errors=[
        errors.Forbidden
    ]
)
def login(
    credentials: schemes.LoginSchema = Body(...,),
) -> schemes.UserTokenSchema:
    user = models.User.objects.get_or_none(email=credentials.email)

    if user is None:
        raise errors.Forbidden

    if not user.check_password(credentials.password):
        raise errors.Forbidden

    token = security.encode_jwt(user_id=user.id)

    return schemes.UserTokenSchema(token=token)
