import typing as tp

import pydantic
from pydantic import BaseModel as PydanticBaseModel
from pydantic import EmailStr
from pydantic import Field

from hr import models


class BaseModel(PydanticBaseModel):
    class Config:
        allow_population_by_field_name = True


class DepartmentSchema(BaseModel):
    id: int = Field(..., title='ID департамента')
    name: str = Field(..., title='Название департамента')

    @classmethod
    def from_model(cls, department: models.Department):
        return cls(
            id=department.id,
            name=department.name,
        )


class RegistrationSchema(BaseModel):
    email: EmailStr = Field(..., title='Email')
    password: str = Field(..., title='Пароль')
    password_confirmation: str = Field(
        ...,
        title='Подтверждение пароля',
        description='Поля password и password_confirmation должны совпадать',
    )

    first_name: str = Field(..., title='Имя')
    last_name: str = Field(..., title='Фамилия')
    patronymic: tp.Optional[str] = Field(None, title='Отчество')

    department_id: int = Field(..., title='ID департамента')

    @pydantic.root_validator()
    def validate_passwords_are_equal(cls, values):
        password = values.get('password')
        password_confirmation = values.get('password_confirmation')

        if password != password_confirmation:
            # TODO: возможно это тот случай, когда надо завести отдельную ошибку
            raise ValueError('Password and password confirmation should be equal!')

        return values


class UserSchema(BaseModel):
    id: int = Field(..., title='Идентификатор пользователя')
    email: EmailStr = Field(..., title='Email')
    first_name: str = Field(..., title='Имя')
    last_name: str = Field(..., title='Фамилия')
    patronymic: tp.Optional[str] = Field(..., title='Отчество')

    department: DepartmentSchema = Field(..., title='Департамент')

    is_manager: bool = Field(..., title='Является менеджером')

    @classmethod
    def from_model(cls, user: models.User):
        return cls(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            patronymic=user.patronymic,
            department=DepartmentSchema.from_model(user.department),
            is_manager=user.is_manager,
        )


class LoginSchema(BaseModel):
    email: EmailStr = Field(..., title='Email')
    password: str = Field(..., title='Пароль в сыром виде')


class UserTokenSchema(BaseModel):
    token: str = Field(..., title='Токен', description='JWT-токен')
