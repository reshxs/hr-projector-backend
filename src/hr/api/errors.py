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
