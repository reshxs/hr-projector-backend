import datetime as dt
import typing as tp

import pydantic
from pydantic import BaseModel as PydanticBaseModel
from pydantic import EmailStr
from pydantic import Field
from pydantic import conlist
from pydantic import conint

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
            raise ValueError('Password and password confirmation should be equal!')

        return values


class UserSchema(BaseModel):
    id: int = Field(..., title='Идентификатор пользователя')
    email: EmailStr = Field(..., title='Email')
    first_name: str = Field(..., title='Имя')
    last_name: str = Field(..., title='Фамилия')
    patronymic: tp.Optional[str] = Field(..., title='Отчество')

    department: DepartmentSchema = Field(..., title='Департамент')

    role: models.UserRole = Field(..., title='Является менеджером')

    @classmethod
    def from_model(cls, user: models.User):
        return cls(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            patronymic=user.patronymic,
            department=DepartmentSchema.from_model(user.department),
            role=user.role,
        )


class LoginSchema(BaseModel):
    email: EmailStr = Field(..., title='Email')
    password: str = Field(..., title='Пароль в сыром виде')


class UserTokenSchema(BaseModel):
    token: str = Field(..., title='Токен', description='JWT-токен')


class ResumeForApplicantSchema(BaseModel):
    id: int = Field(..., title='ID')
    state: models.ResumeState = Field(..., title='Состояние')
    content: str = Field(..., title='Содержимое')
    created_at: dt.datetime = Field(..., title='Дата/Время создания')
    published_at: tp.Optional[dt.datetime] = Field(
        None,
        title='Дата/Время публикации',
    )

    @classmethod
    def from_model(cls, resume: models.Resume):
        return cls(
            id=resume.id,
            state=resume.state,
            content=resume.content,
            created_at=resume.created_at,
            published_at=resume.published_at,
        )


class ResumeFiltersForApplicant(BaseModel):
    state__in: tp.Optional[conlist(models.ResumeState, min_items=1)] = Field(
        None,
        title='Фильтр по состоянию',
        description='Вернутся только резюме, состояния которых соответствуют заданным',
        alias='states',
    )
    id__in: tp.Optional[conlist(int, min_items=1)] = Field(
        None,
        title='Фильтр по Id',
        description='Возвращает резюме по переданному списку ID',
        alias='ids',
    )


class CreateVacancySchema(BaseModel):
    position: str = Field(..., title='Должность')
    experience: tp.Optional[conint(ge=0)] = Field(None, title='Стаж работы')
    description: str = Field(..., title='Описание')


class VacancyForManagerSchema(BaseModel):
    state: models.VacancyState = Field(..., title='Состояние')
    creator: UserSchema = Field(..., title='Создатель вакансии')
    position: str = Field(..., title='Должность соискателя')
    experience: tp.Optional[conint(ge=0)] = Field(None, title='Стаж работы соискателя')
    description: str = Field(..., title='Описание')
    published_at: tp.Optional[dt.datetime] = Field(None, title='Дата/Время публикации')

    @classmethod
    def from_model(cls, vacancy: models.Vacancy):
        return cls(
            state=vacancy.state,
            creator=UserSchema.from_model(vacancy.creator),
            position=vacancy.position,
            experience=vacancy.experience,
            description=vacancy.description,
            published_at=vacancy.published_at,
        )
