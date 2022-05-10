import typing as tp

from django.db import transaction
from django.utils import timezone
from fastapi import Body
from fastapi import Depends
from fastapi_jsonrpc import Entrypoint

from hr import models
from . import errors
from . import schemas
from .dependencies import UserGetter

api_v1 = Entrypoint(
    '/api/v1/web/jsonrpc',
    name='web',
    summary='Web JSON_RPC entrypoint',
)


# TODO: вытащить handle_default_errors из NPD
# TODO: сделать общий механизм проверки сессии, явно указывать, если не требуется авторизация


@api_v1.method(
    tags=['departments']
)
def get_departments() -> list[schemas.DepartmentSchema]:
    # TODO: кэшировать!
    departments = models.Department.objects.order_by('name').all()
    return [schemas.DepartmentSchema.from_model(department) for department in departments]


@api_v1.method(
    tags=['applicant'],
    summary='Добавить резюме',
)
def create_resume(
    user: models.User = Depends(
        UserGetter(
            allowed_roles=[models.UserRole.APPLICANT],
        ),
    ),
    content: str = Body(..., title='Содержимое резюме'),
) -> schemas.ResumeForApplicantSchema:
    resume = models.Resume.objects.create(
        user=user,
        content=content,
    )

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
    filters: tp.Optional[schemas.ResumeFiltersForApplicant] = Body(None, title='Фильтры')
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
    new_content: str = Body(..., title='Данные для обновления'),
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

        resume.content = new_content
        resume.save(update_fields=('content',))

    return schemas.ResumeForApplicantSchema.from_model(resume)


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

        if vacancy is None:
            raise errors.VacancyNotFound

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

        if vacancy is None:
            raise errors.VacancyNotFound

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

        if vacancy is None:
            raise errors.VacancyNotFound

        if vacancy.state != models.VacancyState.PUBLISHED:
            raise errors.VacancyWrongState

        vacancy.state = models.VacancyState.HIDDEN
        vacancy.published_at = None
        vacancy.save(update_fields=('state', 'published_at'))

    return schemas.VacancyForManagerSchema.from_model(vacancy)


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
