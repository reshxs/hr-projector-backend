from fastapi_jsonrpc import BaseError


class Forbidden(BaseError):
    CODE = 403
    MESSAGE = 'forbidden'
