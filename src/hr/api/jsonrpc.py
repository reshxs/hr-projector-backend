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
from .dependencies import get_token

api_v1 = Entrypoint(
    '/api/v1/web/jsonrpc',
    name='web',
    summary='Web JSON_RPC entrypoint',
)


# TODO: вытащить handle_default_errors из NPD
# TODO: отдавать понятные ошибки валидации из pydantic
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
def add_resume(
    user: models.User = Depends(
        UserGetter(
            allowed_roles=[models.UserRole.EMPLOYEE],
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
            allowed_roles=[models.UserRole.EMPLOYEE],
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
            allowed_roles=[models.UserRole.EMPLOYEE],
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
            allowed_roles=[models.UserRole.EMPLOYEE],
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
            allowed_roles=[models.UserRole.EMPLOYEE],
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
def edit_resume(
    user: models.User = Depends(
        UserGetter(allowed_roles=[models.UserRole.EMPLOYEE,]),
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
