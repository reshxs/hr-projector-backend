import typing as tp

import fastapi
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request

from hr import models
from hr import security
from . import errors


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

        user = models.User.objects.get_or_none(id=token.user_id)

        if user is None:
            raise errors.Forbidden

        return user
