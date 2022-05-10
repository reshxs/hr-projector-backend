import typing as tp

import fastapi
import fastapi_jsonrpc
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request

from hr import models
from hr import security
from . import errors
from .pagination import PaginationParams, AnyPagination
from .pagination import PaginationInfinityScrollParams


class JsonRpcBearerAuth(OAuth2PasswordBearer):
    async def __call__(self, request: Request):
        try:
            return await super().__call__(request)
        except fastapi.exceptions.HTTPException:
            raise errors.Forbidden


jsonrpc_bearer_auth = JsonRpcBearerAuth(tokenUrl='/')


def get_token(
    raw_token: str = Depends(jsonrpc_bearer_auth)
) -> security.UserToken:
    try:
        token = security.decode_jwt(raw_token)
    except security.TokenExpiredError:
        raise errors.Forbidden

    return token


class UserGetter:
    def __init__(self, allowed_roles: tp.List[models.UserRole] = None):
        self.allowed_roles = allowed_roles

    def __call__(self, token: security.UserToken = Depends(get_token)):
        if self.allowed_roles is not None and token.user_role not in self.allowed_roles:
            raise errors.Forbidden

        # TODO: возвращать данные сессии, а не пользователя из БД
        user = models.User.objects.get_or_none(id=token.user_id)

        if user is None:
            raise errors.Forbidden

        return user


def get_mutual_exclusive_pagination(
    pagination: tp.Optional[PaginationParams] = fastapi_jsonrpc.Body(None, title='Постраничная пагинация'),
    pagination_scroll: tp.Optional[PaginationInfinityScrollParams] = fastapi_jsonrpc.Body(
        None, title='Бесконечный скроллинг',
    ),
) -> AnyPagination:
    if pagination is not None and pagination_scroll is not None:
        raise fastapi_jsonrpc.InvalidParams

    return pagination or pagination_scroll or PaginationParams()
