import datetime as dt

import pydantic
from django.contrib.postgres.search import SearchVector
from pydantic import BaseModel as PydanticBaseModel, constr
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
    patronymic: str | None = Field(None, title='Отчество')

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
    patronymic: str | None = Field(..., title='Отчество')

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


class LoginResponseSchema(BaseModel):
    token: str = Field(..., title='Токен', description='JWT-токен')
    user: UserSchema = Field(..., title='Информация о пользователе')


class ResumeForApplicantSchema(BaseModel):
    id: int = Field(..., title='ID')
    state: models.ResumeState = Field(..., title='Состояние')
    content: str = Field(..., title='Содержимое')
    created_at: dt.datetime = Field(..., title='Дата/Время создания')
    published_at: dt.datetime | None = Field(
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
    state__in: conlist(models.ResumeState, min_items=1) | None = Field(
        None,
        title='Фильтр по состоянию',
        description='Вернутся только резюме, состояния которых соответствуют заданным',
        alias='states',
    )
    id__in: conlist(int, min_items=1) | None = Field(
        None,
        title='Фильтр по Id',
        description='Возвращает резюме по переданному списку ID',
        alias='ids',
    )


class CreateVacancySchema(BaseModel):
    position: str = Field(..., title='Должность')
    experience: conint(ge=0) | None = Field(None, title='Стаж работы')
    description: str = Field(..., title='Описание')


class UpdateVacancySchema(BaseModel):
    position: str | None = Field(None, title='Должность')
    experience: conint(ge=0) | None = Field(None, title='Стаж работы')
    description: str | None = Field(..., title='Описание')


class ShortVacancyForManagerSchema(BaseModel):
    id: int = Field(..., title='ID вакансии')
    state: models.VacancyState = Field(..., title='Состояние')
    creator_id: int = Field(..., title='ID создателя')
    creator_full_name: str = Field(..., title='ФИО создателя')
    position: str = Field(..., title='Требуемая должность')
    experience: int | None = Field(..., title='Требуемый опыт работы')
    published_at: dt.datetime | None = Field(None, title='Дата/Время публикации')

    @classmethod
    def from_model(cls, vacancy: models.Vacancy):
        return cls(
            id=vacancy.id,
            state=vacancy.state,
            creator_id=vacancy.creator.id,
            creator_full_name=vacancy.creator.full_name,
            position=vacancy.position,
            experience=vacancy.experience,
            published_at=vacancy.published_at,
        )


class VacancyForManagerSchema(BaseModel):
    id: int = Field(..., title='ID вакансии')
    state: models.VacancyState = Field(..., title='Состояние')
    creator: UserSchema = Field(..., title='Создатель вакансии')
    position: str = Field(..., title='Должность соискателя')
    experience: conint(ge=0) | None = Field(None, title='Стаж работы соискателя')
    description: str = Field(..., title='Описание')
    published_at: dt.datetime | None = Field(None, title='Дата/Время публикации')

    @classmethod
    def from_model(cls, vacancy: models.Vacancy):
        return cls(
            id=vacancy.id,
            state=vacancy.state,
            creator=UserSchema.from_model(vacancy.creator),
            position=vacancy.position,
            experience=vacancy.experience,
            description=vacancy.description,
            published_at=vacancy.published_at,
        )


class VacancyFiltersForManager(BaseModel):
    state__in: conlist(models.VacancyState, min_items=1) | None = Field(
        None,
        title='Фильтрация по состоянию',
        description='Вернутся только те вакансии, состояние которых соответствует одному их переданных',
        alias='states',
    )
    position__icontains: constr(min_length=3) | None = Field(
        None,
        title='Поиск по должности',
        description='Вернутся только те вакансии, требуемая должность которых содержит переданную строку',
        alias='position',
    )
    # FIXME: experience может быть null
    experience__lte: conint(ge=1) | None = Field(
        None,
        title='Требуемый опыт меньше...',
        alias='experience_lte',
    )
    experience__gte: conint(ge=0) | None = Field(
        None,
        title='Требуемый опыт больше...',
        alias='experience_gte',
    )
    published_at__date__lte: dt.date | None = Field(
        None,
        title='Опубликовано после ...',
        description='Вернет только те вакансии, которые были опубликованы после переданной даты',
        example='2022-05-10',
        alias='published_lte',
    )
    published_at__date__gte: dt.date | None = Field(
        None,
        title='Опубликовано до ...',
        description='Вернет только те вакансии, которые были опубликованы до переданной даты',
        example='2022-05-10',
        alias='published_gte',
    )


class ShortVacancyForApplicantSchema(BaseModel):
    id: int = Field(..., title='ID вакансии')
    creator_id: int = Field(..., title='ID создателя')
    creator_full_name: str = Field(..., title='ФИО создателя')
    department_id: int = Field(..., title='ID департамента')
    department_name: str = Field(..., title='Название департамента')
    position: str = Field(..., title='Требуемая должность')
    experience: conint(ge=0) | None = Field(None, title='Требуемый стаж работы')
    published_at: dt.datetime | None = Field(None, title='Дата/Время публикации')

    @classmethod
    def from_model(cls, vacancy: models.Vacancy):
        return cls(
            id=vacancy.id,
            creator_id=vacancy.creator.id,
            creator_full_name=vacancy.creator.full_name,
            department_id=vacancy.creator.department.id,
            department_name=vacancy.creator.department.name,
            position=vacancy.position,
            experience=vacancy.experience,
            published_at=vacancy.published_at,
        )


class VacancyForApplicantSchema(BaseModel):
    id: int = Field(..., title='ID вакансии')
    creator_id: int = Field(..., title='ID менеджера, создавшего вакансию')
    creator_full_name: str = Field(..., title='ФИО менеджера, создавшего вакансию')
    creator_contact: str = Field(..., title='Контакт менеджера, разместившего вакансию')
    department_id: int = Field(..., title='ID департамента')
    department_name: str = Field(..., title='Название департамента')
    position: str = Field(..., title='Требуемая должность')
    experience: conint(ge=0) | None = Field(None, title='Требуемый стаж работы')
    description: str = Field(..., title='Описание вакансии')
    published_at: dt.datetime = Field(..., title='Дата публикации')

    @classmethod
    def from_model(cls, vacancy: models.Vacancy):
        return cls(
            id=vacancy.id,
            creator_id=vacancy.creator.id,
            creator_full_name=vacancy.creator.full_name,
            creator_contact=vacancy.creator.email,
            department_id=vacancy.creator.department.id,
            department_name=vacancy.creator.department.name,
            position=vacancy.position,
            experience=vacancy.experience,
            description=vacancy.description,
            published_at=vacancy.published_at,
        )


class VacancyFiltersForApplicant(BaseModel):
    creator__department_id__in: conlist(int, min_items=1) | None = Field(
        None,
        title='Фильтрация по департаменту',
        description='Вернет только те вакансии, департамент которых соответствует одному из переданных',
        alias='department_ids',
    )
    position__icontains: constr(min_length=3) | None = Field(
        None,
        title='Поиск по должности',
        description='Вернутся только те вакансии, требуемая должность которых содержит переданную строку',
        alias='position',
    )
    # FIXME: experience может быть null
    experience__lte: conint(ge=1) | None = Field(
        None,
        title='Требуемый опыт меньше...',
        alias='experience_lte',
    )
    experience__gte: conint(ge=0) | None = Field(
        None,
        title='Требуемый опыт больше...',
        alias='experience_gte',
    )
    published_at__date__lte: dt.date | None = Field(
        None,
        title='Опубликовано после ...',
        description='Вернет только те вакансии, которые были опубликованы после переданной даты',
        example='2022-05-10',
        alias='published_lte',
    )
    published_at__date__gte: dt.date | None = Field(
        None,
        title='Опубликовано до ...',
        description='Вернет только те вакансии, которые были опубликованы до переданной даты',
        example='2022-05-10',
        alias='published_gte',
    )


class ResumeForManagerSchema(BaseModel):
    id: int = Field(..., title='ID')
    content: str = Field(..., title='Содержимое')
    published_at: dt.datetime = Field(
        ...,
        title='Дата/Время публикации',
    )

    @classmethod
    def from_model(cls, resume: models.Resume):
        pass


class ShortApplicantSchema(BaseModel):
    id: int = Field(..., title='Идентификатор пользователя')
    email: EmailStr = Field(..., title='Email')
    full_name: str = Field(..., title='ФИО')
    department: DepartmentSchema = Field(..., title='Департамент')

    @classmethod
    def from_model(cls, user: models.User):

        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            department=DepartmentSchema.from_model(user.department),
        )


class ApplicantFilters(BaseModel):
    email__icontains: constr(min_length=1) | None = Field(
        None,
        title='Поиск по email',
        description='Вернет всех соискателей, email которых содержит переданную строчку',
        alias='email',
    )
    # TODO: повестить индекс!
    full_name_search: constr(min_length=1) | None = Field(
        None,
        title='Поиск по ФИО',
        description='Вернет всех соискателей, ФИО которых содержит переданную строку',
        alias='full_name',
    )
    department_id__in: conlist(int, min_items=1) | None = Field(
        None,
        title='Фильтрация по департаменту',
        description='Вернет всех соискателей, департамент которых соответствует одному их переданных',
        alias='department_ids',
    )

    def filter_query(self, query: models.QuerySet):
        return (
            query
            .annotate(
                full_name_search=SearchVector('first_name', 'last_name', 'patronymic'),
            )
            .filter(
                **self.dict(exclude_none=True),
            )
        )
