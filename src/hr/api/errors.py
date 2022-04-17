from fastapi_jsonrpc import BaseError


class Forbidden(BaseError):
    CODE = 403
    MESSAGE = 'forbidden'


class UserAlreadyExists(BaseError):
    CODE = 1001
    MESSAGE = 'User already exists'


class PasswordsDoesNotMatch(BaseError):
    CODE = 1002
    MESSAGE = 'Passwords does not match'


class DepartmentNotFound(BaseError):
    CODE = 2001
    MESSAGE = 'Department not found'
