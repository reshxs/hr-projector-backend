import datetime as dt

from django.conf import settings
from jose import jwt
from pydantic import BaseModel
from pydantic import Field


class UserToken(BaseModel):
    user_id: int
    expired_at: dt.datetime = Field(..., alias='exp')

    class Config:
        allow_population_by_field_name = True


class TokenExpiredError(Exception):
    ...


def encode_jwt(user_id: int) -> str:
    expired_at = dt.datetime.now() + settings.JWT_EXPIRATION_INTERVAL
    token = UserToken(user_id=user_id, expired_at=expired_at.isoformat())
    return jwt.encode(token.dict(by_alias=True), key=settings.SECRET_KEY)


def decode_jwt(token: str) -> UserToken:
    try:
        token_dict = jwt.decode(token, settings.SECRET_KEY)
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError

    return UserToken(**token_dict)
