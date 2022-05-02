from fastapi import Body
from fastapi import Depends
from fastapi_jsonrpc import Entrypoint

from hr import models
from . import schemas
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
