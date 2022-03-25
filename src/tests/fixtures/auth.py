import datetime as dt

import pytest
from hr import factories
from hr import security
from hr import models


@pytest.fixture()
def auth_user() -> models.User:
    raw_password = 'password'
    user = factories.UserFactory.create(raw_password=raw_password)
    return user


@pytest.fixture()
def auth_user_id(auth_user) -> int:
    return auth_user.id


@pytest.fixture()
def auth_user_token(settings, auth_user) -> str:
    settings.JWT_EXPIRATION_INTERVAL = dt.timedelta(days=90)
    return security.encode_jwt(auth_user.id)
