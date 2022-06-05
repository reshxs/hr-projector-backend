from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone
from fastapi import Body
from fastapi import Depends
from fastapi_jsonrpc import Entrypoint

from hr import models
from hr import security
from . import errors
from . import schemas
from .dependencies import UserGetter
from .dependencies import get_mutual_exclusive_pagination
from .pagination import AnyPagination
from .pagination import TypedPaginator, PaginatedResponse

api_v1 = Entrypoint(
    '/api/v1/web/jsonrpc',
    name='web',
    summary='Web JSON_RPC entrypoint',
)


# TODO: сделать общий механизм проверки сессии, явно указывать, если не требуется авторизация


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
) -> schemas.LoginResponseSchema:
    user = models.User.objects.get_or_none(email=credentials.email)

    if user is None:
        raise errors.Forbidden

    if not user.check_password(credentials.password):
        raise errors.Forbidden

    token = security.encode_jwt(user)

    return schemas.LoginResponseSchema(token=token, user=schemas.UserSchema.from_model(user))


@api_v1.method(
    tags=['auth'],
    summary='Получить информацию об авторизованном пользователе',
)
def get_current_user(
    user: models.User = Depends(
        UserGetter()
    ),
) -> schemas.UserSchema:
    return schemas.UserSchema.from_model(user)


@api_v1.method(
    tags=['departments']
)
def get_departments() -> list[schemas.DepartmentSchema]:
    # TODO: кэшировать!
    departments = models.Department.objects.order_by('name').all()
    return [schemas.DepartmentSchema.from_model(department) for department in departments]


# МЕТОДЫ ДЛЯ СОИСКАТЕЛЯ


@api_v1.method(
    tags=['applicant'],
    summary='Добавить резюме',
)
@transaction.atomic
def create_resume(
    user: models.User = Depends(
        UserGetter(
            allowed_roles=[models.UserRole.APPLICANT],
        ),
    ),
    content: schemas.CreateResumeSchema = Body(..., title='Содержимое резюме'),
) -> schemas.ResumeForApplicantSchema:
    resume = models.Resume.objects.create(
        user=user,
        current_position=content.current_position,
        desired_position=content.desired_position,
        experience=content.experience,
        bio=content.bio,
    )

    skills_to_create = [
        models.Skill(name=skill_name.lower())
        for skill_name in content.skills
    ]
    models.Skill.objects.bulk_create(skills_to_create, ignore_conflicts=True)

    skills = models.Skill.objects.filter(name__in=content.skills)
    assert len(skills) == len(content.skills)

    resume.skills.set(skills)
    resume.save()

    return schemas.ResumeForApplicantSchema.from_model(resume)


@api_v1.method(
    tags=['applicant'],
    summary='Получить резюме по ID',
    errors=[
        errors.ResumeNotFound,
    ]
)
def get_resume_for_applicant(
    user: models.User = Depends(
        UserGetter(
            allowed_roles=[models.UserRole.APPLICANT],
        ),
    ),
    resume_id: int = Body(..., title='ID резюме', alias='id')
) -> schemas.ResumeForApplicantSchema:
    resume = models.Resume.objects.get_or_none(
        user_id=user.id,
        id=resume_id,
    )

    if resume is None:
        raise errors.ResumeNotFound

    return schemas.ResumeForApplicantSchema.from_model(resume)


@api_v1.method(
    tags=['applicant'],
    summary='Получить список резюме',
)
def get_resumes_for_applicant(
    user: models.User = Depends(
        UserGetter(
            allowed_roles=[models.UserRole.APPLICANT],
        ),
    ),
    filters: schemas.ResumeFiltersForApplicant | None = Body(None, title='Фильтры')
) -> list[schemas.ResumeForApplicantSchema]:
    if filters is not None:
        filters = filters.dict(exclude_none=True)
    else:
        filters = {}

    resumes = models.Resume.objects.filter(
        user_id=user.id,
        **filters
    )

    return [schemas.ResumeForApplicantSchema.from_model(resume) for resume in resumes]


@api_v1.method(
    tags=['applicant'],
    summary='Опубликовать резюме',
    errors=[
        errors.ResumeNotFound,
    ]
)
def publish_resume(
    user: models.User = Depends(
        UserGetter(
            allowed_roles=[models.UserRole.APPLICANT],
        ),
    ),
    resume_id: int = Body(..., title='ID резюме', alias='id')
) -> schemas.ResumeForApplicantSchema:
    with transaction.atomic():
        resume = (
            models.Resume.objects
            .select_for_update(
                of=('self',)
            )
            .get_or_none(
                user_id=user.id,
                id=resume_id,
            )
        )

        if resume is None:
            raise errors.ResumeNotFound

        # FIXME: проверять состояние!

        resume.state = models.ResumeState.PUBLISHED
        resume.published_at = timezone.now()
        resume.save(update_fields=('state', 'published_at'))

    return schemas.ResumeForApplicantSchema.from_model(resume)


@api_v1.method(
    tags=['applicant'],
    summary='Скрыть резюме',
    errors=[
        errors.ResumeNotFound,
    ]
)
def hide_resume(
    user: models.User = Depends(
        UserGetter(
            allowed_roles=[models.UserRole.APPLICANT],
        ),
    ),
    resume_id: int = Body(..., title='ID резюме', alias='id')
) -> schemas.ResumeForApplicantSchema:
    with transaction.atomic():
        resume = (
            models.Resume.objects
            .select_for_update(
                of=('self',)
            )
            .get_or_none(
                user_id=user.id,
                id=resume_id,
            )
        )

        if resume is None:
            raise errors.ResumeNotFound

        if resume.state != models.ResumeState.PUBLISHED:
            raise errors.ResumeWrongState

        resume.state = models.ResumeState.HIDDEN
        resume.published_at = None
        resume.save(update_fields=('state', 'published_at'))

    return schemas.ResumeForApplicantSchema.from_model(resume)


@api_v1.method(
    tags=['applicant'],
    summary='Редактировать резюме',
    errors=[
        errors.ResumeNotFound,
        errors.ResumeWrongState,
    ],
)
def update_resume(
    user: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.APPLICANT, ]),
    ),
    resume_id: int = Body(..., title='ID резюме', alias='id'),
    content: schemas.UpdateResumeSchema = Body(..., title='Данные для обновления'),
) -> schemas.ResumeForApplicantSchema:
    with transaction.atomic():
        resume = (
            models.Resume.objects
            .select_for_update(
                of=('self',),
            )
            .get_or_none(
                id=resume_id,
                user_id=user.id,
            )
        )

        if resume is None:
            raise errors.ResumeNotFound

        if resume.state != models.ResumeState.DRAFT:
            raise errors.ResumeWrongState

        data_to_update = content.dict(exclude_none=True)

        if 'skills' in data_to_update:
            skill_names = data_to_update.pop('skills')
            skills = [
                models.Skill(name=skill_name)
                for skill_name in skill_names
            ]
            models.Skill.objects.bulk_create(skills, ignore_conflicts=True)
            skills = models.Skill.objects.filter(name__in=skill_names)
            resume.skills.set(skills)

        for key, value in data_to_update.items():
            setattr(resume, key, value)

        resume.save(
            update_fields=(
                'current_position',
                'desired_position',
                'experience',
                'bio',
            ),
        )

    return schemas.ResumeForApplicantSchema.from_model(resume)


@api_v1.method(
    tags=['applicant'],
    summary='Получить вакансию для соискателя',
    errors=[
        errors.VacancyNotFound,
    ],
)
def get_vacancy_for_applicant(
    _: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.APPLICANT]),
    ),
    vacancy_id: int = Body(..., title='ID вакансии', alias='id'),
) -> schemas.VacancyForApplicantSchema:
    vacancy = (
        models.Vacancy.objects
        .select_related('creator', 'creator__department')
        .get_or_none(
            id=vacancy_id,
            state=models.VacancyState.PUBLISHED,
        )
    )

    if vacancy is None:
        raise errors.VacancyNotFound

    return schemas.VacancyForApplicantSchema.from_model(vacancy)


@api_v1.method(
    tags=['applicant'],
    summary=['Получить список вакансий для соискателя'],
)
def get_vacancies_for_applicant(
    _: models.User = Depends(UserGetter()),
    any_pagination: AnyPagination = Depends(get_mutual_exclusive_pagination),
    filters: schemas.VacancyFiltersForApplicant | None = Body(
        None,
        title='Фильтры',
    )
) -> PaginatedResponse[schemas.ShortVacancyForApplicantSchema]:
    if filters is None:
        filters = {}
    else:
        filters = filters.dict(exclude_none=True)

    query = (
        models.Vacancy.objects
        .select_related('creator', 'creator__department')
        .filter(
            state__exact=models.VacancyState.PUBLISHED,
            **filters,
        )
        .order_by('-id')
    )

    paginator = TypedPaginator(schemas.ShortVacancyForApplicantSchema, query)
    return paginator.get_response(any_pagination)


@api_v1.method(
    tags=['applicant'],
    summary='Откликнуться на вакансию',
    errors=[
        errors.VacancyNotFound,
        errors.ResumeNotFound,
        errors.ResumeWrongState,
    ]
)
@transaction.atomic
def respond_vacancy(
    user: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.APPLICANT]),
    ),
    vacancy_id: int = Body(..., title='ID вакансии'),
    resume_id: int = Body(..., title='ID резюме'),
    message: str | None = Body(None, title='Сопроводительное письмо'),
) -> schemas.VacancyResponseSchema:
    vacancy = models.Vacancy.objects.get_or_none(
        id=vacancy_id,
        state=models.VacancyState.PUBLISHED,
    )
    if vacancy is None:
        raise errors.VacancyNotFound

    resume = models.Resume.objects.get_or_none(
        id=resume_id,
        user_id=user.id,
    )

    if resume is None:
        raise errors.ResumeNotFound

    if resume.state != models.ResumeState.PUBLISHED:
        raise errors.ResumeWrongState

    vacancy_response, created = models.VacancyResponse.objects.get_or_create(
        vacancy=vacancy,
        resume=resume,
        defaults={
            'applicant_message': message,
        },
    )

    if not created:
        raise errors.VacancyResponseAlreadyExists

    return schemas.VacancyResponseSchema.from_model(vacancy_response)


# МЕТОДЫ ДЛЯ МЕНЕДЖЕРА


@api_v1.method(
    tags=['manager'],
    summary='Создать вакансию',
)
def create_vacancy(
    user: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.MANAGER]),
    ),
    vacancy_data: schemas.CreateVacancySchema = Body(..., title='Данные для создания вакансии'),
) -> schemas.VacancyForManagerSchema:
    vacancy = models.Vacancy.objects.create(
        creator=user,
        position=vacancy_data.position,
        experience=vacancy_data.experience,
        description=vacancy_data.description,
    )

    return schemas.VacancyForManagerSchema.from_model(vacancy)


@api_v1.method(
    tags=['manager'],
    summary='Получить вакансию по ID',
    errors=[
        errors.VacancyNotFound,
    ],
)
def get_vacancy_for_manager(
    user: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.MANAGER]),
    ),
    vacancy_id: int = Body(..., title='ID вакансии', alias='id'),
) -> schemas.VacancyForManagerSchema:
    vacancy = models.Vacancy.objects.get_or_none(
        id=vacancy_id,
        creator__department_id=user.department_id,
    )

    if vacancy is None:
        raise errors.VacancyNotFound

    return schemas.VacancyForManagerSchema.from_model(vacancy)


@api_v1.method(
    tags=['manager'],
    summary='Получить список вакансий для менеджера',
)
def get_vacancies_for_manager(
    user: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.MANAGER]),
    ),
    any_pagination: AnyPagination = Depends(get_mutual_exclusive_pagination),
    filters: schemas.VacancyFiltersForManager | None = Body(
        None,
        title='Фильтры',
    ),
) -> PaginatedResponse[schemas.ShortVacancyForManagerSchema]:
    if filters is None:
        filters = {}
    else:
        filters = filters.dict(exclude_none=True)

    query = (
        models.Vacancy.objects
        .filter(
            creator__department_id=user.department_id,
            **filters,
        )
        .select_related(
            'creator', 'creator__department',
        )
        .order_by('-id')
    )

    paginator = TypedPaginator(schemas.ShortVacancyForManagerSchema, query)
    return paginator.get_response(any_pagination)


def _get_vacancy_for_update(vacancy_id: int, user_id: int):
    # TODO: вынести из API
    vacancy = (
        models.Vacancy.objects
        .select_for_update(of=('self',))
        .get_or_none(
            id=vacancy_id,
            creator_id=user_id,
        )
    )

    if vacancy is None:
        raise errors.VacancyNotFound

    return vacancy


@api_v1.method(
    tags=['manager'],
    summary='Редактировать вакансию',
    errors=[
        errors.VacancyNotFound,
        errors.VacancyWrongState,
    ],
)
def update_vacancy(
    user: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.MANAGER]),
    ),
    vacancy_id: int = Body(..., title='ID вакансии', alias='id'),
    new_data: schemas.UpdateVacancySchema = Body(..., title='Новые данные вакансии')
) -> schemas.VacancyForManagerSchema:
    with transaction.atomic():
        vacancy = _get_vacancy_for_update(vacancy_id, user.id)

        if vacancy.state != models.VacancyState.DRAFT:
            raise errors.VacancyWrongState

        for key, value in new_data.dict(exclude_none=True).items():
            setattr(vacancy, key, value)

        vacancy.save(update_fields=('position', 'experience', 'description'))

    return schemas.VacancyForManagerSchema.from_model(vacancy)


@api_v1.method(
    tags=['manager'],
    summary='Опубликовать вакансию',
    errors=[
        errors.VacancyNotFound,
        errors.VacancyWrongState,
    ],
)
def publish_vacancy(
    user: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.MANAGER]),
    ),
    vacancy_id: int = Body(..., title='ID вакансии', alias='id'),
) -> schemas.VacancyForManagerSchema:
    with transaction.atomic():
        vacancy = _get_vacancy_for_update(vacancy_id, user.id)

        if vacancy.state != models.VacancyState.DRAFT:
            raise errors.VacancyWrongState

        vacancy.state = models.VacancyState.PUBLISHED
        vacancy.published_at = timezone.now()
        vacancy.save(update_fields=('state', 'published_at'))

    return schemas.VacancyForManagerSchema.from_model(vacancy)


@api_v1.method(
    tags=['manager'],
    summary='Скрыть вакансию',
    errors=[
        errors.VacancyNotFound,
        errors.VacancyWrongState,
    ],
)
def hide_vacancy(
    user: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.MANAGER]),
    ),
    vacancy_id: int = Body(..., title='ID вакансии', alias='id'),
) -> schemas.VacancyForManagerSchema:
    with transaction.atomic():
        vacancy = _get_vacancy_for_update(vacancy_id, user.id)

        if vacancy.state != models.VacancyState.PUBLISHED:
            raise errors.VacancyWrongState

        vacancy.state = models.VacancyState.HIDDEN
        vacancy.published_at = None
        vacancy.save(update_fields=('state', 'published_at'))

    return schemas.VacancyForManagerSchema.from_model(vacancy)


@api_v1.method(
    tags=['manager'],
    summary=['Получить список соискателей'],
)
def get_applicants_for_manager(
    _: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.MANAGER]),
    ),
    any_pagination: AnyPagination = Depends(get_mutual_exclusive_pagination),
    filterer: schemas.ApplicantFilters | None = Body(None, title='Фильтрация', alias='filters'),
) -> PaginatedResponse[schemas.ShortApplicantSchema]:
    query = (
        models.User.objects
        .filter(
            role=models.UserRole.APPLICANT,
        )
        .order_by('-id')
    )

    if filterer is not None:
        query = filterer.filter_query(query)

    paginator = TypedPaginator(schemas.ShortApplicantSchema, query)
    return paginator.get_response(any_pagination)


@api_v1.method(
    tags=['manager'],
    summary='Получить список резюме для менеджера',
)
def get_resumes_for_manager(
    _: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.MANAGER]),
    ),
    any_pagination: AnyPagination = Depends(get_mutual_exclusive_pagination),
    filterer: schemas.ResumeFiltersForManager | None = Body(None, title='Фильтры', alias='filters'),
) -> PaginatedResponse[schemas.ResumeForManagerSchema]:
    query = models.Resume.objects.filter(
        state__exact=models.ResumeState.PUBLISHED,
    ).select_related(
        'user',
    ).order_by('-published_at')

    if filterer is not None:
        query = filterer.filter_query(query)

    paginator = TypedPaginator(schemas.ResumeForManagerSchema, query)
    return paginator.get_response(any_pagination)


@api_v1.method(
    tags=['manager'],
    summary='Получить список откликов на вакансию для менеджера',
)
def get_vacancy_responses_for_manager(
    user: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.MANAGER]),
    ),
    any_pagination: AnyPagination = Depends(get_mutual_exclusive_pagination),
) -> PaginatedResponse[schemas.VacancyResponseSchema]:
    query = models.VacancyResponse.objects.filter(
        vacancy__creator__department_id=user.department_id,
    ).select_related(
        'vacancy', 'vacancy__creator', 'resume', 'resume__user',
    )

    paginator = TypedPaginator(schemas.VacancyResponseSchema, query)
    return paginator.get_response(any_pagination)
