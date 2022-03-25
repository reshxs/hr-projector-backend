import fastapi
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request

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


def get_user_id(
    token: security.UserToken = Depends(get_token)
) -> int:
    return token.user_id
