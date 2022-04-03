from pydantic import BaseModel
from pydantic import Field


class LoginSchema(BaseModel):
    email: str = Field(..., title='Email')  # FIXME: EmailStr
    password: str = Field(..., title='Пароль в сыром виде')


class UserTokenSchema(BaseModel):
    token: str = Field(..., title='Токен', description='JWT-токен')
