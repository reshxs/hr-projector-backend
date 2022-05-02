from fastapi import Body
from fastapi import Depends
from fastapi_jsonrpc import Entrypoint

from hr import models
from . import schemas
from . import errors
from .dependencies import UserGetter
from .dependencies import get_token

api_v1 = Entrypoint(
    '/api/v1/web/jsonrpc',
    name='web',
    summary='Web JSON_RPC entrypoint',
    dependencies=[
        Depends(get_token),
    ]
)


# TODO: вытащить handle_default_errors из NPD
# TODO: отдавать понятные ошибки валидации из pydantic


@api_v1.method(
    tags=["applicant"],
    summary="Добавить резюме",
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
