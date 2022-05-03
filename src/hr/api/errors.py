from fastapi_jsonrpc import BaseError


class Forbidden(BaseError):
    CODE = 403
    MESSAGE = 'forbidden'


class UserAlreadyExists(BaseError):
    CODE = 1001
    MESSAGE = 'User already exists'


class DepartmentNotFound(BaseError):
    CODE = 2001
    MESSAGE = 'Department not found'


class ResumeNotFound(BaseError):
    CODE = 3001
    MESSAGE = 'Resume not found'


class ResumeWrongState(BaseError):
    CODE = 3002
    MESSAGE = 'Resume has not allowed state for this method'


class VacancyNotFound(BaseError):
    CODE = 4001
    MESSAGE = 'Vacancy not found'


class VacancyWrongState(BaseError):
    CODE = 4002
    MESSAGE = 'Vacancy has not allowed state for this method'
