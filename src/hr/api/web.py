from fastapi_jsonrpc import Entrypoint


api_v1 = Entrypoint(
    '/api/v1/web/jsonrpc',
    name='web',
    summary='Web JSON_RPC entrypoint',
)


@api_v1.method(
    tags=['test'],
    summary='Тестовый метод, возвращает содержимое сообщения',
)
def echo(message: str) -> str:
    return message
