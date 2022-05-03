import datetime as dt

import pytest

from hr import factories
from hr import models
from hr import security


@pytest.fixture
def department():
    return factories.DepartmentFactory.create()


@pytest.fixture(params=[models.UserRole.APPLICANT])
def user(request) -> models.User:
    role = request.param

    if not isinstance(role, models.UserRole):
        raise RuntimeError(f'Request param should be a UserRole, not {type(role)}')

    raw_password = 'password'
    user = factories.UserFactory.create(raw_password=raw_password, role=role)
    return user


@pytest.fixture()
def user_token(settings, user) -> str:
    settings.JWT_EXPIRATION_INTERVAL = dt.timedelta(days=90)
    return security.encode_jwt(user)
