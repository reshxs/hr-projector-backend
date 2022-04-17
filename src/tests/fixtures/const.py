import pytest
from hr import factories


@pytest.fixture
def department():
    return factories.DepartmentFactory.create()