import pytest
from django.forms import model_to_dict

from hr.api import factories as api_factories
from hr import models
from hr import factories
from dirty_equals import IsInt


pytestmark = [
    pytest.mark.django_db(transaction=True)
]


def test_register__ok(auth_request, department):
    request = api_factories.StartRegistrationRequestFactory.create(
        department_id=department.id,
    )

    response = auth_request(
        'register',
        {
            'user_data': request,
        },
        use_auth=False,
    )

    assert response.get('result') == {
        'id': IsInt,
        'email': request.get('email'),
        'first_name': request.get('first_name'),
        'last_name': request.get('last_name'),
        'patronymic': request.get('patronymic'),
        'department': {
            'id': department.id,
            'name': department.name,
        },
        'role': 'APPLICANT',
    }

    user_id = response['result'].get('id')
    user: models.User = models.User.objects.get_or_none(id=user_id)
    assert user is not None

    assert user.email == request.get('email')
    assert user.first_name == request.get('first_name')
    assert user.last_name == request.get('last_name')
    assert user.patronymic == request.get('patronymic')
    assert user.check_password(request.get('password'))
    assert model_to_dict(user.department) == model_to_dict(department)
    assert user.role == models.UserRole.APPLICANT


def test_register__user_already_exists(auth_request, department):
    existing_user = factories.UserFactory.create()
    request = api_factories.StartRegistrationRequestFactory.create(
        email=existing_user.email,
        department_id=department.id,
    )

    response = auth_request(
        'register',
        {
            'user_data': request,
        },
        use_auth=False,
    )

    assert response.get('error') == {'code': 1001, 'message': 'User already exists'}


def test_register__passwords_does_not_match(auth_request, department):
    request = api_factories.StartRegistrationRequestFactory.create(
        password='password1',
        password_confirmation='password2',
        department_id=department.id,
    )

    response = auth_request(
        'register',
        {
            'user_data': request,
        },
        use_auth=False,
    )

    assert response.get('error') == {
        'code': -32602,
        'data': {
            'errors': [
                {
                    'loc': ['user_data', '__root__'],
                    'msg': 'Password and password confirmation should be equal!',
                    'type': 'value_error',
                },
            ],
        },
        'message': 'Invalid params',
    }


def test_register__department_not_found(auth_request):
    request = api_factories.StartRegistrationRequestFactory.create()

    response = auth_request(
        'register',
        {
            'user_data': request,
        },
        use_auth=False,
    )

    assert response.get('error') == {'code': 2001, 'message': 'Department not found'}
